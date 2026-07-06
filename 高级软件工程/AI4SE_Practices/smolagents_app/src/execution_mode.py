"""
执行模式选择：在稳定性与速度优先场景下选择更短路径。
"""

import os
from .task_profiles import build_task_profile


def fast_mode_enabled() -> bool:
    """是否启用默认极速模式。默认开启。"""
    return os.getenv("SMOLAGENTS_FAST_MODE", "1").strip().lower() not in {"0", "false", "no"}


def force_full_flow() -> bool:
    """是否强制完整多角色流程。默认关闭。"""
    return os.getenv("SMOLAGENTS_FORCE_FULL_FLOW", "0").strip().lower() in {"1", "true", "yes"}


def should_use_fast_path(goal: str) -> bool:
    """当前任务是否应走极速路径。"""
    if force_full_flow():
        return False
    if not fast_mode_enabled():
        return False
    profile = build_task_profile(goal)
    return profile.artifact_type == "static_web_app"
