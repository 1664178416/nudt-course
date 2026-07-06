from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.task_profiles import build_execution_brief, build_task_profile


def test_build_task_profile_for_static_web_goal():
    profile = build_task_profile("做一个好看的前端网页，展示各种算法，放到 /output目录下")

    assert profile.artifact_type == "static_web_app"
    assert profile.primary_output_dir == "artifacts/web"
    assert profile.expected_entrypoint.endswith("index.html")
    assert profile.ui_focus is True
    assert profile.recommended_features


def test_execution_brief_contains_contract_and_output():
    brief = build_execution_brief(
        "做一个好看的前端网页，展示各种算法，放到 /output目录下",
        Path("output/demo-run"),
    )

    assert "[Execution Contract]" in brief
    assert "artifact_type: static_web_app" in brief
    assert "expected_entrypoint: artifacts/web/index.html" in brief
    assert "current_run_dir: output/demo-run" in brief
