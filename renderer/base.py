"""
渲染后端抽象接口。
所有数字人渲染实现(2D头肩实时 / 3D全身离线)统一实现此接口,
使业务层(Session)不感知后端差异。
"""
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class BaseRenderer(ABC):
    @abstractmethod
    def init_avatar(self, source_image_path: str):
        """加载/构建数字人形象(源图或3D资产)。实时后端加载源图;离线后端构建3DGS。"""

    @abstractmethod
    def render_speaking(self, audio: np.ndarray, sample_rate: int, source_image_path: str = None) -> tuple:
        """
        根据音频渲染"说话"视频。

        Args:
            audio: TTS产出的波形 1D float32
            sample_rate: 采样率
            source_image_path: 可选,覆盖默认形象
        Returns:
            (frames: list[np.ndarray], audio_path: str, fps: int)
            frames 为 HxWx3 uint8 列表
        """

    @abstractmethod
    def render_idle(self, duration: float = 3.0, source_image_path: str = None) -> list:
        """渲染待机(闭嘴微动)画面,用于无对话时。"""


def get_renderer(renderer_name: str, **kwargs) -> BaseRenderer:
    """工厂方法:按名称获取渲染后端。"""
    if renderer_name == "liveportrait":
        from renderer.liveportrait_backend import LivePortraitBackend
        return LivePortraitBackend(**kwargs)
    elif renderer_name == "lhm":
        from renderer.lhm_backend import LHMBackend
        return LHMBackend(**kwargs)
    else:
        raise ValueError(f"未知渲染后端: {renderer_name}")
