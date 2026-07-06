from pathlib import Path
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.fallback_runner import run_fallback_static_web_task
from src.runtime.run_context import create_run_dir, run_context


def test_fallback_runner_generates_web_artifacts():
    with tempfile.TemporaryDirectory() as temp_dir:
        run_dir = create_run_dir(Path(temp_dir), "fallback-demo")
        with run_context(run_dir):
            result = run_fallback_static_web_task(
                "Build a beautiful front-end web page that showcases classic algorithms and save it under /output.",
                run_dir,
            )

        entrypoint = Path(result["bundle"]["entrypoint"])
        assert result["mode"] == "fallback_static_web"
        assert result["verification_report"]["passed"] is True
        assert entrypoint.exists()
        assert (run_dir / "input" / "task_profile.json").exists()
        assert (run_dir / "logs" / "summary.md").exists()
