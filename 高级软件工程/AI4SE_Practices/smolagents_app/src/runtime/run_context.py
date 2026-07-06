"""
任务运行上下文：管理每次任务的输出目录
"""

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
import os
from pathlib import Path
from typing import Optional

from ..config import get_project_root

_CURRENT_RUN_DIR: ContextVar[Optional[Path]] = ContextVar("current_run_dir", default=None)
_GLOBAL_RUN_DIR: Optional[Path] = None


def ensure_run_structure(run_dir: Path) -> Path:
    """创建任务目录结构"""
    for folder in [
        "input",
        "design",
        "src",
        "artifacts",
        "tests",
        "docs",
        "logs",
    ]:
        (run_dir / folder).mkdir(parents=True, exist_ok=True)
    return run_dir


def create_run_dir(base_output_dir: Optional[Path] = None, timestamp: Optional[str] = None) -> Path:
    """创建任务运行目录（默认位于项目根目录 output/ 下）"""
    base_dir = base_output_dir or (get_project_root() / "output")
    ts = timestamp or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = base_dir / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    return ensure_run_structure(run_dir)


def get_current_run_dir() -> Optional[Path]:
    """获取当前任务运行目录"""
    current = _CURRENT_RUN_DIR.get()
    if current is not None:
        return current
    if _GLOBAL_RUN_DIR is not None:
        return _GLOBAL_RUN_DIR
    env_dir = os.getenv("SMOLAGENTS_RUN_DIR")
    return Path(env_dir) if env_dir else None


def set_global_run_dir(run_dir: Optional[Path]) -> None:
    """设置/清除全局任务运行目录（用于跨线程/上下文）"""
    global _GLOBAL_RUN_DIR
    _GLOBAL_RUN_DIR = run_dir


@contextmanager
def run_context(run_dir: Path):
    """设置当前任务运行目录上下文"""
    token = _CURRENT_RUN_DIR.set(run_dir)
    old_env = os.getenv("SMOLAGENTS_RUN_DIR")
    os.environ["SMOLAGENTS_RUN_DIR"] = str(run_dir)
    try:
        yield run_dir
    finally:
        _CURRENT_RUN_DIR.reset(token)
        if old_env is None:
            os.environ.pop("SMOLAGENTS_RUN_DIR", None)
        else:
            os.environ["SMOLAGENTS_RUN_DIR"] = old_env
