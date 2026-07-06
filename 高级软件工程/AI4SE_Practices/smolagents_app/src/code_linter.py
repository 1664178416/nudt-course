"""代码检查器模块

检测代码中的语法错误、潜在问题和规范问题。
"""

import ast
import re
from typing import Dict, List, Tuple, Any


class CodeLinter:
    """代码检查器

    检测代码中的语法错误、潜在问题和规范问题。
    """

    def __init__(self):
        self.rules = {
            "syntax_error": self._check_syntax_error,
            "undefined_variables": self._check_undefined_variables,
            "unreachable_code": self._check_unreachable_code,
            "unused_imports": self._check_unused_imports,
            "shadowed_variables": self._check_shadowed_variables,
            "missing_docstrings": self._check_missing_docstrings,
            "line_length": self._check_line_length,
            "indentation": self._check_indentation,
        }

    def lint(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        """检测代码中的问题

        Args:
            code: 要检测的Python代码

        Returns:
            包含所有检测到的问题的字典
        """
        issues = {}

        for rule_name, rule_func in self.rules.items():
            try:
                rule_issues = rule_func(code)
                if rule_issues:
                    issues[rule_name] = rule_issues
            except Exception as e:
                print(f"Error running rule {rule_name}: {e}")

        return issues

    def _check_syntax_error(self, code: str) -> List[Dict[str, Any]]:
        """检查语法错误"""
        issues = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append({
                "line": e.lineno,
                "column": e.offset,
                "message": f"语法错误: {e.msg}"
            })
        return issues

    def _check_undefined_variables(self, code: str) -> List[Dict[str, Any]]:
        """检查未定义的变量"""
        issues = []
        try:
            tree = ast.parse(code)
            # 简单的变量定义检测
            defined_vars = set()
            used_vars = set()

            class VariableAnalyzer(ast.NodeVisitor):
                def visit_FunctionDef(self, node):
                    # 函数参数
                    for arg in node.args.args:
                        defined_vars.add(arg.arg)
                    # 函数内部变量
                    self.generic_visit(node)

                def visit_Assign(self, node):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined_vars.add(target.id)
                    self.generic_visit(node)

                def visit_Name(self, node):
                    if isinstance(node.ctx, ast.Load):
                        used_vars.add(node.id)
                    self.generic_visit(node)

            analyzer = VariableAnalyzer()
            analyzer.visit(tree)

            # 检查内置变量和导入的模块
            builtins = {'True', 'False', 'None', 'print', 'len', 'range', 'list', 'dict', 'set', 'tuple'}
            undefined = used_vars - defined_vars - builtins

            for var in undefined:
                # 简单的行号检测
                for line_num, line in enumerate(code.split('\n'), 1):
                    if var in line and not re.search(r'\bimport\b|\bfrom\b', line):
                        issues.append({
                            "line": line_num,
                            "message": f"未定义的变量: {var}"
                        })
                        break
        except Exception:
            pass
        return issues

    def _check_unreachable_code(self, code: str) -> List[Dict[str, Any]]:
        """检查不可达代码"""
        issues = []
        try:
            tree = ast.parse(code)

            class UnreachableCodeAnalyzer(ast.NodeVisitor):
                def __init__(self):
                    self.unreachable_lines = []
                    self.current_function = None

                def visit_FunctionDef(self, node):
                    self.current_function = node.name
                    self.generic_visit(node)
                    self.current_function = None

                def visit_Return(self, node):
                    # 检查return语句后的代码
                    if hasattr(node, 'lineno'):
                        # 简单的检查，实际情况可能更复杂
                        lines = code.split('\n')
                        for i in range(node.lineno, len(lines)):
                            line = lines[i].strip()
                            if line and not line.startswith('#'):
                                issues.append({
                                    "line": i + 1,
                                    "message": "不可达代码: return语句后的代码永远不会执行"
                                })
                                break
                    self.generic_visit(node)

            analyzer = UnreachableCodeAnalyzer()
            analyzer.visit(tree)
        except Exception:
            pass
        return issues

    def _check_unused_imports(self, code: str) -> List[Dict[str, Any]]:
        """检查未使用的导入"""
        issues = []
        try:
            tree = ast.parse(code)
            imports = {}
            used_names = set()

            class ImportAnalyzer(ast.NodeVisitor):
                def visit_Import(self, node):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = node.lineno
                    self.generic_visit(node)

                def visit_ImportFrom(self, node):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = node.lineno
                    self.generic_visit(node)

                def visit_Name(self, node):
                    if isinstance(node.ctx, ast.Load):
                        used_names.add(node.id)
                    self.generic_visit(node)

            analyzer = ImportAnalyzer()
            analyzer.visit(tree)

            for name, line in imports.items():
                if name not in used_names:
                    issues.append({
                        "line": line,
                        "message": f"未使用的导入: {name}"
                    })
        except Exception:
            pass
        return issues

    def _check_shadowed_variables(self, code: str) -> List[Dict[str, Any]]:
        """检查变量遮蔽"""
        issues = []
        try:
            tree = ast.parse(code)

            class ShadowedVariableAnalyzer(ast.NodeVisitor):
                def __init__(self):
                    self.scopes = []

                def visit_FunctionDef(self, node):
                    # 检查函数参数是否遮蔽外部变量
                    local_vars = set(arg.arg for arg in node.args.args)
                    if self.scopes and local_vars.intersection(self.scopes[-1]):
                        for arg in node.args.args:
                            if arg.arg in self.scopes[-1]:
                                issues.append({
                                    "line": arg.lineno,
                                    "message": f"变量遮蔽: {arg.arg} 遮蔽了外部作用域的变量"
                                })
                    # 进入新作用域
                    self.scopes.append(local_vars)
                    self.generic_visit(node)
                    # 退出作用域
                    self.scopes.pop()

            analyzer = ShadowedVariableAnalyzer()
            analyzer.visit(tree)
        except Exception:
            pass
        return issues

    def _check_missing_docstrings(self, code: str) -> List[Dict[str, Any]]:
        """检查缺失的文档字符串"""
        issues = []
        try:
            tree = ast.parse(code)

            class DocstringAnalyzer(ast.NodeVisitor):
                def visit_FunctionDef(self, node):
                    if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str)):
                        issues.append({
                            "line": node.lineno,
                            "message": f"函数 {node.name} 缺少文档字符串"
                        })
                    self.generic_visit(node)

                def visit_ClassDef(self, node):
                    if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str)):
                        issues.append({
                            "line": node.lineno,
                            "message": f"类 {node.name} 缺少文档字符串"
                        })
                    self.generic_visit(node)

            analyzer = DocstringAnalyzer()
            analyzer.visit(tree)
        except Exception:
            pass
        return issues

    def _check_line_length(self, code: str) -> List[Dict[str, Any]]:
        """检查行长度"""
        issues = []
        max_length = 79  # PEP 8 建议的最大行长度
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            if len(line) > max_length:
                issues.append({
                    "line": line_num,
                    "message": f"行长度超过 {max_length} 字符: {len(line)} 字符"
                })
        return issues

    def _check_indentation(self, code: str) -> List[Dict[str, Any]]:
        """检查缩进"""
        issues = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            if line.strip() and not line.startswith(' ' * (len(line) - len(line.lstrip()))):
                # 简单的缩进检查，实际情况可能更复杂
                indent = len(line) - len(line.lstrip())
                if indent % 4 != 0:  # PEP 8 建议使用4个空格缩进
                    issues.append({
                        "line": line_num,
                        "message": f"缩进应该是4个空格的倍数: 当前缩进 {indent} 空格"
                    })
        return issues

    def get_recommendations(self, issues: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """根据检测到的问题生成改进建议"""
        recommendations = []

        if issues.get("syntax_error"):
            recommendations.append("修复所有语法错误")

        if issues.get("undefined_variables"):
            recommendations.append("定义所有使用的变量")

        if issues.get("unreachable_code"):
            recommendations.append("移除不可达代码")

        if issues.get("unused_imports"):
            recommendations.append("移除未使用的导入")

        if issues.get("shadowed_variables"):
            recommendations.append("避免变量遮蔽，使用不同的变量名")

        if issues.get("missing_docstrings"):
            recommendations.append("为所有函数和类添加文档字符串")

        if issues.get("line_length"):
            recommendations.append("缩短过长的行，保持在79字符以内")

        if issues.get("indentation"):
            recommendations.append("使用4个空格的缩进")

        return recommendations
