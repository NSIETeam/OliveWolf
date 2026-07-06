# OliveWolf — 开源 3D 数字人引擎

> 基于开源项目 **LHM**(阿里通义·全身3D) + **LivePortrait**(快手·2D头肩) 双后端，
> 构建通用数字人框架，支持实时音频驱动问答与企业级部署。
>
> OliveWolf 是 [Miraphant](https://github.com/NSIETeam/miraphant) 的开源数字人产品。

完整设计见 [DESIGN.md](DESIGN.md)。

---

## 一、能做什么

| 场景 | 渲染后端 | 实时性 |
|------|---------|--------|
| ① 线上金牌讲解员 | LHM 全身3D | 离线出片 |
| ② 7×24智能置业顾问 | LivePortrait 头肩 | **实时问答** |
| ③ 新房直播主播 | LivePortrait 头肩 | **实时口播** |
| ④ 签约过户讲解员 | LHM 全身3D | 离线出片 |

---

## 二、环境要求

- **GPU**：NVIDIA CUDA（LHM需16-24GB显存；LivePortrait实时后端也建议CUDA）
- **Python**：3.10
- **前置依赖**：先在 `../LHM` 和 `../LivePortrait` 各自装好依赖与权重
- **API 密钥**：
  - `OPENAI_API_KEY`（GPT-4o + Whisper）
  - `ELEVENLABS_API_KEY` + `voice_id`

```bash
export OPENAI_API_KEY="sk-..."
export ELEVENLABS_API_KEY="..."
```

---

## 三、安装

```bash
cd i5j_dh
pip install -r requirements.txt

# LivePortrait 依赖（实时后端必需）
cd ../LivePortrait && pip install -r requirements.txt && cd ../i5j_dh
```

---

## 四、准备数字人形象

在 `assets/avatars/` 放置数字人源图：

- `agent_female.jpg` — LivePortrait 头肩形象（正面、中性表情、光照均匀）
- `agent_full_body.jpg` — LHM 全身形象

> 源图质量直接决定效果。建议专业拍摄，512x512 以上，正面无遮挡。

---

## 五、运行实时问答

```bash
python app_realtime.py
# 打开 http://localhost:7860
```

界面功能：
- 选择场景（②③ 为实时场景）
- 麦克风语音 或 文本输入
- 数字人返回说话视频

---

## 六、核心模块说明

### 实时问答数据流
```
语音/文本 → ASR(Whisper) → LLM(GPT-4o,流式) → TTS(ElevenLabs) → 音频
                                                              ↓
                                              audio2lip: 音频→lip_close_ratio
                                                              ↓
                                    LivePortrait retarget_lip → 逐帧渲染 → 视频
```

### 关键改造点

**1. 音频驱动口型** (`renderer/audio2lip.py`)
- 把 TTS 音频分帧算 RMS 能量 → 平滑 → 映射成 `lip_close_ratio` 序列
- 喂给 LivePortrait 的 `retarget_lip(x_s, combined_lip_ratio)` 驱动口型
- 这是实时问答的核心：绕过驱动视频，直接音频驱动

**2. 形象缓存复用** (`renderer/liveportrait_backend.py`)
- 源图预处理（人脸检测、3D特征提取）只做一次并缓存
- 多次说话复用 `x_s / f_s`，避免重复计算

**3. 双后端统一接口** (`renderer/base.py`)
- `BaseRenderer` 抽象，业务层用 `get_renderer(name)` 切换
- 实时用 `liveportrait`，离线3D用 `lhm`

---

## 七、离线3D出片（场景①④）

LHM 后端需在 CUDA 服务器：

```python
from renderer.lhm_backend import LHMBackend

backend = LHMBackend()
# 用全身形象 + 讲解动作渲染视频
backend.render_with_motion(
    source_image_path="assets/avatars/agent_full_body.jpg",
    motion_params_dir="../LHM/train_data/motion_video/mimo1/smplx_params",
    output_video_path="output/explainer.mp4",
)
```

动作参数可用 LHM 的 `video2motion.py` 从讲解视频中提取。

---

## 八、代码示例：纯对话（不渲染）

```python
from conversation.llm import LLM

llm = LLM(system_prompt="你是专业的企业数字人顾问，回答要准确、简洁、可信。")
for sentence in llm.chat_stream_sentences("请介绍一下你能做什么？"):
    print(sentence)  # 逐句输出，可喂 TTS
```

---

## 九、已知限制与后续

- **audio2lip 能量法**为轻量方案，口型与语音不完全精确；Phase 2 可接入 wav2lip/SyncNet
- **LHM 实时性**：全身3D暂只能离线；准实时需模型蒸馏+TensorRT，列为长期项
- **知识库 RAG**：Phase 3 接入房产政策/税费知识库，提升专业度
- **直播推流**：Phase 4 接 RTMP，支持③场景长时直播

---

## 十、目录结构

```
i5j_dh/
├── DESIGN.md                  # 架构设计文档
├── README.md                  # 本文件
├── requirements.txt
├── config/
│   ├── __init__.py            # 配置加载
│   └── config.yaml            # 统一配置
├── conversation/              # 对话引擎
│   ├── asr.py                 # 语音识别(Whisper)
│   ├── llm.py                 # LLM(GPT-4o,流式+按句)
│   └── tts.py                 # TTS(ElevenLabs,流式)
├── renderer/                  # 渲染后端
│   ├── base.py                # 抽象接口
│   ├── audio2lip.py           # ★音频→口型适配层
│   ├── liveportrait_backend.py# 实时头肩后端
│   └── lhm_backend.py         # 离线3D后端
├── core/
│   ├── session.py             # 会话串联
│   └── scene_registry.py      # 场景注册
├── assets/                    # 数字人资产(自备)
│   ├── avatars/
│   ├── motions/
│   └── knowledge/
└── app_realtime.py            # 实时问答入口(Gradio)
```
