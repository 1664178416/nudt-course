"""
smolagents_app 核心包。

保持包级导入尽量轻量，避免在仅使用工具函数或运行测试时，
被 `smolagents` 等重依赖强制阻塞。
"""

from importlib import import_module

__version__ = "0.3.0"

_EXPORTS = {
    "RequirementAgent": ("src.agents", "RequirementAgent"),
    "DesignAgent": ("src.agents", "DesignAgent"),
    "ImplementationAgent": ("src.agents", "ImplementationAgent"),
    "VerificationAgent": ("src.agents", "VerificationAgent"),
    "create_requirement_agent": ("src.agents", "create_requirement_agent"),
    "create_design_agent": ("src.agents", "create_design_agent"),
    "create_implementation_agent": ("src.agents", "create_implementation_agent"),
    "create_test_agent": ("src.agents", "create_test_agent"),
    "create_verification_agent": ("src.agents", "create_verification_agent"),
    "TaskOrchestrator": ("src.orchestrator", "TaskOrchestrator"),
    "RunResult": ("src.orchestrator", "RunResult"),
    "RequirementSpec": ("src.data.specs", "RequirementSpec"),
    "DesignSpec": ("src.data.specs", "DesignSpec"),
    "VerificationReport": ("src.data.specs", "VerificationReport"),
    "ModelConfig": ("src.config", "ModelConfig"),
    "FrameworkConfig": ("src.config", "FrameworkConfig"),
    "load_config": ("src.config", "load_config"),
    "save_results_to_output": ("src.utils", "save_results_to_output"),
    "extract_code_from_output": ("src.utils", "extract_code_from_output"),
    "format_agent_output": ("src.utils", "format_agent_output"),
    "Task": ("src.tasks", "Task"),
    "TaskRegistry": ("src.tasks", "TaskRegistry"),
    "build_default_registry": ("src.tasks", "build_default_registry"),
    "create_model": ("src.factories", "create_model"),
    "create_manager_agent": ("src.factories", "create_manager_agent"),
    "parse_agent_output": ("src.parsing", "parse_agent_output"),
    "launch_gradio_demo": ("src.apps", "launch_gradio_demo"),
    "run_cli_example": ("src.apps", "run_cli_example"),
    "create_run_dir": ("src.runtime", "create_run_dir"),
    "get_current_run_dir": ("src.runtime", "get_current_run_dir"),
    "run_context": ("src.runtime", "run_context"),
}

__all__ = ["__version__", *_EXPORTS.keys()]


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module 'src' has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
