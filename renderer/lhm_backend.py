"""
LHM 离线渲染后端 (全身 3D 数字人)

仅支持 NVIDIA CUDA。用于场景①④等需要全身3D的离线出片场景。
改造点: 形象(infer_single_view 产出的 3DGS)构建一次后缓存,
       不同话术/房源只换 SMPL-X 动作参数复用渲染, 避免重复重建。

依赖 LHM 原始项目的 app.py 核心函数, 此处做轻量封装。
注意: LHM 需要 16-24GB 显存与完整先验模型, 部署需在 CUDA 服务器。
"""
import sys
import os
from pathlib import Path

import numpy as np

from config import get_config, project_root
from renderer.base import BaseRenderer


class LHMBackend(BaseRenderer):
    def __init__(self):
        cfg = get_config()
        lhm_cfg = cfg["lhm"]
        self.lhm_root = (project_root() / lhm_cfg["project_root"]).resolve()
        if str(self.lhm_root) not in sys.path:
            sys.path.insert(0, str(self.lhm_root))
        os.chdir(str(self.lhm_root))  # LHM 用相对路径加载权重

        self.model_name = lhm_cfg["model_name"]
        self.render_fps = lhm_cfg["render_fps"]
        self._avatar_cache = {}
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化(避免 import 即加载大模型)。"""
        if self._initialized:
            return
        os.environ["APP_MODEL_NAME"] = self.model_name
        from app import parse_configs, _build_model, PoseEstimator, VGGHeadDetector
        from LHM.utils.preprocess import Preprocessor

        self.cfg, self.cfg_train = parse_configs()
        self.lhm = _build_model(self.cfg)
        self.pose_estimator = PoseEstimator()
        self.face_detector = VGGHeadDetector()
        self.preprocessor = Preprocessor()
        self._initialized = True

    def init_avatar(self, source_image_path: str):
        """构建全身 3DGS 形象并缓存。耗时约 2-6s。"""
        self._lazy_init()
        if source_image_path in self._avatar_cache:
            return self._avatar_cache[source_image_path]

        import torch, cv2
        import numpy as np
        from PIL import Image
        from app import infer_preprocess_image
        from LHM.runners.infer.utils import prepare_motion_seqs

        # 复用 app.py 的预处理逻辑构建形象
        image_out = self.preprocessor.preprocess(
            image_path=source_image_path, save_path=source_image_path + ".rembg.png",
            rmbg=True, recenter=True,
        )
        parsing_mask = None
        shape_pose = self.pose_estimator(source_image_path + ".rembg.png")

        image, _, _ = infer_preprocess_image(
            source_image_path + ".rembg.png", mask=parsing_mask, intr=None,
            pad_ratio=0, bg_color=1.0, max_tgt_size=896,
            aspect_standard=5.0 / 3, enlarge_ratio=[1.0, 1.0],
            render_tgt_size=self.cfg.source_size, multiply=14, need_mask=True,
        )
        rgb = np.array(Image.open(source_image_path))[..., :3]
        rgb = torch.from_numpy(rgb).permute(2, 0, 1)
        bbox = self.face_detector.detect_face(rgb)
        head_rgb = rgb[:, int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]
        src_head_rgb = cv2.resize(head_rgb.permute(1, 2, 0).cpu().numpy(),
                                  (self.cfg.src_head_size, self.cfg.src_head_size))
        src_head_rgb = torch.from_numpy(src_head_rgb / 255.0).float().permute(2, 0, 1).unsqueeze(0)

        # 构建一次 3DGS (后续动作复用)
        gs_model_list, query_points, transform_mat = self.lhm.infer_single_view(
            image.unsqueeze(0).cuda(), src_head_rgb.unsqueeze(0).cuda(),
            None, None, render_c2ws=None, render_intrs=None,
            render_bg_colors=None, smplx_params=None,
        )
        self._avatar_cache[source_image_path] = {
            "gs_model_list": gs_model_list,
            "query_points": query_points,
            "transform_mat": transform_mat,
            "shape_param": shape_pose.beta,
        }
        return self._avatar_cache[source_image_path]

    def render_with_motion(self, source_image_path: str, motion_params_dir: str,
                            output_video_path: str) -> str:
        """
        用缓存的 3DGS 形象 + 指定 SMPL-X 动作, 渲染全身视频。
        Args:
            motion_params_dir: SMPL-X 参数目录(由 video2motion.py 产出)
        Returns: 输出视频路径
        """
        import torch
        from app import animation_infer
        from LHM.runners.infer.utils import prepare_motion_seqs
        from LHM.utils.ffmpeg_utils import images_to_video

        avatar = self.init_avatar(source_image_path)
        motion_seq = prepare_motion_seqs(
            motion_params_dir, None, save_root=output_video_path + ".tmp",
            fps=30, bg_color=1.0, aspect_standard=5.0 / 3, enlarge_ratio=[1.0, 1.0],
            render_image_res=self.cfg.render_size, multiply=16, need_mask=False,
            vis_motion=False, motion_size=3000,
        )
        shape_param = torch.tensor(avatar["shape_param"], dtype=torch.float32).unsqueeze(0).cuda()
        smplx_params = motion_seq["smplx_params"]
        smplx_params["betas"] = shape_param

        camera_size = len(motion_seq["motion_seqs"])
        batch_size = 40
        batch_list = []
        for batch_i in range(0, camera_size, batch_size):
            keys = ["root_pose", "body_pose", "jaw_pose", "leye_pose", "reye_pose",
                    "lhand_pose", "rhand_pose", "trans", "focal", "princpt",
                    "img_size_wh", "expr"]
            batch_smplx = {"betas": shape_param,
                           "transform_mat_neutral_pose": avatar["transform_mat"]}
            for k in keys:
                batch_smplx[k] = smplx_params[k][:, batch_i:batch_i + batch_size].cuda()
            res = self.lhm.animation_infer(
                avatar["gs_model_list"], avatar["query_points"], batch_smplx,
                render_c2ws=motion_seq["render_c2ws"][:, batch_i:batch_i + batch_size].cuda(),
                render_intrs=motion_seq["render_intrs"][:, batch_i:batch_i + batch_size].cuda(),
                render_bg_colors=motion_seq["render_bg_colors"][:, batch_i:batch_i + batch_size].cuda(),
            )
            comp_rgb = res["comp_rgb"]
            comp_mask = res["comp_mask"]
            comp_mask[comp_mask < 0.5] = 0.0
            batch_rgb = comp_rgb * comp_mask + (1 - comp_mask) * 1
            batch_rgb = (batch_rgb.clamp(0, 1) * 255).to(torch.uint8).cpu().numpy()
            batch_list.append(batch_rgb)
            del res
            torch.cuda.empty_cache()

        rgb = np.concatenate(batch_list, axis=0)
        images_to_video(rgb, output_path=output_video_path, fps=self.render_fps,
                        gradio_codec=False, verbose=True)
        return output_video_path

    def render_speaking(self, audio, sample_rate, source_image_path=None):
        """LHM 离线后端不支持音频驱动实时说话, 走动作模板。"""
        raise NotImplementedError(
            "LHM 为离线3D后端, 不支持音频实时驱动。请用 render_with_motion 配合带口型动画的 SMPL-X 动作, "
            "或使用 LivePortrait 后端做实时问答。"
        )

    def render_idle(self, duration=3.0, source_image_path=None):
        raise NotImplementedError("LHM 待机画面请用 render_with_motion + idle 动作模板生成。")
