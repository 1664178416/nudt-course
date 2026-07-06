# ===================== 原有导入 =====================
from pathlib import Path
from src.tools.base import get_current_run_dir, _ensure_within_run_dir

# ===================== 新增导入 =====================
import black  # 用于代码格式化的核心库

# ===================== 原有函数（如write_code_file） =====================
def write_code_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """
    将代码内容写入指定文件
    :param file_path: 相对运行目录的文件路径
    :param content: 代码内容
    :param overwrite: 是否覆盖已有文件
    :return: 操作结果提示
    """
    run_dir = get_current_run_dir()
    abs_path = _ensure_within_run_dir(Path(file_path), run_dir)
    
    if abs_path.exists() and not overwrite:
        return f"文件 {file_path} 已存在，未覆盖"
    
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return f"成功写入文件: {file_path}"


# ===================== 新增格式化函数 =====================
def format_python_code(file_path: str) -> str:
    """
    格式化Python代码文件，遵循black规范（贴合项目"增强代码质量检查"的迭代计划）
    :param file_path: 代码文件相对路径（基于当前任务运行目录，避免路径越权）
    :return: 格式化结果提示（成功/失败原因，便于智能体识别结果）
    """
    # 复用项目现有工具函数
    run_dir = get_current_run_dir()
    abs_path = _ensure_within_run_dir(Path(file_path), run_dir)
    
    # 校验文件类型，仅处理.py文件
    if not abs_path.suffix == ".py":
        return f"❌ 格式化失败：仅支持Python文件（.py），当前文件类型为 {abs_path.suffix}"
    
    # 读取文件内容（处理编码和文件不存在的情况）
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            original_code = f.read()
    except FileNotFoundError:
        return f"❌ 格式化失败：文件 {file_path} 不存在"
    except UnicodeDecodeError:
        return f"❌ 格式化失败：文件 {file_path} 编码不是UTF-8，无法读取"
    
    # 使用black格式化代码（贴合项目代码风格，行长度设为120）
    try:
        formatted_code = black.format_file_contents(
            original_code,
            fast=False,  # 不跳过语法检查，保证格式化后的代码可运行
            mode=black.FileMode(line_length=120)  # 行长度适配项目代码风格
        )
    except black.InvalidInput:
        return f"❌ 格式化失败：文件 {file_path} 包含无效的Python语法，无法格式化"
    except Exception as e:
        return f"❌ 格式化失败：未知错误 - {str(e)}"
    
    # 写入格式化后的代码
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(formatted_code)
        return f"✅ 格式化成功：文件 {file_path} 已按black规范格式化完成"
    except Exception as e:
        return f"❌ 写入失败：无法保存格式化后的文件 - {str(e)}"