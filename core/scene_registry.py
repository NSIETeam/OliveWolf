"""
场景注册表 — 四个业务场景的统一管理与参数预设。

场景与渲染后端映射:
  property_explainer (① 线上金牌讲解员)   -> lhm 离线3D
  consultant         (② 7×24智能置业顾问) -> liveportrait 实时
  live_streamer      (③ 新房直播主播)      -> liveportrait 实时
  process_guide      (④ 签约过户讲解员)    -> lhm 离线3D
"""
from config import get_config
from core.session import DigitalHumanSession


SCENE_INFO = {
    "property_explainer": {"name": "① 线上金牌讲解员", "desc": "全身3D，配合VR/房源视频边走边讲"},
    "consultant":         {"name": "② 7×24智能置业顾问", "desc": "实时头肩问答，解答政策税费贷款"},
    "live_streamer":      {"name": "③ 新房直播主播", "desc": "实时口播，直播带客留资"},
    "process_guide":      {"name": "④ 签约过户讲解员", "desc": "全身3D，逐步讲解网签过户流程"},
}


def list_scenes() -> dict:
    """返回所有场景信息。"""
    return SCENE_INFO


def get_scene_info(scene: str) -> dict:
    return SCENE_INFO.get(scene, {})


def create_session_for_scene(scene: str) -> DigitalHumanSession:
    """按场景创建数字人会话。"""
    if scene not in SCENE_INFO:
        raise ValueError(f"未知场景: {scene}, 可选: {list(SCENE_INFO.keys())}")
    return DigitalHumanSession(scene=scene)
