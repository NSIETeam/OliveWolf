"""
对话引擎 - LLM 对话大脑
基于 OpenAI GPT-4o，流式输出。支持系统提示词与场景化预设。
"""
import os
import json
from typing import Generator, List, Dict

from openai import OpenAI

from config import get_config


class LLM:
    def __init__(self, system_prompt: str = None):
        cfg = get_config()
        oc = cfg["openai"]
        api_key = os.environ.get("OPENAI_API_KEY", oc.get("api_key", ""))
        base_url = oc.get("base_url")
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)
        self.model = oc["llm_model"]
        self.temperature = oc.get("llm_temperature", 0.6)
        self.max_tokens = oc.get("llm_max_tokens", 800)
        self.system_prompt = system_prompt or "你是5i5j的智能置业顾问，专业、亲和、诚信。"

    def chat(self, user_text: str, history: List[Dict] = None) -> str:
        """一次性返回完整回答（非流式）。"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return resp.choices[0].message.content.strip()

    def chat_stream(self, user_text: str, history: List[Dict] = None) -> Generator[str, None, None]:
        """流式输出，逐 token 返回。用于降低首字延迟。"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    def chat_stream_sentences(self, user_text: str, history: List[Dict] = None) -> Generator[str, None, None]:
        """流式输出并按句切分（按。！？.!?切分），适合喂给 TTS 分句合成。"""
        buffer = ""
        for token in self.chat_stream(user_text, history):
            buffer += token
            while True:
                # 找到第一个句子结束符
                idx = -1
                for punct in ["。", "！", "？", "!", "?", ".", "\n"]:
                    pos = buffer.find(punct)
                    if pos != -1 and (idx == -1 or pos < idx):
                        idx = pos
                        end_punct = punct
                if idx != -1:
                    sentence = buffer[: idx + len(end_punct)]
                    buffer = buffer[idx + len(end_punct) :]
                    sentence = sentence.strip()
                    if sentence:
                        yield sentence
                else:
                    break
        if buffer.strip():
            yield buffer.strip()
