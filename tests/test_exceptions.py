"""
异常模块测试
"""
import pytest

from src.exceptions import (
    PromptProError,
    ConfigError,
    ConnectionError,
    ModelError,
    OptimizerError,
    HistoryError,
    ClipboardError,
    ErrorCode,
)


class TestErrorCodes:
    """错误码测试"""

    def test_error_codes_exist(self):
        """测试错误码存在"""
        assert ErrorCode.CONFIG_LOAD_FAILED == 101
        assert ErrorCode.CONNECTION_FAILED == 201
        assert ErrorCode.MODEL_NOT_FOUND == 301
        assert ErrorCode.OPTIMIZER_FAILED == 401
        assert ErrorCode.UNKNOWN_ERROR == 999


class TestPromptProError:
    """PromptProError 基类测试"""

    def test_basic_error(self):
        """测试基本错误"""
        error = PromptProError("测试错误")
        assert str(error) == "[999] 测试错误"
        assert error.message == "测试错误"
        assert error.error_code == ErrorCode.UNKNOWN_ERROR

    def test_error_with_code(self):
        """测试带错误码的错误"""
        error = PromptProError("测试错误", error_code=ErrorCode.CONFIG_LOAD_FAILED)
        assert error.error_code == ErrorCode.CONFIG_LOAD_FAILED
        assert "[101]" in str(error)

    def test_error_with_details(self):
        """测试带详情的错误"""
        error = PromptProError("测试错误", details="详细信息")
        assert "详细信息" in str(error)


class TestSpecificErrors:
    """特定错误类型测试"""

    def test_config_error(self):
        """测试配置错误"""
        error = ConfigError("配置加载失败")
        assert error.error_code == ErrorCode.CONFIG_LOAD_FAILED

    def test_connection_error(self):
        """测试连接错误"""
        error = ConnectionError("连接失败")
        assert error.error_code == ErrorCode.CONNECTION_FAILED

    def test_model_error(self):
        """测试模型错误"""
        error = ModelError("模型不存在")
        assert error.error_code == ErrorCode.MODEL_NOT_FOUND

    def test_optimizer_error(self):
        """测试优化错误"""
        error = OptimizerError("优化失败")
        assert error.error_code == ErrorCode.OPTIMIZER_FAILED

    def test_history_error(self):
        """测试历史记录错误"""
        error = HistoryError("历史加载失败")
        assert error.error_code == ErrorCode.HISTORY_LOAD_FAILED

    def test_clipboard_error(self):
        """测试剪贴板错误"""
        error = ClipboardError("复制失败")
        assert error.error_code == ErrorCode.CLIPBOARD_COPY_FAILED