import ast
import json
from ..smolagents_compat import tool
from .base import resolve_read_path

@tool
def analyze_code(file_path: str) -> str:
    """
    分析Python代码文件的结构，包括函数、类、导入等信息。返回JSON格式的分析结果。

    Args:
        file_path: 要分析的Python文件路径
    """
    try:
        path = resolve_read_path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code)
        analysis = {
            "file": str(path),
            "imports": [],
            "functions": [],
            "classes": [],
            "line_count": len(code.splitlines()),
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    analysis["imports"].append(f"{module}.{alias.name}")
            elif isinstance(node, ast.FunctionDef):
                analysis["functions"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                })
            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                analysis["classes"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": methods,
                })

        return json.dumps(analysis, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ 代码分析失败: {str(e)}"


@tool
def check_code_quality(file_path: str) -> str:
    """
    检查Python代码的质量，包括语法错误、代码风格、复杂度等。返回检查结果和建议。

    Args:
        file_path: 要检查的Python文件路径
    """
    try:
        path = resolve_read_path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        issues = []

        # 1. 语法检查
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(f"❌ 语法错误 (行 {e.lineno}): {e.msg}")
            return "代码质量检查结果：\n" + "\n".join(issues)

        # 2. 基础规范检查
        lines = code.splitlines()
        if len(lines) > 500:
            issues.append("⚠️ 文件过长 (>500行)，建议按功能模块拆分")

        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(f"⚠️ 行 {i} 过长 ({len(line)} 字符)，建议遵循 PEP 8 (<=120)")

        # 3. 文档字符串检查
        missing_docs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    missing_docs.append(f"{'函数' if isinstance(node, ast.FunctionDef) else '类'} '{node.name}' (行 {node.lineno})")
        
        if missing_docs:
            issues.append(f"⚠️ 建议为以下成员添加文档字符串: {', '.join(missing_docs)}")

        # 4. 圈复杂度初步检查 (简单统计分支)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = 1
                for subnode in ast.walk(node):
                    if isinstance(subnode, (ast.If, ast.For, ast.While, ast.And, ast.Or, ast.ExceptHandler)):
                        complexity += 1
                if complexity > 10:
                    issues.append(f"⚠️ 函数 '{node.name}' 复杂度较高 ({complexity})，建议重构")

        if issues:
            return "代码质量检查结果：\n" + "\n".join(issues)
        return "✅ 代码质量检查通过，未发现明显问题"
    except Exception as e:
        return f"❌ 代码质量检查失败: {str(e)}"
