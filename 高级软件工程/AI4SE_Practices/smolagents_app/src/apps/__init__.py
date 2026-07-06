"""
应用入口模块：Gradio UI 与 CLI
"""

from .gradio_app import launch_gradio_demo
from .cli_app import run_cli_example

__all__ = [
    "launch_gradio_demo",
    "run_cli_example",
]
