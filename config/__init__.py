"""配置加载与缓存。"""
import os
from pathlib import Path
import yaml

_CONFIG = None
_BASE_DIR = Path(__file__).resolve().parent


def load_config(config_path: str = None) -> dict:
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    if config_path is None:
        config_path = _BASE_DIR / "config" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        raw = f.read()
    # 展开 ${ENV_VAR}
    def _expand(env_match):
        return os.environ.get(env_match.group(1), "")
    import re
    raw = re.sub(r"\$\{(\w+)\}", _expand, raw)
    _CONFIG = yaml.safe_load(raw)
    return _CONFIG


def get_config() -> dict:
    return load_config()


def project_root() -> Path:
    return _BASE_DIR
