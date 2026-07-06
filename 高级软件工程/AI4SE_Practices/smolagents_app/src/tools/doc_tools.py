from pathlib import Path
from typing import Optional
from ..smolagents_compat import tool
from .base import resolve_readme_path

@tool
def generate_readme(project_name: str, description: str, features: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    根据项目信息生成README.md文件。输入项目名称、描述等信息，生成标准的README文档。

    Args:
        project_name: 项目名称
        description: 项目描述
        features: 功能列表（用逗号分隔）
        output_path: 输出文件路径（默认：README.md）
    """
    try:
        output_path = output_path or "README.md"
        output_path = resolve_readme_path(output_path)
        features_list = [f.strip() for f in features.split(",")] if features else []

        readme_content = f"""# {project_name}

{description}

## 功能特性

"""
        if features_list:
            for feature in features_list:
                readme_content += f"- {feature}\n"
        else:
            readme_content += "- 待添加功能特性\n"

        readme_content += """
## 使用方法

请查看 src/ 与 tests/ 目录中的代码与测试。
"""

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        return f"✅ README.md 已生成: {output_path}"
    except Exception as e:
        return f"❌ 生成README失败: {str(e)}"
