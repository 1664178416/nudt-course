from typing import List
from smolagents.models import Model

from .requirement_agent import create_requirement_agent
from .design_agent import create_design_agent
from .implementation_agent import create_implementation_agent
from .test_agent import create_test_agent
from .verification_agent import create_verification_agent

# 保留旧接口以兼容
class RequirementAgent:
    """需求分析智能体 (RA) - 兼容接口"""
    def __init__(self, model: Model, tools: List):
        self.agent = create_requirement_agent(model, tools)
    
    def analyze(self, goal: str, context_paths: List[str] = None):
        context_info = f"\n相关文件/目录: {', '.join(context_paths)}" if context_paths else ""
        task = f"请分析以下需求并提取结构化需求规格：\n\n需求目标：{goal}{context_info}\n\n请输出 JSON 格式的需求规格。"
        return self.agent.run(task)


class DesignAgent:
    """方案设计智能体 (DA) - 兼容接口"""
    def __init__(self, model: Model, tools: List):
        self.agent = create_design_agent(model, tools)
    
    def design(self, req_spec):
        task = f"请根据以下需求规格设计技术方案：\n\n{req_spec}\n\n请输出 JSON 格式的设计方案。"
        return self.agent.run(task)


class ImplementationAgent:
    """实现智能体 (IA) - 兼容接口"""
    def __init__(self, model: Model, tools: List):
        self.agent = create_implementation_agent(model, tools)
    
    def implement(self, design_spec, context_paths: List[str] = None):
        context_info = f"\n当前项目路径: {', '.join(context_paths)}" if context_paths else ""
        task = f"请根据以下设计方案实现代码：\n\n{design_spec}{context_info}\n\n请使用 write_source_file 工具创建或修改代码文件。"
        result = self.agent.run(task)
        return {"output": result, "design_spec": str(design_spec)}


class VerificationAgent:
    """验证智能体 (VA) - 兼容接口"""
    def __init__(self, model: Model, tools: List):
        self.agent = create_verification_agent(model, tools)
    
    def verify(self, req_spec, design_spec, implementation):
        task = f"请验证以下实现是否满足需求：\n\n需求规格：\n{req_spec}\n\n设计方案：\n{design_spec}\n\n实现结果：\n{implementation.get('output', '')}\n\n请输出 JSON 格式的验证报告。"
        return self.agent.run(task)
