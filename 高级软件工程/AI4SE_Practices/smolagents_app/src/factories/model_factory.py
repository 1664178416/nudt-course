"""
模型工厂：创建可用的 LLM 模型实例
"""

from smolagents import OpenAIServerModel, InferenceClientModel
from ..config import load_config


def create_model():
    """创建模型"""
    model_config, _ = load_config()

    # 优先使用 OpenAI Server Model（如果有配置）
    if model_config.api_base or model_config.api_key:
        return OpenAIServerModel(
            model_id=model_config.model_id,
            api_base=model_config.api_base,
            api_key=model_config.api_key,
        )

    # 否则使用 InferenceClientModel
    return InferenceClientModel()
