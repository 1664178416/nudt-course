from pathlib import Path
import os
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.execution_mode import should_use_fast_path


def test_should_use_fast_path_default_for_static_web(monkeypatch):
    monkeypatch.delenv("SMOLAGENTS_FAST_MODE", raising=False)
    monkeypatch.delenv("SMOLAGENTS_FORCE_FULL_FLOW", raising=False)
    assert should_use_fast_path("做一个好看的前端网页，展示各种算法，放到 /output目录下")


def test_should_not_use_fast_path_when_force_full(monkeypatch):
    monkeypatch.setenv("SMOLAGENTS_FORCE_FULL_FLOW", "1")
    assert not should_use_fast_path("Build a beautiful front-end web page")
