# ===================== 原有导入 =====================
from typing import Dict, Any, Optional, Type
import traceback
import re

from .utils import AgentError, AgentParsingError, AgentExecutionError, AgentMaxStepsError, AgentToolCallError, AgentToolExecutionError, AgentGenerationError
from .memory import AgentLogger

# ===================== 新增导入 =====================
# 错误处理增强模块的核心组件
from error_handling.error_diagnosis import ErrorDiagnoser
from error_handling.error_recovery import ErrorRecoveryManager
from error_handling.error_formatting import ErrorFormatter
from error_handling.exception_standardizer import ExceptionStandardizer, StandardizedException


class ErrorHandlingEnhancer:
    """错误处理增强器

    为 smolagents 提供智能错误诊断、自动错误恢复、友好错误提示和异常标准化功能。
    """

    def __init__(self):
        self.diagnoser = ErrorDiagnoser()
        self.recovery_manager = ErrorRecoveryManager()
        self.formatter = ErrorFormatter()
        self.standardizer = ExceptionStandardizer()

    def enhance_error_handling(self, error: Exception, logger: AgentLogger, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        增强错误处理流程

        Args:
            error: 异常对象
            logger: AgentLogger 实例
            context: 错误发生的上下文信息

        Returns:
            包含错误处理结果的字典
        """
        context = context or {}
        diagnosis = self.diagnoser.diagnose(error)
        formatted_error = self.formatter.format_error(diagnosis)
        recovery_result = self.recovery_manager.recover(error, context)
        formatted_recovery = self.formatter.format_recovery_result(recovery_result)
        standardized_exception = self.standardizer.standardize(error, context)
        logger.log_error(formatted_error)
        if recovery_result["success"]:
            logger.log(f"错误恢复成功: {formatted_recovery}")
        else:
            logger.log(f"错误恢复失败: {formatted_recovery}")

        return {
            "diagnosis": diagnosis,
            "formatted_error": formatted_error,
            "recovery_result": recovery_result,
            "formatted_recovery": formatted_recovery,
            "standardized_exception": standardized_exception
        }

    def handle_agent_error(self, error: AgentError, logger: AgentLogger, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理 AgentError 类型的异常
        """
        return self.enhance_error_handling(error, logger, context)

    def add_recovery_strategy(self, error_type: str, strategy: callable):
        """
        添加自定义恢复策略
        """
        self.recovery_manager.add_recovery_strategy(error_type, strategy)

    def add_error_template(self, error_type: str, template: str):
        """
        添加自定义错误模板
        """
        self.formatter.add_error_template(error_type, template)

    def add_error_code_mapping(self, error_type: str, error_code: str):
        """
        添加自定义错误码映射
        """
        self.standardizer.add_error_code_mapping(error_type, error_code)


error_handling_enhancer = ErrorHandlingEnhancer()


def enhance_error_handling(error: Exception, logger: AgentLogger, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    增强错误处理的便捷函数
    """
    return error_handling_enhancer.enhance_error_handling(error, logger, context)


def handle_agent_error(error: AgentError, logger: AgentLogger, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    处理 AgentError 类型异常的便捷函数
    """
    return error_handling_enhancer.handle_agent_error(error, logger, context)
