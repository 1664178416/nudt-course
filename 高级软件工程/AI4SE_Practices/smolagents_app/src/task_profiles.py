"""
任务画像：根据用户目标推断交付物类型，并生成执行契约。
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re
from typing import List, Optional


WEB_MARKERS = {
    "网页",
    "前端",
    "html",
    "css",
    "javascript",
    "页面",
    "landing page",
    "web page",
    "web app",
    "网站",
}

API_MARKERS = {"api", "接口", "后端", "服务", "flask", "fastapi", "django"}

ALGORITHM_HINTS = [
    "冒泡排序",
    "选择排序",
    "插入排序",
    "归并排序",
    "快速排序",
    "堆排序",
    "二分查找",
    "深度优先搜索",
    "广度优先搜索",
    "动态规划",
    "bubble sort",
    "quick sort",
    "merge sort",
    "binary search",
    "dfs",
    "bfs",
]


@dataclass
class TaskProfile:
    artifact_type: str
    primary_output_dir: str
    expected_entrypoint: str
    testing_strategy: str
    ui_focus: bool = False
    recommended_features: Optional[List[str]] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def infer_artifact_type(goal: str) -> str:
    goal_lower = goal.lower()
    if any(marker in goal_lower for marker in WEB_MARKERS):
        return "static_web_app"
    if any(marker in goal_lower for marker in API_MARKERS):
        return "api_service"
    return "python_application"


def extract_feature_hints(goal: str) -> List[str]:
    matches = [item for item in ALGORITHM_HINTS if item.lower() in goal.lower()]
    if matches:
        return matches
    if "算法" in goal:
        return ["冒泡排序", "快速排序", "二分查找", "图搜索"]
    return []


def build_task_profile(goal: str) -> TaskProfile:
    artifact_type = infer_artifact_type(goal)
    features = extract_feature_hints(goal)

    if artifact_type == "static_web_app":
        return TaskProfile(
            artifact_type=artifact_type,
            primary_output_dir="artifacts/web",
            expected_entrypoint="artifacts/web/index.html",
            testing_strategy="为静态网页生成至少一个 smoke test，并执行静态资源校验",
            ui_focus=True,
            recommended_features=features,
        )

    if artifact_type == "api_service":
        return TaskProfile(
            artifact_type=artifact_type,
            primary_output_dir="src",
            expected_entrypoint="src/main.py",
            testing_strategy="生成接口级测试并执行基础回归测试",
            recommended_features=features,
        )

    return TaskProfile(
        artifact_type=artifact_type,
        primary_output_dir="src",
        expected_entrypoint="src/main.py",
        testing_strategy="生成单元测试并执行基础回归测试",
        recommended_features=features,
    )


def build_execution_brief(goal: str, run_dir: Optional[Path] = None) -> str:
    profile = build_task_profile(goal)
    lines = [
        "",
        "[Execution Contract]",
        f"- artifact_type: {profile.artifact_type}",
        f"- primary_output_dir: {profile.primary_output_dir}",
        f"- expected_entrypoint: {profile.expected_entrypoint}",
        f"- testing_strategy: {profile.testing_strategy}",
        "- 所有文件必须写入当前任务运行目录，不得写到仓库其他位置。",
    ]
    if run_dir is not None:
        lines.append(f"- current_run_dir: {run_dir.as_posix()}")
    if profile.ui_focus:
        lines.extend(
            [
                "- 本任务强调前端观感，页面需要具备清晰的信息层级、视觉节奏和移动端可用性。",
                "- 如果要生成静态网页，请优先保证 index.html、styles.css、app.js 结构完整且资源引用正确。",
            ]
        )
    if profile.recommended_features:
        lines.append(f"- recommended_features: {', '.join(profile.recommended_features)}")
    return goal.strip() + "\n" + "\n".join(lines)


def save_task_profile(task_goal: str, run_dir: Path) -> Path:
    profile = build_task_profile(task_goal)
    profile_path = run_dir / "input" / "task_profile.json"
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(profile.to_json(), encoding="utf-8")
    return profile_path
