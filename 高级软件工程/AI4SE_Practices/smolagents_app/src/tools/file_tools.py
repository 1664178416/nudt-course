from pathlib import Path
from typing import Optional
from ..smolagents_compat import tool
from .base import (
    resolve_read_path,
    resolve_dir_path,
    resolve_source_write_path,
    resolve_artifact_write_path,
)


def _write_text(path: Path, content: str, label: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ {label}已成功写入: {path} (共 {len(content)} 字符)"

@tool
def read_file(file_path: str) -> str:
    """
    读取指定文件的内容。输入文件路径，返回文件内容。支持文本文件、代码文件等。

    Args:
        file_path: 要读取的文件路径
    """
    try:
        path = resolve_read_path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取文件失败: {str(e)}"


@tool
def write_source_file(file_path: str, content: str) -> str:
    """
    将内容写入源码文件，默认写入当前任务的 src/ 目录。

    Args:
        file_path: 要写入的文件路径（相对路径会写入 src/）
        content: 要写入的文件内容
    """
    try:
        path = resolve_source_write_path(file_path)
        return _write_text(path, content, "源码文件")
    except Exception as e:
        return f"❌ 写入文件失败: {str(e)}"


@tool
def write_artifact_file(file_path: str, content: str) -> str:
    """
    将内容写入交付物文件，默认写入当前任务的 artifacts/ 目录。
    适用于 HTML/CSS/JS、JSON、Markdown、静态资源说明等非源码产物。

    Args:
        file_path: 要写入的文件路径（相对路径会写入 artifacts/）
        content: 要写入的文件内容
    """
    try:
        path = resolve_artifact_write_path(file_path)
        return _write_text(path, content, "交付物文件")
    except Exception as e:
        return f"❌ 写入文件失败: {str(e)}"


@tool
def list_directory(dir_path: str) -> str:
    """
    列出指定目录下的文件和子目录。返回格式化的文件列表，包括文件类型信息。

    Args:
        dir_path: 要列出的目录路径
    """
    try:
        path = resolve_dir_path(dir_path)
        if not path.exists():
            return f"❌ 目录不存在: {dir_path}"
        items = []
        for item in sorted(path.iterdir()):
            item_type = "📁 目录" if item.is_dir() else "📄 文件"
            size = f" ({item.stat().st_size} bytes)" if item.is_file() else ""
            items.append(f"{item_type}: {item.name}{size}")
        return "\n".join(items) if items else "目录为空"
    except Exception as e:
        return f"❌ 列出目录失败: {str(e)}"


@tool
def search_files(dir_path: str, keyword: str, search_in_content: bool = False) -> str:
    """
    在指定目录中搜索包含特定关键词的文件。支持按文件名或内容搜索。

    Args:
        dir_path: 要搜索的目录路径
        keyword: 搜索关键词
        search_in_content: 是否在文件内容中搜索（默认False，只搜索文件名）
    """
    try:
        path = resolve_dir_path(dir_path)
        if not path.exists():
            return f"❌ 目录不存在: {dir_path}"

        results = []
        for item in path.rglob("*"):
            if item.is_file():
                if keyword.lower() in item.name.lower():
                    results.append(f"📄 {item}")
                elif search_in_content:
                    try:
                        with open(item, "r", encoding="utf-8") as f:
                            if keyword in f.read():
                                results.append(f"📄 {item} (内容匹配)")
                    except Exception:
                        pass

        if results:
            return f"找到 {len(results)} 个匹配文件：\n" + "\n".join(results)
        return f"未找到包含 '{keyword}' 的文件"
    except Exception as e:
        return f"❌ 搜索失败: {str(e)}"


@tool
def get_project_structure(root_path: Optional[str] = None, max_depth: int = 3) -> str:
    """
    获取项目的目录结构，以树形格式返回。可以指定根目录和最大深度。

    Args:
        root_path: 项目根目录路径（默认：当前目录）
        max_depth: 最大深度（默认：3）
    """
    try:
        root = resolve_dir_path(root_path)
        if not root.exists():
            return f"❌ 目录不存在: {root_path}"

        def tree(path: Path, prefix: str = "", depth: int = 0) -> str:
            if depth > max_depth:
                return ""

            result = []
            try:
                items = sorted([item for item in path.iterdir() if not item.name.startswith(".")])
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    result.append(f"{prefix}{current_prefix}{item.name}")

                    if item.is_dir():
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        result.append(tree(item, next_prefix, depth + 1))
            except PermissionError:
                pass

            return "\n".join(result)

        structure = f"{root.name}/\n" + tree(root)
        return structure
    except Exception as e:
        return f"❌ 获取项目结构失败: {str(e)}"
