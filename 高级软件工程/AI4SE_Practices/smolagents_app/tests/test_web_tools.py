from pathlib import Path
import sys
import tempfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.runtime.run_context import create_run_dir, run_context
from src.tools.web_tools import build_static_web_app_bundle, validate_static_web_app_bundle


def test_build_and_validate_static_web_bundle():
    with tempfile.TemporaryDirectory() as temp_dir:
        run_dir = create_run_dir(Path(temp_dir), "web-demo")

        with run_context(run_dir):
            bundle = build_static_web_app_bundle(
                project_name="算法展厅",
                summary="一个用于展示经典算法的静态网页。",
                feature_list="冒泡排序,快速排序,二分查找",
            )
            report = validate_static_web_app_bundle("artifacts/web/index.html")

        assert bundle["entrypoint"].endswith("index.html")
        assert Path(bundle["entrypoint"]).exists()
        assert report["passed"] is True
        assert not report["issues"]
