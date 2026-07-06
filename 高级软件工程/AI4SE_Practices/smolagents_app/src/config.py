"""
配置管理：模型参数、路径配置
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """模型配置"""
    provider: str = "openai"  # "openai" 或 "huggingface"
    model_id: str = "gpt-4.1"
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.2


@dataclass
class FrameworkConfig:
    """框架配置"""
    project_root: str = "."
    output_dir: str = "output"
    max_steps_per_agent: int = 8
    enable_verbose: bool = True


def load_config() -> tuple[ModelConfig, FrameworkConfig]:
    """加载配置"""
    model_config = ModelConfig(
        api_base=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    framework_config = FrameworkConfig()
    return model_config, framework_config


def get_project_root() -> Path:
    """获取项目根目录（src 的上一级目录）"""
    return Path(__file__).resolve().parent.parent
