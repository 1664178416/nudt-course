"""
对 smolagents 的轻量兼容封装。

用于在未安装 smolagents 时，仍能测试本地工具函数和非模型逻辑。
"""

from typing import Any, Callable, TypeVar


try:
    from smolagents import Tool, tool  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - 仅在测试或无依赖环境下触发
    Tool = Any
    F = TypeVar("F", bound=Callable[..., Any])

    def tool(func: F) -> F:
        return func
