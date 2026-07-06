"""
编排器：按 RA → DA → IA → VA 顺序执行智能体
"""

from dataclasses import dataclass
from typing import Optional
from .agents import RequirementAgent, DesignAgent, ImplementationAgent, VerificationAgent
from .data.specs import RequirementSpec, DesignSpec, VerificationReport


@dataclass
class RunResult:
    """运行结果"""
    requirement_spec: Optional[RequirementSpec] = None
    design_spec: Optional[DesignSpec] = None
    implementation: Optional[dict] = None
    verification_report: Optional[VerificationReport] = None
    success: bool = False
    error: Optional[str] = None


class TaskOrchestrator:
    """任务编排器"""
    
    def __init__(
        self,
        ra: RequirementAgent,
        da: DesignAgent,
        ia: ImplementationAgent,
        va: VerificationAgent
    ):
        self.ra = ra
        self.da = da
        self.ia = ia
        self.va = va
    
    def run_task(self, goal: str, context_paths: list[str] = None) -> RunResult:
        """执行完整任务流程"""
        try:
            # 1. 需求分析
            print("🔍 [RA] 开始需求分析...")
            req_spec = self.ra.analyze(goal, context_paths)
            print(f"✅ [RA] 需求分析完成\n{req_spec}\n")
            
            # 2. 方案设计
            print("📐 [DA] 开始方案设计...")
            design_spec = self.da.design(req_spec)
            print(f"✅ [DA] 方案设计完成\n{design_spec}\n")
            
            # 3. 实现
            print("💻 [IA] 开始代码实现...")
            implementation = self.ia.implement(design_spec, context_paths)
            print(f"✅ [IA] 代码实现完成\n")
            
            # 4. 验证
            print("✔️  [VA] 开始验证...")
            verification = self.va.verify(req_spec, design_spec, implementation)
            print(f"✅ [VA] 验证完成\n{verification}\n")
            
            return RunResult(
                requirement_spec=req_spec,
                design_spec=design_spec,
                implementation=implementation,
                verification_report=verification,
                success=verification.passed
            )
        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            return RunResult(
                success=False,
                error=error_msg
            )
