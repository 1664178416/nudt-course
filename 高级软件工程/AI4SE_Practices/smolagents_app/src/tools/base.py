from pathlib import Path
from ..runtime.run_context import get_current_run_dir

_RUN_SUBDIRS = {
    "input",
    "design",
    "src",
    "artifacts",
    "tests",
    "docs",
    "logs",
}


def require_run_dir() -> Path:
    run_dir = get_current_run_dir()
    if run_dir is None:
        raise RuntimeError("未设置任务目录（run_dir）。请通过 run_context 创建并设置。")
    return run_dir


def ensure_within_run_dir(path: Path, run_dir: Path) -> Path:
    resolved = path.resolve()
    run_resolved = run_dir.resolve()
    if not resolved.is_relative_to(run_resolved):
        raise RuntimeError("禁止访问任务目录之外的路径")
    return resolved


def resolve_read_path(path_value: str | None) -> Path:
    """读取路径解析：优先当前任务目录，其次项目根目录"""
    run_dir = require_run_dir()
    if not path_value:
        return run_dir
    path = Path(path_value)
    if path.is_absolute():
        return ensure_within_run_dir(path, run_dir)
    return run_dir / path


def resolve_source_write_path(path_value: str) -> Path:
    """源码写入路径解析：优先当前任务目录，默认写入 src/"""
    run_dir = require_run_dir()
    path = Path(path_value)
    if path.is_absolute():
        return ensure_within_run_dir(path, run_dir)
    if path.parts and path.parts[0] in _RUN_SUBDIRS:
        return run_dir / path
    return run_dir / "src" / path


def resolve_artifact_write_path(path_value: str) -> Path:
    """交付物写入路径解析：默认写入 artifacts/"""
    run_dir = require_run_dir()
    path = Path(path_value)
    if path.is_absolute():
        return ensure_within_run_dir(path, run_dir)
    if path.parts and path.parts[0] in _RUN_SUBDIRS:
        return run_dir / path
    return run_dir / "artifacts" / path


def resolve_readme_path(path_value: str) -> Path:
    """README 写入路径解析：写入当前任务根目录"""
    run_dir = require_run_dir()
    path = Path(path_value)
    if path.is_absolute():
        return ensure_within_run_dir(path, run_dir)
    return run_dir / path


def resolve_tests_write_path(path_value: str) -> Path:
    """测试写入路径解析：写入 tests/"""
    run_dir = require_run_dir()
    path = Path(path_value)
    if path.is_absolute():
        return ensure_within_run_dir(path, run_dir)
    if path.parts and path.parts[0] == "tests":
        return run_dir / path
    return run_dir / "tests" / path


def resolve_dir_path(path_value: str | None) -> Path:
    """目录路径解析：若任务目录存在且命中，优先任务目录"""
    run_dir = require_run_dir()
    if not path_value:
        return run_dir
    path = Path(path_value)
    if path.is_absolute():
        return ensure_within_run_dir(path, run_dir)
    return run_dir / path
