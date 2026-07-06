from typing import List
from ..smolagents_compat import Tool

from .file_tools import (
    read_file,
    write_source_file,
    write_artifact_file,
    list_directory,
    search_files,
    get_project_structure,
)
from .code_tools import analyze_code, check_code_quality
from .test_tools import write_test_file, run_test
from .doc_tools import generate_readme
from .web_tools import scaffold_static_web_app, validate_static_web_app
from .spec_tools import (
    save_requirement_spec,
    save_design_spec,
    save_verification_report,
)


def get_all_tools() -> List[Tool]:
    """获取所有工具"""
    return [
        read_file,
        list_directory,
        search_files,
        analyze_code,
        check_code_quality,
        run_test,
        get_project_structure,
        write_source_file,
        write_artifact_file,
        write_test_file,
        generate_readme,
        scaffold_static_web_app,
        validate_static_web_app,
        save_requirement_spec,
        save_design_spec,
        save_verification_report,
    ]


def get_requirement_tools() -> List[Tool]:
    """需求分析阶段工具"""
    return [
        save_requirement_spec,
        read_file,
        list_directory,
        get_project_structure,
    ]


def get_design_tools() -> List[Tool]:
    """方案设计阶段工具"""
    return [
        save_design_spec,
        read_file,
        list_directory,
        get_project_structure,
        analyze_code,
    ]


def get_implementation_tools() -> List[Tool]:
    """实现阶段工具"""
    return [
        write_source_file,
        write_artifact_file,
        read_file,
        list_directory,
        analyze_code,
        generate_readme,
        scaffold_static_web_app,
    ]


def get_test_tools() -> List[Tool]:
    """测试阶段工具"""
    return [
        write_test_file,
        read_file,
        list_directory,
        analyze_code,
    ]


def get_verification_tools() -> List[Tool]:
    """验证阶段工具"""
    return [
        check_code_quality,
        run_test,
        validate_static_web_app,
        save_verification_report,
        read_file,
        list_directory,
        analyze_code,
    ]
