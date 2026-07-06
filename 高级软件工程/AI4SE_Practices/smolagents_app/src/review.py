"""
智能体输出自动化评审工具
支持需求规格、设计规格、实现代码的自动化评审
"""
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .tools import analyze_code, check_code_quality
from .data.specs import RequirementSpec, DesignSpec, VerificationReport

@dataclass
class ReviewResult:
    """评审结果"""
    type: str  # requirement/design/code
    passed: bool
    score: float  # 0-100
    issues: List[str]
    suggestions: List[str]

class AgentOutputReviewer:
    """智能体输出评审器"""
    def __init__(self):
        # 评审规则配置
        self.req_rules = [
            ("完整性", r"功能需求|非功能需求|接口需求|数据需求", "缺失核心需求分类"),
            ("可测性", r"每[\u4e00-\u9fa5]+需求[\u4e00-\u9fa5]+可验证", "需求缺乏可验证性描述"),
            ("无歧义", r"大约|可能|大概|尽量", "需求包含模糊性词汇")
        ]
        self.design_rules = [
            ("架构分层", r"表现层|业务层|数据层|接口层", "设计未体现分层架构"),
            ("接口定义", r"接口名称|入参|出参|异常处理", "接口定义不完整"),
            ("技术选型", r"使用[\u4e00-\u9fa5]+框架|[\u4e00-\u9fa5]+库|[\u4e00-\u9fa5]+技术", "未明确技术选型")
        ]
        self.code_rules = {
            "min_complexity": 10,  # 最大圈复杂度
            "min_coverage": 80,    # 最小测试覆盖率
            "max_issues": 0        # 最大代码质量问题数
        }

    def review_requirement(self, req_spec: RequirementSpec) -> ReviewResult:
        """评审需求规格"""
        req_text = req_spec.content
        score = 100
        issues = []
        suggestions = []

        # 检查每条规则
        for rule_name, pattern, error_msg in self.req_rules:
            if not re.search(pattern, req_text):
                if "模糊性词汇" in error_msg:
                    # 模糊词汇是扣分项，不是否决项
                    score -= 10
                    issues.append(f"{rule_name}: {error_msg}")
                    suggestions.append(f"移除'{pattern.strip()}'等模糊词汇，明确需求描述")
                else:
                    score -= 20
                    issues.append(f"{rule_name}: {error_msg}")
                    suggestions.append(f"补充{rule_name}相关内容，确保需求完整")

        # 边界处理
        score = max(0, score)
        passed = score >= 80 and len([i for i in issues if "缺失核心" in i]) == 0

        return ReviewResult(
            type="requirement",
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions
        )

    def review_design(self, design_spec: DesignSpec) -> ReviewResult:
        """评审设计规格"""
        design_text = design_spec.content
        score = 100
        issues = []
        suggestions = []

        for rule_name, pattern, error_msg in self.design_rules:
            if not re.search(pattern, design_text):
                score -= 20
                issues.append(f"{rule_name}: {error_msg}")
                suggestions.append(f"补充{rule_name}相关设计内容，完善架构设计")

        score = max(0, score)
        passed = score >= 80

        return ReviewResult(
            type="design",
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions
        )

    def review_code(self, code_path: str) -> ReviewResult:
        """评审实现代码"""
        # 代码质量分析
        quality_report = check_code_quality(code_path)
        code_analysis = analyze_code(code_path)

        score = 100
        issues = []
        suggestions = []

        # 检查圈复杂度
        if code_analysis.get("cyclomatic_complexity", 0) > self.code_rules["min_complexity"]:
            score -= 25
            issues.append(f"圈复杂度超标: 当前{code_analysis['cyclomatic_complexity']} > 阈值{self.code_rules['min_complexity']}")
            suggestions.append("拆分复杂函数，降低圈复杂度")

        # 检查测试覆盖率
        if quality_report.get("coverage", 0) < self.code_rules["min_coverage"]:
            score -= 20
            issues.append(f"测试覆盖率不足: 当前{quality_report['coverage']}% < 阈值{self.code_rules['min_coverage']}%")
            suggestions.append("补充单元测试，提升测试覆盖率")

        # 检查代码质量问题
        quality_issues = quality_report.get("issues", [])
        if len(quality_issues) > self.code_rules["max_issues"]:
            score -= len(quality_issues) * 5
            issues.append(f"代码质量问题: 共{len(quality_issues)}个")
            suggestions.extend([f"修复{issue['type']}: {issue['message']}" for issue in quality_issues[:3]])

        score = max(0, score)
        passed = score >= 75

        return ReviewResult(
            type="code",
            passed=passed,
            score=score,
            issues=issues,
            suggestions=suggestions
        )

    def review_all(self, 
                  req_spec: Optional[RequirementSpec] = None,
                  design_spec: Optional[DesignSpec] = None,
                  code_path: Optional[str] = None) -> Dict[str, ReviewResult]:
        """批量评审所有类型"""
        results = {}
        if req_spec:
            results["requirement"] = self.review_requirement(req_spec)
        if design_spec:
            results["design"] = self.review_design(design_spec)
        if code_path:
            results["code"] = self.review_code(code_path)
        return results

# 便捷函数：生成评审报告
def generate_review_report(
    output_path: str = "review_report.json",
    req_spec: Optional[RequirementSpec] = None,
    design_spec: Optional[DesignSpec] = None,
    code_path: Optional[str] = None
):
    """生成并保存评审报告"""
    reviewer = AgentOutputReviewer()
    results = reviewer.review_all(req_spec, design_spec, code_path)
    
    # 转换为可序列化格式
    serializable_results = {k: asdict(v) for k, v in results.items()}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    # 输出控制台摘要
    print("=== 智能体输出评审报告 ===")
    for type_, res in results.items():
        print(f"\n{type_.upper()} 评审: {'通过' if res.passed else '未通过'} (得分: {res.score})")
        print(f"问题: {', '.join(res.issues) if res.issues else '无'}")
        print(f"建议: {', '.join(res.suggestions) if res.suggestions else '无'}")
    
    return results