"""格式化检查器模块

检查代码的格式化问题，确保代码符合PEP 8规范。
"""

import re
from typing import List, Dict, Any





class FormatChecker:
    """格式化检查器

    检查代码的格式化问题，确保代码符合PEP 8规范。
    """

    def __init__(self):
        self.checks = {
            "trailing_whitespace": self._check_trailing_whitespace,
            "blank_lines": self._check_blank_lines,
            "line_breaks": self._check_line_breaks,
            "quotation_style": self._check_quotation_style,
            "operator_spacing": self._check_operator_spacing,
            "comma_spacing": self._check_comma_spacing,
            "parentheses_spacing": self._check_parentheses_spacing,
            "comment_spacing": self._check_comment_spacing,
        }

    def check_format(self, code: str) -> Dict[str, List[Dict[str, Any]]]:
        """检查代码的格式化问题

        Args:
            code: 要检查的Python代码

        Returns:
            包含所有检测到的格式化问题的字典
        """
        issues = {}

        for check_name, check_func in self.checks.items():
            try:
                check_issues = check_func(code)
                if check_issues:
                    issues[check_name] = check_issues
            except Exception as e:
                print(f"Error running check {check_name}: {e}")

        return issues

    def _check_trailing_whitespace(self, code: str) -> List[Dict[str, Any]]:
        """检查行尾空白"""
        issues = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            if line.rstrip() != line:
                issues.append({
                    "line": line_num,
                    "message": "行尾存在空白字符"
                })
        return issues

    def _check_blank_lines(self, code: str) -> List[Dict[str, Any]]:
        """检查空行

        - 函数和类之间应该有两个空行
        - 函数内部的逻辑块之间应该有一个空行
        """
        issues = []
        lines = code.split('\n')
        
        # 检查函数和类之间的空行
        for i in range(len(lines) - 1):
            current_line = lines[i].strip()
            next_line = lines[i + 1].strip()
            
            if (current_line.startswith('def ') or current_line.startswith('class ')) and \
               (next_line.startswith('def ') or next_line.startswith('class ')):
                # 检查它们之间的空行数量
                blank_lines = 0
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        break
                    blank_lines += 1
                
                if blank_lines < 2:
                    issues.append({
                        "line": i + 1,
                        "message": "函数或类之间应该有两个空行"
                    })
        
        return issues

    def _check_line_breaks(self, code: str) -> List[Dict[str, Any]]:
        """检查换行

        - 避免反斜杠换行
        - 长行应该在括号、逗号或操作符后换行
        """
        issues = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            # 检查反斜杠换行
            if line.rstrip().endswith('\\'):
                issues.append({
                    "line": line_num,
                    "message": "避免使用反斜杠换行，应该使用括号"
                })
        return issues

    def _check_quotation_style(self, code: str) -> List[Dict[str, Any]]:
        """检查引号风格

        - 保持一致的引号风格（单引号或双引号）
        """
        issues = []
        # 简单的引号风格检查
        single_quotes = len(re.findall(r"'[^"]*'", code))
        double_quotes = len(re.findall(r'"[^']*"', code))
        
        if single_quotes > double_quotes * 2:
            # 主要使用单引号
            if double_quotes > 0:
                issues.append({
                    "line": 1,
                    "message": "引号风格不一致，建议统一使用单引号"
                })
        elif double_quotes > single_quotes * 2:
            # 主要使用双引号
            if single_quotes > 0:
                issues.append({
                    "line": 1,
                    "message": "引号风格不一致，建议统一使用双引号"
                })
        return issues

    def _check_operator_spacing(self, code: str) -> List[Dict[str, Any]]:
        """检查操作符间距

        - 操作符前后应该有空格
        """
        issues = []
        lines = code.split('\n')
        operators = ['+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', '+=', '-=', '*=', '/=']
        
        for line_num, line in enumerate(lines, 1):
            for op in operators:
                # 检查操作符前后是否有空格
                pattern = re.escape(op)
                # 跳过字符串和注释中的操作符
                if not re.search(r'["\'][^"\']*' + pattern + r'[^"\']*["\']|#.*' + pattern, line):
                    # 检查操作符前没有空格
                    if re.search(r'\S' + pattern, line):
                        issues.append({
                            "line": line_num,
                            "message": f"操作符 {op} 前应该有空格"
                        })
                    # 检查操作符后没有空格
                    if re.search(pattern + r'\S', line):
                        issues.append({
                            "line": line_num,
                            "message": f"操作符 {op} 后应该有空格"
                        })
        return issues

    def _check_comma_spacing(self, code: str) -> List[Dict[str, Any]]:
        """检查逗号间距

        - 逗号后应该有空格
        """
        issues = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            # 检查逗号后是否有空格
            if re.search(r',\S', line):
                issues.append({
                    "line": line_num,
                    "message": "逗号后应该有空格"
                })
        return issues

    def _check_parentheses_spacing(self, code: str) -> List[Dict[str, Any]]:
        """检查括号间距

        - 括号内不应该有空格
        - 函数调用的括号前不应该有空格
        """
        issues = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            # 检查括号内的空格
            if re.search(r'\(\s+[^\s]', line):
                issues.append({
                    "line": line_num,
                    "message": "括号内不应该有空格"
                })
            # 检查函数调用括号前的空格
            if re.search(r'\w+\s+\(', line):
                issues.append({
                    "line": line_num,
                    "message": "函数调用的括号前不应该有空格"
                })
        return issues

    def _check_comment_spacing(self, code: str) -> List[Dict[str, Any]]:
        """检查注释间距

        - 注释前应该有空格
        - 行内注释应该与代码之间有两个空格
        """
        issues = []
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            # 检查行内注释
            if re.search(r'[^\s]#', line) and not re.search(r'"""|\'\'\'', line):
                issues.append({
                    "line": line_num,
                    "message": "行内注释应该与代码之间有两个空格"
                })
        return issues

    def format_code(self, code: str) -> str:
        """简单的代码格式化

        修复一些常见的格式化问题。
        """
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # 移除行尾空白
            line = line.rstrip()
            
            # 修复操作符间距
            line = re.sub(r'(\S)([=+\-*/!=<>]+)(\S)', r'\1 \2 \3', line)
            
            # 修复逗号间距
            line = re.sub(r',(\S)', r', \1', line)
            
            # 修复括号间距
            line = re.sub(r'(\w+)\s+\(', r'\1(', line)
            line = re.sub(r'\(\s+', r'(', line)
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
