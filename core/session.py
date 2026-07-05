"""
DigitalHumanSession — 数字人会话核心

串联对话引擎(ASR→LLM→TTS)与渲染后端, 提供两类入口:
  - talk(audio): 一次性问答(语音进→语音出+视频)
  - talk_stream(text): 流式问答(文本进→流式出视频), 降低首字延迟

设计要点:
  - 渲染后端可在 liveportrait(实时头肩) / lhm(离线3D) 间切换, 由场景预设决定
  - LLM 流式输出按句切分, 每句独立 TTS + 渲染, 边出边播
  - 多轮对话维护 history
"""
import os
import tempfile
from typing import Generator, List, Dict, Optional

import numpy as np

from config import get_config
from conversation.llm import LLM
from conversation.tts import TTS
from renderer.base import get_renderer
from renderer.audio2lip import load_audio


class DigitalHumanSession:
    def __init__(self, scene: str = "consultant"):
        """
        Args:
            scene: 场景名, 对应 config.yaml 中 scenes 预设
        """
        cfg = get_config()
        if scene not in cfg["scenes"]:
            raise ValueError(f"未知场景: {scene}, 可选: {list(cfg['scenes'].keys())}")
        self.scene_cfg = cfg["scenes"][scene]
        self.scene_name = scene

        # 对话引擎
        self.llm = LLM(system_prompt=self.scene_cfg["llm_system_prompt"])
        self.tts = TTS()

        # 渲染后端 (按场景预设选择)
        self.renderer = get_renderer(self.scene_cfg["renderer"])
        self.history: List[Dict] = []

    def talk(self, audio_path: str) -> dict:
        """
        一次性语音问答。
        Args:
            audio_path: 用户语音文件路径
        Returns:
            {transcript, answer, audio_path, video_path, fps}
        """
        from conversation.asr import ASR
        asr = ASR()

        # 1. ASR: 语音 -> 文本
        transcript = asr.transcribe(audio_path)
        print(f"[ASR] 用户: {transcript}")

        # 2. LLM: 文本 -> 回答
        answer = self.llm.chat(transcript, self.history)
        print(f"[LLM] 数字人: {answer}")

        # 3. TTS: 回答 -> 音频文件
        tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        self.tts.synthesize_to_file(answer, tmp_wav)

        # 4. 加载音频 + 渲染说话视频
        audio, sr = load_audio(tmp_wav)
        frames, fps = self.renderer.render_speaking(audio, sr)

        # 5. 合成视频(带原音)
        video_path = self._frames_to_video(frames, fps, tmp_wav)

        # 更新历史
        self.history.append({"role": "user", "content": transcript})
        self.history.append({"role": "assistant", "content": answer})

        return {
            "transcript": transcript,
            "answer": answer,
            "audio_path": tmp_wav,
            "video_path": video_path,
            "fps": fps,
        }

    def talk_stream(self, text: str) -> Generator[dict, None, None]:
        """
        流式问答: 文本进, 逐句产出 {sentence, audio_chunk, frames}。
        用于实时场景, 边生成边播放。
        """
        print(f"[USER] {text}")
        sentence_buffer = []
        for sentence in self.llm.chat_stream_sentences(text, self.history):
            print(f"[LLM 句] {sentence}")
            # 每句 TTS -> 音频
            tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
            self.tts.synthesize_to_file(sentence, tmp_wav)
            audio, sr = load_audio(tmp_wav)
            # 每句渲染
            frames, fps = self.renderer.render_speaking(audio, sr)
            sentence_buffer.append(sentence)
            yield {
                "sentence": sentence,
                "audio_path": tmp_wav,
                "frames": frames,
                "fps": fps,
            }
        # 更新历史
        self.history.append({"role": "user", "content": text})
        self.history.append({"role": "assistant", "content": "".join(sentence_buffer)})

    def _frames_to_video(self, frames: list, fps: int, audio_path: str) -> str:
        """把帧列表 + 音频合成 mp4。"""
        import cv2
        tmp_mp4 = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        h, w = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(tmp_mp4, fourcc, fps, (w, h))
        for fr in frames:
            writer.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
        writer.release()
        # 合入音频
        final = tmp_mp4.replace(".mp4", "_final.mp4")
        os.system(
            f'ffmpeg -y -i "{tmp_mp4}" -i "{audio_path}" '
            f'-c:v copy -c:a aac -shortest "{final}" -loglevel error'
        )
        os.remove(tmp_mp4)
        return final


def create_session(scene: str = "consultant") -> DigitalHumanSession:
    """工厂: 按场景创建会话。"""
    return DigitalHumanSession(scene=scene)
