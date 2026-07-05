# 5i5j 数字人框架改造设计文档

> 基于 LHM（阿里通义·全身3D）+ LivePortrait（快手·2D头肩）双渲染后端，构建我爱我家四个业务场景的通用数字人框架，并实现实时问答能力。

---

## 一、技术边界（必读）

在动手前，必须正视两个开源项目的真实约束：

| 维度 | LHM (Large Human Model) | LivePortrait |
|------|------------------------|--------------|
| 产出 | 全身 3D 数字人（高质量） | 2D 头肩人像动画 |
| GPU | **必须 NVIDIA CUDA**，16~24GB 显存 | CUDA / **MPS(Apple Silicon)** |
| 速度 | 1.41~6.57s/次，按40帧批量渲染 | 实时可达成（TensorRT 加速后30fps+）|
| 驱动方式 | SMPL-X 动作参数（.npz/.pkl） | 驱动视频 / 动作模板(.pkl) / **音频→口型** |
| 适合场景 | 离线批量出片、VR房源讲解、直播切片 | 实时问答、客服、直播口播 |

**结论**：实时问答走 LivePortrait（头肩），高质量全身3D走 LHM 离线。两套渲染后端统一封装在 `renderer` 接口下，业务层不感知差异。

---

## 二、架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    业务场景层 (Scenes)                    │
│  房源讲解员 / 智能置业顾问 / 直播主播 / 流程讲解员         │
└──────────────────────┬──────────────────────────────────┘
                       │ 统一 DigitalHumanSession
┌──────────────────────▼──────────────────────────────────┐
│                  对话引擎层 (Conversation)               │
│  ASR(语音→文本) → LLM(GPT-4o) → TTS(ElevenLabs)         │
│         ↑ 流式: 边出文本边出音频，降低首字延迟            │
└──────────────────────┬──────────────────────────────────┘
                       │ 音频流 / 文本流
┌──────────────────────▼──────────────────────────────────┐
│                  渲染抽象层 (Renderer)                   │
│  ┌─────────────────┐        ┌─────────────────────────┐ │
│  │ LivePortrait后端 │        │      LHM后端(离线)       │ │
│  │ 实时·头肩·音频驱动│        │ 全身3D·SMPL-X动作驱动    │ │
│  │ audio→lip_ratio │        │ image+motion→3DGS video │ │
│  └─────────────────┘        └─────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              基础设施层 (Infra)                           │
│  数字人资产库 / 知识库(RAG) / 任务队列 / 推流             │
└─────────────────────────────────────────────────────────┘
```

---

## 三、四个场景的渲染后端选型

| 场景 | 渲染后端 | 理由 |
|------|---------|------|
| ① 线上金牌讲解员 | **LHM 离线** | 需要全身走动配合VR/房源视频，3D沉浸感强；可预渲染缓存 |
| ② 7×24智能置业顾问 | **LivePortrait 实时** | 实时问答，头肩即可，延迟低 |
| ③ 新房直播主播 | **LivePortrait 实时** | 长时口播，头肩稳定；可叠加全身动作模板 |
| ④ 签约/过户流程讲解员 | **LHM 离线 或 LivePortrait** | 内容固定可预渲染；线下大屏可用3D增强 |

---

## 四、核心改造点（对接真实代码）

### 4.1 LivePortrait 音频驱动改造（实时问答核心）

**原始机制**：`live_portrait_pipeline.py` 用驱动视频提取 `c_d_lip_lst`（每帧嘴部开合比），再调 `retarget_lip` 驱动口型。

**改造**：绕过驱动视频，直接由音频生成 `lip_close_ratio` 序列。

- 关键函数链（已确认真实签名）：
  - `LivePortraitWrapper.retarget_lip(kp_source, lip_close_ratio)` — 口型注入点
  - `retargeting_utils.calc_lip_close_ratio(lmk)` — 距离比 = ‖lmk[90]-lmk[102]‖ / ‖lmk[48]-lmk[66]‖
  - `calc_combined_lip_ratio(c_d_lip, source_lmk)` — 拼接源图基准比，喂给 retarget_lip

- 音频→口型比映射：用音频能量/音素特征驱动 `lip_close_ratio` ∈ [0, 1]。
  - 轻量方案：音频分帧 RMS 能量 → 平滑 → 映射到开合度
  - 进阶方案：接入 wav2lip/SyncNet 预测精确口型（见 `renderer/audio2lip.py`）

### 4.2 LHM 动作复用改造（离线出片提效）

**原始机制**：`app.py` 每次都重算 `pose_estimator` + `infer_single_view`。

**改造**：抽离 LHM 的 `animation_infer`，做成"形象构建一次、动作复用多次"：
- `infer_single_view` 产出的 `gs_model_list, query_points, transform_mat` 可缓存
- 不同房源/话术只换 SMPL-X 动作参数，复用同一数字人形象，避免重复重建 3DGS

---

## 五、目录结构

```
digital-human/
├── LHM/                      # 原始开源（全身3D）
├── LivePortrait/             # 原始开源（2D头肩）
└── i5j_dh/                   # ★ 我爱我家的数字人框架（新增）
    ├── README.md
    ├── config/
    │   └── config.yaml       # 统一配置（API密钥、资产路径、场景参数）
    ├── core/
    │   ├── session.py        # DigitalHumanSession：串联对话+渲染
    │   └── scene_registry.py # 四场景注册与参数预设
    ├── conversation/
    │   ├── asr.py            # 语音识别（OpenAI Whisper API）
    │   ├── llm.py            # 对话大脑（GPT-4o + 房产知识库）
    │   └── tts.py            # 语音合成（ElevenLabs，流式）
    ├── renderer/
    │   ├── base.py           # 渲染后端抽象接口
    │   ├── liveportrait_backend.py   # LivePortrait实时后端
    │   ├── audio2lip.py      # 音频→lip_close_ratio 适配层
    │   └── lhm_backend.py    # LHM离线后端
    ├── assets/
    │   ├── avatars/          # 数字人形象图/视频（工装照）
    │   ├── motions/          # 动作模板（讲解手势、站立待机）
    │   └── knowledge/        # 房产知识库（政策、税费、贷款）
    └── app_realtime.py       # 实时问答入口（Gradio）
```

---

## 六、实时问答数据流（场景②③）

```
用户语音 ──ASR──▶ 文本 ──LLM(RAG)──▶ 回答文本
                                      │ 流式分句
                                      ▼
                              TTS流式合成 ──▶ 音频分块
                                      │
                          ┌───────────┴───────────┐
                          ▼                       ▼
                   音频→lip_ratio          音频→播放/推流
                          │
                          ▼
              LivePortrait retarget_lip 逐帧渲染
                          │
                          ▼
                   数字人说话视频流 ──▶ 用户/直播间
```

**降延迟关键**：LLM 流式输出 → 按句切分 → 边合成边渲染边播放，首字延迟 < 1.5s 目标。

---

## 七、分阶段落地

- **Phase 1（当前）**：实时问答原型打通——ASR→LLM→TTS→LivePortrait音频驱动，单机CUDA验证
- **Phase 2**：LHM离线出片管线——形象缓存+动作复用，产出房源讲解视频
- **Phase 3**：房产知识库RAG接入，对话专业化
- **Phase 4**：直播推流 + 多形象管理 + 监控
