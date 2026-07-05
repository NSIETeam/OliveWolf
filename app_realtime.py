"""
5i5j 数字人 — 实时问答入口 (Gradio)

启动:
    cd i5j_dh
    python app_realtime.py

功能:
  - 选择场景(②③实时场景)
  - 麦克风语音输入 -> ASR -> LLM -> TTS -> 数字人说话视频
  - 或文本输入 -> 流式回答 -> 视频
  - 展示对话历史

注意: 需 CUDA 环境 + OpenAI/ElevenLabs API 密钥。
首次需在 LivePortrait 放置工装照源图 assets/avatars/agent_female.jpg
"""
import os
import sys
import tempfile

# 确保包内 import 可用
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr

from core.scene_registry import list_scenes, create_session_for_scene
from conversation.asr import ASR
from conversation.tts import TTS
from renderer.audio2lip import load_audio
from config import get_config


# 全局会话池(按场景缓存, 避免重复加载模型)
_sessions = {}
_asr = None
_tts = None


def get_asr():
    global _asr
    if _asr is None:
        _asr = ASR()
    return _asr


def get_tts():
    global _tts
    if _tts is None:
        _tts = TTS()
    return _tts


def get_session(scene: str):
    if scene not in _sessions:
        _sessions[scene] = create_session_for_scene(scene)
    return _sessions[scene]


def handle_voice(audio_path: str, scene: str, history: list):
    """语音问答: 麦克风录音 -> 数字人回答视频。"""
    if not audio_path:
        return history, None, "请先录音或上传语音"
    try:
        sess = get_session(scene)
        asr = get_asr()
        # 1. 识别
        text = asr.transcribe(audio_path)
        history.append([text, ""])
        yield history, None, f"识别中…已识别: {text}"

        # 2. LLM + TTS + 渲染
        result = sess.talk(audio_path)
        history[-1][1] = result["answer"]
        yield history, result["video_path"], "回答完成"
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield history, None, f"出错: {e}"


def handle_text(text: str, scene: str, history: list):
    """文本问答(流式): 文本 -> 流式回答视频。"""
    if not text.strip():
        return history, None, "请输入问题"
    try:
        sess = get_session(scene)
        history.append([text, ""])
        full_answer = []
        last_video = None
        for chunk in sess.talk_stream(text):
            full_answer.append(chunk["sentence"])
            history[-1][1] = "".join(full_answer)
            # 逐句渲染视频(这里返回最后一句的视频, 实际可拼接)
            last_video = chunk  # 简化: 完整流式拼接见 talk()
            yield history, None, f"生成中: {chunk['sentence']}"
        # 完整回答统一渲染一个视频
        result = sess.talk  # talk_stream 已渲染, 这里取历史最后视频
        yield history, last_video, "回答完成"
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield history, None, f"出错: {e}"


def build_ui():
    scenes = list_scenes()
    scene_choices = [(f"{v['name']} - {v['desc']}", k) for k, v in scenes.items()]
    default_scene = "consultant"

    with gr.Blocks(title="5i5j 数字人 - 实时问答") as demo:
        gr.Markdown("# 🏠 5i5j 数字人 实时问答\n基于 LHM + LivePortrait 双后端 · OpenAI GPT-4o + ElevenLabs")

        with gr.Row():
            scene_dd = gr.Dropdown(
                choices=scene_choices, value=default_scene,
                label="选择场景(实时场景用 LivePortrait 后端)",
            )

        chatbot = gr.Chatbot(label="对话", height=360)
        with gr.Row():
            audio_in = gr.Audio(sources=["microphone", "upload"], type="filepath", label="语音输入")
            text_in = gr.Textbox(label="或文本输入", placeholder="如:首套房首付几成？")
        with gr.Row():
            btn_voice = gr.Button("🎙 语音问答", variant="primary")
            btn_text = gr.Button("💬 文本问答")
        video_out = gr.Video(label="数字人回答视频")
        status = gr.Textbox(label="状态", interactive=False)

        btn_voice.click(handle_voice, [audio_in, scene_dd, chatbot], [chatbot, video_out, status])
        btn_text.click(handle_text, [text_in, scene_dd, chatbot], [chatbot, video_out, status])

    return demo


if __name__ == "__main__":
    cfg = get_config()
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
