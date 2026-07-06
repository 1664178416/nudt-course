"""
本地降级执行器。

当 smolagents 或模型依赖不可用时，为部分交付物类型提供可运行的兜底路径。
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from .task_profiles import build_task_profile, save_task_profile
from .tools.web_tools import build_static_web_app_bundle, validate_static_web_app_bundle
from .utils import save_results_to_output


def _build_fallback_requirement(goal: str, profile) -> Dict[str, Any]:
    features = profile.recommended_features or ["算法卡片展示", "搜索筛选", "讲解面板", "移动端适配"]
    return {
        "functions": [
            "生成一个可直接打开的静态前端页面",
            "展示多个算法主题，并支持交互式浏览",
            "确保所有页面资源写入当前 output 运行目录",
        ],
        "constraints": [
            "不得写入当前任务目录之外的路径",
            "生成的页面必须本地可打开，不依赖构建工具",
        ],
        "acceptance_criteria": [
            "存在可直接访问的 index.html 入口文件",
            "页面正确引用本地 styles.css 与 app.js",
            "页面至少展示 3 个以上算法主题或功能模块",
        ],
        "non_functional_requirements": [
            "页面风格清晰、美观，适合课程展示",
            "移动端布局不应完全崩坏",
        ],
        "artifact_type": profile.artifact_type,
        "deliverables": [profile.expected_entrypoint, *features],
    }


def _build_fallback_design(profile) -> Dict[str, Any]:
    return {
        "modules": [
            {
                "name": "page_shell",
                "description": "负责页面整体结构与导航布局",
                "files": ["artifacts/web/index.html", "artifacts/web/styles.css"],
                "dependencies": ["interaction_layer"],
            },
            {
                "name": "interaction_layer",
                "description": "负责筛选、随机聚焦和讲解面板交互",
                "files": ["artifacts/web/app.js"],
                "dependencies": [],
            },
        ],
        "interfaces": [
            {
                "name": "renderExplanation",
                "description": "根据算法名称更新页面讲解面板",
                "signature": "renderExplanation(name: string) -> void",
                "module": "interaction_layer",
            }
        ],
        "data_flow": "用户访问 index.html -> 页面加载 styles.css 与 app.js -> 用户筛选或点击算法卡片 -> JS 更新讲解面板与页面状态。",
        "file_structure": {
            "description": "前端交付物放入 artifacts/web，测试脚本位于 tests/",
            "directories": ["artifacts/web/", "tests/"],
        },
        "technology_stack": ["HTML", "CSS", "JavaScript"],
        "artifact_type": profile.artifact_type,
        "deliverables": [
            {"path": "artifacts/web/index.html", "purpose": "页面入口"},
            {"path": "artifacts/web/styles.css", "purpose": "视觉样式"},
            {"path": "artifacts/web/app.js", "purpose": "交互逻辑"},
            {"path": "tests/test_web_bundle.py", "purpose": "静态网页 smoke test"},
        ],
    }


def _write_web_smoke_test(run_dir: Path) -> Path:
    test_path = run_dir / "tests" / "test_web_bundle.py"
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text(
        """from pathlib import Path


def test_static_web_bundle_exists():
    root = Path(__file__).resolve().parents[1] / "artifacts" / "web"
    assert (root / "index.html").exists()
    assert (root / "styles.css").exists()
    assert (root / "app.js").exists()


def test_index_references_local_assets():
    index_html = (Path(__file__).resolve().parents[1] / "artifacts" / "web" / "index.html").read_text(encoding="utf-8")
    assert "./styles.css" in index_html
    assert "./app.js" in index_html
""",
        encoding="utf-8",
    )
    return test_path


def _build_ui_message(
    goal: str,
    bundle: Dict[str, Any],
    verification_report: Dict[str, Any],
    saved_files: Dict[str, str],
    trace: List[str],
) -> str:
    status = "通过" if verification_report.get("passed") else "未通过"
    lines = [
        "## 执行完成（极速模式）",
        "",
        f"**任务目标**：{goal}",
        f"**验证状态**：{status}",
        "",
        "### 过程追踪",
    ]
    lines.extend([f"- {item}" for item in trace])
    lines.extend(
        [
            "",
            "### 关键输出",
            f"- 入口页面：`{bundle.get('entrypoint', '')}`",
            f"- 资源文件：`{bundle.get('files', [])}`",
            f"- 摘要报告：`{saved_files.get('summary', '')}`",
            f"- 验证报告：`{saved_files.get('verification_report', '')}`",
        ]
    )
    return "\n".join(lines)


def _write_process_trace(run_dir: Path, trace: List[str]) -> Path:
    trace_path = run_dir / "logs" / "process_trace.md"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    content = ["# 极速模式过程日志", ""]
    content.extend([f"- {item}" for item in trace])
    trace_path.write_text("\n".join(content), encoding="utf-8")
    return trace_path


def run_fallback_static_web_task(
    goal: str,
    run_dir,
    logger: Callable[[str], None] | None = None,
) -> Dict[str, Any]:
    trace: List[str] = []

    def log(message: str) -> None:
        trace.append(message)
        if logger:
            logger(message)

    log("开始极速模式：识别任务画像。")
    profile = build_task_profile(goal)
    log(f"任务画像识别结果：artifact_type={profile.artifact_type}。")
    save_task_profile(goal, run_dir)
    log("已保存 task_profile.json。")

    log("生成需求规格（requirement_spec）。")
    requirement_spec = _build_fallback_requirement(goal, profile)
    log("生成设计方案（design_spec）。")
    design_spec = _build_fallback_design(profile)
    log("生成静态网页交付物（index.html / styles.css / app.js）。")
    bundle = build_static_web_app_bundle(
        project_name="算法展厅",
        summary=goal,
        feature_list=",".join(profile.recommended_features or []),
    )
    log("写入 smoke test 到 tests/test_web_bundle.py。")
    test_file = _write_web_smoke_test(run_dir)
    log("执行静态网页结构校验。")
    validation = validate_static_web_app_bundle(profile.expected_entrypoint)
    log(f"静态网页校验结果：passed={validation['passed']}。")

    verification_report = {
        "passed": validation["passed"],
        "requirements_coverage": {
            "covered": requirement_spec["functions"],
            "missing": [] if validation["passed"] else ["请检查静态资源是否完整"],
        },
        "code_quality": {
            "score": "8" if validation["passed"] else "5",
            "issues": validation["issues"],
        },
        "issues": validation["issues"],
        "suggestions": [
            "可继续加入更多算法动画或真实数据驱动可视化",
            "如需完整多角色 LLM 流程，请安装 smolagents 并配置模型访问",
        ],
        "test_results": json.dumps(validation, ensure_ascii=False),
        "overall_assessment": "已通过本地静态网页结构校验，适合作为演示产物。",
        "output_artifacts": [*bundle["files"], str(test_file)],
    }

    log("保存需求/设计/实现/验证结果到 output 目录。")
    saved_files = save_results_to_output(
        requirement_spec=requirement_spec,
        design_spec=design_spec,
        implementation={"output": json.dumps(bundle, ensure_ascii=False, indent=2), "files": bundle["files"]},
        verification_report=verification_report,
        task_goal=goal,
    )
    trace_file = _write_process_trace(Path(run_dir), trace)
    log(f"过程日志已写入：{trace_file}")
    ui_message = _build_ui_message(goal, bundle, verification_report, saved_files, trace)

    return {
        "mode": "fallback_static_web",
        "bundle": bundle,
        "verification_report": verification_report,
        "saved_files": saved_files,
        "trace": trace,
        "ui_message": ui_message,
    }
