"""
对话引擎 - 语音识别 (ASR)
基于 OpenAI Whisper API，将用户语音转文本。
"""
import os
from pathlib import Path
from openai import OpenAI

from config import get_config


class ASR:
    def __init__(self):
        cfg = get_config()
        oc = cfg["openai"]
        api_key = os.environ.get("OPENAI_API_KEY", oc.get("api_key", ""))
        base_url = oc.get("base_url")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = oc["asr_model"]

    def transcribe(self, audio_path: str) -> str:
        """将音频文件转写为文本。"""
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
        with open(path, "rb") as f:
            resp = self.client.audio.transcriptions.create(
                model=self.model,
                file=f,
                language="zh",
            )
        return resp.text.strip()

    def transcribe_bytes(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """转写内存中的音频字节（适用于实时麦克风录音）。"""
        resp = self.client.audio.transcriptions.create(
            model=self.model,
            file=(filename, audio_bytes),
            language="zh",
        )
        return resp.text.strip()
