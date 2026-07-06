"""
智能体输出解析工具
"""

import json
import re
from typing import Dict
from ..utils import extract_code_from_output


def parse_agent_output(output: str) -> Dict[str, object]:
    """解析智能体输出，提取各个阶段的结果"""
    result = {
        "requirement_spec": None,
        "design_spec": None,
        "implementation": None,
        "verification_report": None,
    }

    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_matches = re.findall(json_pattern, output, re.DOTALL)

    for json_str in json_matches:
        try:
            data = json.loads(json_str)
            if "functions" in data or "acceptance_criteria" in data:
                result["requirement_spec"] = json_str
            elif "modules" in data or "interfaces" in data:
                result["design_spec"] = json_str
            elif "passed" in data or "issues" in data:
                result["verification_report"] = json_str
        except Exception:
            pass

    code_blocks = extract_code_from_output(output)
    if code_blocks:
        result["implementation"] = {
            "output": output,
            "files": code_blocks,
        }
    else:
        result["implementation"] = {"output": output}

    return result
