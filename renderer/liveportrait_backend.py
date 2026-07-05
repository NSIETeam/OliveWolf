"""
LivePortrait 实时渲染后端 (2D 头肩, 音频驱动口型)

改造自 LivePortrait 的 LivePortraitPipeline, 核心变化:
  - 不依赖驱动视频, 口型由 audio2lip 产出的 lip_close_ratio 序列驱动
  - 形象(源图)只预处理一次并缓存(x_s, f_s, source_lmk 等), 复用于多次说话
  - 头部姿态用小幅自然摆动(待机 motion), 而非驱动视频姿态

对接的 LivePortrait 真实接口:
  - LivePortraitWrapper.prepare_source / get_kp_info / extract_feature_3d / transform_keypoint
  - Cropper.crop_source_image  -> source_lmk, img_crop_256x256
  - retarget_lip(x_s, combined_lip_ratio_tensor) -> lip_delta
  - warp_decode(f_s, x_s, x_d_i_new) -> 渲染帧
  - paste_back(I_p_i, M_c2o, source_rgb, mask_ori_float) -> 贴回原图
"""
import sys
import os
from pathlib import Path

import numpy as np
import cv2

from config import get_config, project_root
from renderer.base import BaseRenderer
from renderer.audio2lip import Audio2Lip


class LivePortraitBackend(BaseRenderer):
    def __init__(self):
        cfg = get_config()
        lp_cfg = cfg["liveportrait"]
        self.lp_root = (project_root() / lp_cfg["project_root"]).resolve()
        # 把 LivePortrait 加入 sys.path, 复用其模块
        if str(self.lp_root) not in sys.path:
            sys.path.insert(0, str(self.lp_root))

        self.output_fps = lp_cfg["output_fps"]
        self.audio2lip = Audio2Lip()

        # 延迟导入, 避免 Mac 无 CUDA 时 import 报错
        from src.config.inference_config import InferenceConfig
        from src.config.crop_config import CropConfig
        from src.live_portrait_pipeline import LivePortraitPipeline
        from src.config.argument_config import ArgumentConfig

        self._InferenceConfig = InferenceConfig
        self._CropConfig = CropConfig
        self._Pipeline = LivePortraitPipeline

        # 初始化 pipeline 与形象缓存
        self._init_pipeline(lp_cfg)
        self._avatar_cache = {}  # source_path -> avatar state

    def _init_pipeline(self, lp_cfg):
        import tyro
        from src.config.argument_config import ArgumentConfig

        # 用默认参数构造, 仅取需要的字段
        args = ArgumentConfig()
        inf_fields = {k: v for k, v in args.__dict__.items()
                      if hasattr(self._InferenceConfig, k)}
        crop_fields = {k: v for k, v in args.__dict__.items()
                       if hasattr(self._CropConfig, k)}
        # 应用配置覆盖
        inf_fields["flag_use_half_precision"] = lp_cfg["flag_use_half_precision"]
        inf_fields["flag_stitching"] = lp_cfg["flag_stitching"]
        inf_fields["flag_do_crop"] = lp_cfg["flag_do_crop"]
        inf_fields["flag_pasteback"] = lp_cfg["flag_pasteback"]
        inf_fields["source_max_dim"] = lp_cfg["source_max_dim"]
        inf_fields["flag_lip_retargeting"] = True   # ★ 启用口型重定向
        inf_fields["flag_eye_retargeting"] = False
        inf_fields["flag_relative_motion"] = True

        inference_cfg = self._InferenceConfig(**inf_fields)
        crop_cfg = self._CropConfig(**crop_fields)
        self.pipeline = self._Pipeline(inference_cfg=inference_cfg, crop_cfg=crop_cfg)
        self.wrapper = self.pipeline.live_portrait_wrapper
        self.cropper = self.pipeline.cropper
        self.inf_cfg = inference_cfg
        self.crop_cfg = crop_cfg

    def init_avatar(self, source_image_path: str):
        """预处理源图, 缓存形象状态。"""
        if source_image_path in self._avatar_cache:
            return self._avatar_cache[source_image_path]

        from src.utils.io import load_image_rgb, resize_to_limit
        from src.utils.camera import get_rotation_matrix
        from src.utils.crop import prepare_paste_back

        img_rgb = load_image_rgb(source_image_path)
        img_rgb = resize_to_limit(img_rgb, self.inf_cfg.source_max_dim,
                                  self.inf_cfg.source_division)
        crop_info = self.cropper.crop_source_image(img_rgb, self.crop_cfg)
        if crop_info is None:
            raise Exception(f"源图未检测到人脸: {source_image_path}")
        source_lmk = crop_info["lmk_crop"]
        img_crop_256 = crop_info["img_crop_256x256"]

        I_s = self.wrapper.prepare_source(img_crop_256)
        x_s_info = self.wrapper.get_kp_info(I_s)
        R_s = get_rotation_matrix(x_s_info["pitch"], x_s_info["yaw"], x_s_info["roll"])
        f_s = self.wrapper.extract_feature_3d(I_s)
        x_s = self.wrapper.transform_keypoint(x_s_info)

        mask_ori_float = None
        if self.inf_cfg.flag_pasteback and self.inf_cfg.flag_do_crop and self.inf_cfg.flag_stitching:
            mask_ori_float = prepare_paste_back(
                self.inf_cfg.mask_crop, crop_info["M_c2o"],
                dsize=(img_rgb.shape[1], img_rgb.shape[0]),
            )

        state = {
            "img_rgb": img_rgb,
            "source_lmk": source_lmk,
            "I_s": I_s,
            "x_s_info": x_s_info,
            "R_s": R_s,
            "f_s": f_s,
            "x_s": x_s,
            "M_c2o": crop_info["M_c2o"],
            "mask_ori_float": mask_ori_float,
        }
        self._avatar_cache[source_image_path] = state
        return state

    def render_speaking(self, audio: np.ndarray, sample_rate: int,
                        source_image_path: str = None) -> tuple:
        """
        音频驱动口型渲染。
        Returns: (frames: list[np.ndarray HxWx3 uint8], fps: int)
        """
        from src.utils.crop import paste_back

        cfg = get_config()
        src_path = source_image_path or cfg["assets"]["liveportrait_source"]
        st = self.init_avatar(src_path)

        x_s = st["x_s"]
        f_s = st["f_s"]
        source_lmk = st["source_lmk"]
        x_s_info = st["x_s_info"]

        # 1. 音频 -> lip_close_ratio 序列
        ratios = self.audio2lip.audio_to_lip_ratios(audio, sample_rate)
        c_d_lip_lst = self.audio2lip.ratios_to_lip_inputs(ratios)

        n_frames = len(c_d_lip_lst)
        frames = []
        for i in range(n_frames):
            # 2. 计算口型 delta
            c_d_lip_i = c_d_lip_lst[i]
            combined_lip_ratio_tensor = self.wrapper.calc_combined_lip_ratio(
                c_d_lip_i, source_lmk
            )
            lip_delta = self.wrapper.retarget_lip(x_s, combined_lip_ratio_tensor)

            # 3. 组装驱动关键点: 基准 x_s + 自然摆动 + 口型 delta
            x_d_i_new = self._apply_idle_motion(x_s_info, i, x_s)
            x_d_i_new = x_d_i_new + lip_delta

            if self.inf_cfg.flag_stitching:
                x_d_i_new = self.wrapper.stitching(x_s, x_d_i_new)

            x_d_i_new = x_s + (x_d_i_new - x_s) * self.inf_cfg.driving_multiplier

            # 4. 渲染 + 贴回原图
            out = self.wrapper.warp_decode(f_s, x_s, x_d_i_new)
            I_p_i = self.wrapper.parse_output(out["out"])[0]
            if st["mask_ori_float"] is not None:
                I_p_i = paste_back(I_p_i, st["M_c2o"], st["img_rgb"],
                                   st["mask_ori_float"])
            frames.append(I_p_i)
        return frames, self.output_fps

    def _apply_idle_motion(self, x_s_info: dict, frame_idx: int, x_s) -> "torch.Tensor":
        """生成小幅自然头部摆动(替代驱动视频姿态)。保持基准姿态+轻微正弦摆动。"""
        import torch
        from src.utils.camera import get_rotation_matrix
        # 轻微 yaw 摆动, 振幅约 ±3 度
        yaw_offset = 3.0 * np.sin(frame_idx * 0.15)
        pitch = x_s_info["pitch"]
        yaw = x_s_info["yaw"] + yaw_offset
        roll = x_s_info["roll"]
        R_new = get_rotation_matrix(
            torch.tensor([pitch]), torch.tensor([yaw]), torch.tensor([roll])
        )
        # 用新旋转重算关键点 (保持表情/位移不变)
        kp = x_s_info["kp"]
        exp = x_s_info["exp"]
        scale = x_s_info["scale"]
        t = x_s_info["t"]
        kp_new = kp.view(1, -1, 3) @ R_new + exp.view(1, -1, 3)
        kp_new *= scale[..., None]
        kp_new[:, :, 0:2] += t[:, None, 0:2]
        return kp_new

    def render_idle(self, duration: float = 3.0, source_image_path: str = None) -> list:
        """渲染待机画面: 闭嘴 + 小幅摆动。"""
        import torch
        cfg = get_config()
        src_path = source_image_path or cfg["assets"]["liveportrait_source"]
        st = self.init_avatar(src_path)
        n_frames = int(duration * self.output_fps)
        # 闭嘴: lip_ratio=0
        zero_audio = np.zeros(int(duration * 16000), dtype=np.float32)
        return self.render_speaking(zero_audio, 16000, src_path)[0][:n_frames]
