"""
音频 → 嘴部开合度(lip_close_ratio) 适配层

核心作用: 把 TTS 产出的音频转成 LivePortrait 所需的逐帧 lip_close_ratio 序列,
使其能通过 retarget_lip 驱动数字人口型, 实现音频驱动的实时说话。

LivePortrait 的 lip_close_ratio 语义:
  calc_lip_close_ratio(lmk) = ‖lmk[90]-lmk[102]‖ / ‖lmk[48]-lmk[66]‖
  即 嘴部上下唇距离 / 脸宽, 数值越大嘴张得越开。

本模块提供两种映射方案:
  - 能量法(默认): 音频分帧 RMS 能量 → 平滑 → 映射到 [0, open_scale]
    轻量、实时性好, 适合首版原型。口型与语音不完全同步, 但自然度可接受。
  - (进阶) wav2lip: 后续可接入精确音素口型预测, 见 TODO。
"""
import numpy as np

from config import get_config


class Audio2Lip:
    """音频 → lip_close_ratio 序列 适配器。"""

    def __init__(self):
        cfg = get_config()["liveportrait"]["audio2lip"]
        self.frame_rate = cfg["frame_rate"]
        self.smooth_window = cfg["smooth_window"]
        self.energy_threshold = cfg["energy_threshold"]
        self.open_scale = cfg["open_scale"]

    def audio_to_lip_ratios(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        将音频波形转换为 lip_close_ratio 序列。

        Args:
            audio: 1D float32 波形, 范围 [-1, 1]
            sample_rate: 采样率
        Returns:
            ratios: (n_frames,) float32, 每帧嘴部开合度 ∈ [0, open_scale]
        """
        n_frames = max(1, int(len(audio) / sample_rate * self.frame_rate))
        # 每帧的样本数
        frame_len = len(audio) // n_frames if n_frames > 0 else len(audio)

        energies = np.zeros(n_frames, dtype=np.float32)
        for i in range(n_frames):
            chunk = audio[i * frame_len: (i + 1) * frame_len]
            if len(chunk) == 0:
                continue
            # RMS 能量
            rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
            energies[i] = rms

        # 静音抑制: 能量低于阈值视为闭嘴
        energies[energies < self.energy_threshold] = 0.0

        # 归一化到 [0, 1] (用动态最大值, 避免极端值)
        max_e = energies.max() + 1e-6
        ratios = energies / max_e

        # 非线性映射(开方)让小幅张嘴更自然, 再乘上限
        ratios = np.sqrt(ratios) * self.open_scale

        # 平滑(滑动平均), 消除抖动
        ratios = self._smooth(ratios)
        return ratios.astype(np.float32)

    def _smooth(self, x: np.ndarray) -> np.ndarray:
        if self.smooth_window <= 1 or len(x) <= 1:
            return x
        # 边缘镜像填充的滑动平均
        pad = self.smooth_window // 2
        padded = np.pad(x, pad, mode="edge")
        kernel = np.ones(self.smooth_window) / self.smooth_window
        return np.convolve(padded, kernel, mode="valid")[: len(x)]

    def ratios_to_lip_inputs(self, ratios: np.ndarray) -> list:
        """将 ratio 序列转成 LivePortrait 需要的 c_d_lip 格式: list of [[ratio]]。"""
        return [[[float(r)]] for r in ratios]


def load_audio(audio_path: str, target_sr: int = 16000) -> np.ndarray:
    """加载音频文件为 1D float32 波形。"""
    import librosa
    audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)
    return audio.astype(np.float32), sr
