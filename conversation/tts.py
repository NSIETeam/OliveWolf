"""
对话引擎 - 语音合成 (TTS)
基于 ElevenLabs，支持流式合成以降低首字延迟。
"""
import os
from typing import Generator

from config import get_config


class TTS:
    def __init__(self):
        cfg = get_config()
        tc = cfg["tts"]
        self.provider = tc.get("provider", "elevenlabs")
        self.voice_id = tc.get("voice_id")
        self.model_id = tc.get("model_id", "eleven_multilingual_v2")
        self.stability = tc.get("stability", 0.5)
        self.similarity_boost = tc.get("similarity_boost", 0.75)
        self.streaming = tc.get("streaming", True)
        self.api_key = os.environ.get("ELEVENLABS_API_KEY", tc.get("api_key", ""))

        if self.provider == "elevenlabs":
            from elevenlabs import ElevenLabs
            self.client = ElevenLabs(api_key=self.api_key)
        else:
            raise ValueError(f"不支持的 TTS provider: {self.provider}")

    def synthesize(self, text: str) -> bytes:
        """一次性合成完整音频(MP3 bytes)。"""
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            model_id=self.model_id,
            text=text,
            voice_settings={
                "stability": self.stability,
                "similarity_boost": self.similarity_boost,
            },
            output_format="mp3_44100_128",
        )
        return b"".join(audio)

    def synthesize_stream(self, text: str) -> Generator[bytes, None, None]:
        """流式合成，逐块返回 MP3 bytes。用于边合成边播放/渲染。"""
        audio_stream = self.client.text_to_speech.stream(
            voice_id=self.voice_id,
            model_id=self.model_id,
            text=text,
            voice_settings={
                "stability": self.stability,
                "similarity_boost": self.similarity_boost,
            },
            output_format="mp3_44100_128",
        )
        for chunk in audio_stream:
            if chunk:
                yield chunk

    def synthesize_to_file(self, text: str, output_path: str) -> str:
        """合成并保存为 WAV 文件（供音频驱动口型用）。"""
        import subprocess
        mp3_path = output_path.rsplit(".", 1)[0] + ".mp3"
        audio_bytes = self.synthesize(text)
        with open(mp3_path, "wb") as f:
            f.write(audio_bytes)
        # 转 WAV（16kHz 单声道）便于 audio2lip 处理
        subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_path, "-ar", "16000", "-ac", "1", output_path],
            check=True, capture_output=True,
        )
        os.remove(mp3_path)
        return output_path
