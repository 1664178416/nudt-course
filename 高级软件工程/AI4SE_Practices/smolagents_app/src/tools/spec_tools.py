from ..smolagents_compat import tool
from .base import require_run_dir

@tool
def save_requirement_spec(spec_json: str) -> str:
    """
    保存需求规格 JSON 到 input/requirement.json。

    Args:
        spec_json: JSON 字符串
    """
    try:
        run_dir = require_run_dir()
        path = run_dir / "input" / "requirement.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(spec_json)
        return f"✅ 需求规格已保存: {path}"
    except Exception as e:
        return f"❌ 保存需求规格失败: {str(e)}"


@tool
def save_design_spec(spec_json: str) -> str:
    """
    保存设计方案 JSON 到 design/design.json。

    Args:
        spec_json: JSON 字符串
    """
    try:
        run_dir = require_run_dir()
        path = run_dir / "design" / "design.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(spec_json)
        return f"✅ 设计方案已保存: {path}"
    except Exception as e:
        return f"❌ 保存设计方案失败: {str(e)}"


@tool
def save_verification_report(report_json: str) -> str:
    """
    保存验证报告 JSON 到 logs/verification.json。

    Args:
        report_json: JSON 字符串
    """
    try:
        run_dir = require_run_dir()
        path = run_dir / "logs" / "verification.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(report_json)
        return f"✅ 验证报告已保存: {path}"
    except Exception as e:
        return f"❌ 保存验证报告失败: {str(e)}"
