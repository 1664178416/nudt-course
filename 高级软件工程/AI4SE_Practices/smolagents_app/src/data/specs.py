"""
规格数据结构：RequirementSpec、DesignSpec、VerificationReport
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional


@dataclass
class RequirementSpec:
    """需求规格"""
    functions: List[str]  # 功能列表
    constraints: List[str]  # 约束
    acceptance_criteria: List[str]  # 验收标准
    non_functional_requirements: List[str] = field(default_factory=list)
    artifact_type: str = "generic_software"
    deliverables: List[str] = field(default_factory=list)
    
    @classmethod
    def from_json(cls, json_str: str) -> "RequirementSpec":
        """从 JSON 字符串创建 RequirementSpec"""
        try:
            data = json.loads(json_str)
            return cls(
                functions=data.get("functions", []),
                constraints=data.get("constraints", []),
                acceptance_criteria=data.get("acceptance_criteria", []),
                non_functional_requirements=data.get("non_functional_requirements", []),
                artifact_type=data.get("artifact_type", "generic_software"),
                deliverables=data.get("deliverables", []),
            )
        except:
            # 如果解析失败，返回默认值
            return cls(functions=[], constraints=[], acceptance_criteria=[])
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    
    def __str__(self) -> str:
        return self.to_json()


@dataclass
class DesignSpec:
    """设计方案"""
    modules: List[Dict]  # 模块划分
    interfaces: List[Dict]  # 接口草图
    data_flow: str  # 数据流说明
    file_structure: Dict[str, Any] = field(default_factory=dict)
    technology_stack: List[str] = field(default_factory=list)
    artifact_type: str = "generic_software"
    deliverables: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_json(cls, json_str: str) -> "DesignSpec":
        """从 JSON 字符串创建 DesignSpec"""
        try:
            data = json.loads(json_str)
            return cls(
                modules=data.get("modules", []),
                interfaces=data.get("interfaces", []),
                data_flow=data.get("data_flow", ""),
                file_structure=data.get("file_structure", {}),
                technology_stack=data.get("technology_stack", []),
                artifact_type=data.get("artifact_type", "generic_software"),
                deliverables=data.get("deliverables", []),
            )
        except:
            return cls(modules=[], interfaces=[], data_flow="")
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    
    def __str__(self) -> str:
        return self.to_json()


@dataclass
class VerificationReport:
    """验证报告"""
    passed: bool  # 是否通过
    issues: List[str]  # 缺陷列表
    suggestions: List[str]  # 改进建议
    requirements_coverage: Dict[str, List[str]] = field(default_factory=dict)
    code_quality: Dict[str, Any] = field(default_factory=dict)
    test_results: str = ""
    overall_assessment: str = ""
    output_artifacts: List[str] = field(default_factory=list)
    
    @classmethod
    def from_json(cls, json_str: str) -> "VerificationReport":
        """从 JSON 字符串创建 VerificationReport"""
        try:
            data = json.loads(json_str)
            return cls(
                passed=data.get("passed", False),
                issues=data.get("issues", []),
                suggestions=data.get("suggestions", []),
                requirements_coverage=data.get("requirements_coverage", {}),
                code_quality=data.get("code_quality", {}),
                test_results=data.get("test_results", ""),
                overall_assessment=data.get("overall_assessment", ""),
                output_artifacts=data.get("output_artifacts", []),
            )
        except:
            return cls(passed=False, issues=[], suggestions=[])
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    
    def __str__(self) -> str:
        return self.to_json()
