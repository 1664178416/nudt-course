"""
工具函数：结果保存、格式化等
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from .runtime.run_context import get_current_run_dir, ensure_run_structure, create_run_dir


def collect_generated_files(task_dir: Path) -> list[str]:
    """收集任务目录下的关键输出文件列表。"""
    results: list[str] = []
    for folder in ["input", "design", "src", "artifacts", "tests", "docs", "logs"]:
        current = task_dir / folder
        if not current.exists():
            continue
        for path in sorted(p for p in current.rglob("*") if p.is_file()):
            results.append(str(path.relative_to(task_dir)))
    return results


def save_results_to_output(
    requirement_spec: Optional[str] = None,
    design_spec: Optional[str] = None,
    implementation: Optional[Dict[str, Any]] = None,
    verification_report: Optional[str] = None,
    task_goal: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    保存所有结果到 output/ 目录
    
    Returns:
        保存的文件路径字典
    """
    current_run_dir = get_current_run_dir()
    if current_run_dir is not None:
        task_dir = ensure_run_structure(current_run_dir)
    else:
        # 若未设置 run_dir，则新建任务目录，确保输出仍在 output/<timestamp>/ 下
        task_dir = create_run_dir(Path(output_dir) if output_dir else None)
    
    saved_files = {}
    
    # 保存任务目标
    if task_goal:
        goal_file = task_dir / "input" / "task.txt"
        with open(goal_file, 'w', encoding='utf-8') as f:
            f.write(task_goal)
        saved_files["task_goal"] = str(goal_file)
    
    # 保存需求规格（放入 input）
    if requirement_spec:
        req_file = task_dir / "input" / "requirement.json"
        with open(req_file, 'w', encoding='utf-8') as f:
            if isinstance(requirement_spec, str):
                f.write(requirement_spec)
            else:
                json.dump(requirement_spec, f, ensure_ascii=False, indent=2)
        saved_files["requirement_spec"] = str(req_file)
    
    # 保存设计方案
    if design_spec:
        design_file = task_dir / "design" / "design.json"
        with open(design_file, 'w', encoding='utf-8') as f:
            if isinstance(design_spec, str):
                f.write(design_spec)
            else:
                json.dump(design_spec, f, ensure_ascii=False, indent=2)
        saved_files["design_spec"] = str(design_file)
    
    # 保存实现结果
    if implementation:
        impl_file = task_dir / "logs" / "implementation_output.txt"
        with open(impl_file, 'w', encoding='utf-8') as f:
            if isinstance(implementation, dict):
                f.write(implementation.get("output", str(implementation)))
            else:
                f.write(str(implementation))
        saved_files["implementation"] = str(impl_file)
        
        # 如果实现中包含生成的文件列表，也保存
        if isinstance(implementation, dict) and "files" in implementation:
            files_info = task_dir / "logs" / "generated_files.json"
            with open(files_info, 'w', encoding='utf-8') as f:
                json.dump(implementation["files"], f, ensure_ascii=False, indent=2)
            saved_files["generated_files"] = str(files_info)
    
    # 保存验证报告（放入 logs）
    if verification_report:
        verify_file = task_dir / "logs" / "verification.json"
        with open(verify_file, 'w', encoding='utf-8') as f:
            if isinstance(verification_report, str):
                f.write(verification_report)
            else:
                json.dump(verification_report, f, ensure_ascii=False, indent=2)
        saved_files["verification_report"] = str(verify_file)
    
    # 生成总结报告
    summary_file = task_dir / "logs" / "summary.md"
    generated_files = collect_generated_files(task_dir)
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# 任务执行总结\n\n")
        f.write(f"**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if task_goal:
            f.write(f"**任务目标**: {task_goal}\n\n")
        f.write(f"## 生成的文件\n\n")
        for key, path in saved_files.items():
            f.write(f"- `{key}`: `{path}`\n")
        f.write(f"\n## 执行状态\n\n")
        if verification_report:
            try:
                if isinstance(verification_report, str):
                    verify_data = json.loads(verification_report)
                else:
                    verify_data = verification_report
                status = "✅ 通过" if verify_data.get("passed", False) else "❌ 未通过"
                f.write(f"**验证状态**: {status}\n\n")
            except:
                pass
        if generated_files:
            f.write("## 目录内已生成文件\n\n")
            for path in generated_files:
                f.write(f"- `{path}`\n")
    saved_files["summary"] = str(summary_file)
    
    return saved_files


def extract_code_from_output(output: str) -> Dict[str, str]:
    """
    从智能体输出中提取代码块
    
    Returns:
        文件名到代码内容的字典
    """
    import re
    
    code_blocks = {}
    
    # 匹配代码块：```python 或 ``` 开头的代码块
    pattern = r'```(?:python|py)?\n(.*?)```'
    matches = re.findall(pattern, output, re.DOTALL)
    
    for i, code in enumerate(matches):
        # 尝试从代码中提取文件名
        file_match = re.search(r'(?:file|path|filename)[\s:=]+["\']([^"\']+)["\']', code, re.IGNORECASE)
        if file_match:
            filename = file_match.group(1)
        else:
            filename = f"generated_code_{i+1}.py"
        
        code_blocks[filename] = code.strip()
    
    return code_blocks


def format_agent_output(output: str) -> str:
    """格式化智能体输出，使其更易读"""
    # 这里可以添加更多的格式化逻辑
    return output

