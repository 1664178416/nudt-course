import subprocess
from ..smolagents_compat import tool
from .base import resolve_read_path, require_run_dir, resolve_tests_write_path

@tool
def write_test_file(file_path: str, content: str) -> str:
    """
    将内容写入测试文件，默认写入当前任务的 tests/ 目录。

    Args:
        file_path: 要写入的文件路径（相对路径会写入 tests/）
        content: 要写入的文件内容
    """
    try:
        path = resolve_tests_write_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"✅ 测试文件已成功写入: {path} (共 {len(content)} 字符)"
    except Exception as e:
        return f"❌ 写入测试文件失败: {str(e)}"


@tool
def run_test(test_file: str) -> str:
    """
    运行Python测试文件。支持pytest和unittest。返回测试结果。

    Args:
        test_file: 测试文件路径或测试目录
    """
    try:
        path = resolve_read_path(test_file)
        if not path.exists():
            return f"❌ 测试文件不存在: {test_file}"

        try:
            result = subprocess.run(
                ["pytest", str(path), "-v"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(require_run_dir()),
            )
            return f"测试结果：\n{result.stdout}\n{result.stderr}"
        except FileNotFoundError:
            result = subprocess.run(
                ["python", "-m", "unittest", str(path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(require_run_dir()),
            )
            return f"测试结果：\n{result.stdout}\n{result.stderr}"
    except Exception as e:
        return f"❌ 运行测试失败: {str(e)}"
