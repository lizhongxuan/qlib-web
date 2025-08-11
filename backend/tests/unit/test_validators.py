"""
验证器单元测试
"""
import pytest
from datetime import datetime, timedelta
import json

from app.utils.validators import (
    DataValidator,
    SafeDataProcessor,
    ValidationError,
    ErrorHandler
)


class TestDataValidator:
    """数据验证器测试"""

    def test_validate_experiment_config_success(self):
        """测试实验配置验证成功"""
        config = {
            "model_config": {
                "name": "LightGBM",
                "params": {
                    "n_estimators": 100,
                    "learning_rate": 0.1
                }
            },
            "data_config": {
                "stock_pool": "csi300",
                "start_date": "2022-01-01",
                "end_date": "2023-01-01"
            },
            "strategy_config": {
                "name": "TopkDropoutStrategy",
                "params": {
                    "topk": 50
                }
            }
        }
        
        is_valid, errors = DataValidator.validate_experiment_config(config)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_experiment_config_missing_required_fields(self):
        """测试缺少必需字段的配置"""
        config = {
            "model_config": {
                "name": "LightGBM"
            }
            # 缺少 data_config 和 strategy_config
        }
        
        is_valid, errors = DataValidator.validate_experiment_config(config)
        assert is_valid is False
        assert "缺少必需的配置项: data_config" in errors
        assert "缺少必需的配置项: strategy_config" in errors

    def test_validate_model_config_missing_name(self):
        """测试缺少模型名称"""
        errors = DataValidator._validate_model_config({})
        assert "模型配置缺少名称" in errors

    def test_validate_model_config_invalid_params(self):
        """测试无效的模型参数"""
        config = {
            "name": "LightGBM",
            "params": "not a dict"  # 应该是字典
        }
        
        errors = DataValidator._validate_model_config(config)
        assert "模型参数必须是字典类型" in errors

    def test_validate_model_config_null_params(self):
        """测试空参数值"""
        config = {
            "name": "LightGBM",
            "params": {
                "n_estimators": None,
                "learning_rate": 0.1
            }
        }
        
        errors = DataValidator._validate_model_config(config)
        assert "模型参数 n_estimators 不能为空" in errors

    def test_validate_data_config_invalid_dates(self):
        """测试无效日期配置"""
        config = {
            "start_date": "2023-01-01",
            "end_date": "2022-12-31"  # 结束日期早于开始日期
        }
        
        errors = DataValidator._validate_data_config(config)
        assert "开始日期必须早于结束日期" in errors

    def test_validate_data_config_short_period(self):
        """测试时间范围过短"""
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        config = {
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": tomorrow.strftime("%Y-%m-%d")
        }
        
        errors = DataValidator._validate_data_config(config)
        assert "数据时间范围至少需要30天" in errors

    def test_validate_data_config_invalid_date_format(self):
        """测试无效日期格式"""
        config = {
            "start_date": "invalid-date",
            "end_date": "2023-01-01"
        }
        
        errors = DataValidator._validate_data_config(config)
        assert "日期格式无效" in errors

    def test_validate_data_config_invalid_stock_pool(self):
        """测试无效股票池"""
        config = {
            "stock_pool": "invalid_pool"
        }
        
        errors = DataValidator._validate_data_config(config)
        assert "无效的股票池: invalid_pool" in errors

    def test_validate_pagination_params_valid(self):
        """测试有效分页参数"""
        is_valid, error = DataValidator.validate_pagination_params(1, 20)
        assert is_valid is True
        assert error is None

    def test_validate_pagination_params_invalid_page(self):
        """测试无效页码"""
        is_valid, error = DataValidator.validate_pagination_params(0, 20)
        assert is_valid is False
        assert error == "页码必须大于0"

    def test_validate_pagination_params_invalid_page_size(self):
        """测试无效页大小"""
        is_valid, error = DataValidator.validate_pagination_params(1, 101)
        assert is_valid is False
        assert error == "每页大小必须在1-100之间"

    def test_validate_experiment_name_valid(self):
        """测试有效实验名称"""
        is_valid, error = DataValidator.validate_experiment_name("测试实验")
        assert is_valid is True
        assert error is None

    def test_validate_experiment_name_empty(self):
        """测试空实验名称"""
        is_valid, error = DataValidator.validate_experiment_name("")
        assert is_valid is False
        assert error == "实验名称不能为空"

    def test_validate_experiment_name_too_short(self):
        """测试过短的实验名称"""
        is_valid, error = DataValidator.validate_experiment_name("AB")
        assert is_valid is False
        assert error == "实验名称至少需要3个字符"

    def test_validate_experiment_name_too_long(self):
        """测试过长的实验名称"""
        long_name = "A" * 101
        is_valid, error = DataValidator.validate_experiment_name(long_name)
        assert is_valid is False
        assert error == "实验名称不能超过100个字符"

    def test_validate_experiment_name_invalid_chars(self):
        """测试包含无效字符的实验名称"""
        is_valid, error = DataValidator.validate_experiment_name("测试<>实验")
        assert is_valid is False
        assert "实验名称只能包含字母、数字、中文、连字符、下划线和空格" in error

    def test_validate_template_data_valid(self):
        """测试有效模板数据"""
        template_data = {
            "name": "测试模板",
            "config": {
                "model_config": {"name": "LightGBM", "params": {}},
                "data_config": {"stock_pool": "csi300"},
                "strategy_config": {"name": "TopkDropoutStrategy", "params": {}}
            }
        }
        
        is_valid, errors = DataValidator.validate_template_data(template_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_template_data_missing_fields(self):
        """测试缺少必需字段的模板数据"""
        template_data = {}
        
        is_valid, errors = DataValidator.validate_template_data(template_data)
        assert is_valid is False
        assert "缺少必需字段: name" in errors
        assert "缺少必需字段: config" in errors


class TestSafeDataProcessor:
    """安全数据处理器测试"""

    def test_safe_json_loads_valid(self):
        """测试有效JSON解析"""
        json_str = '{"key": "value"}'
        result = SafeDataProcessor.safe_json_loads(json_str)
        assert result == {"key": "value"}

    def test_safe_json_loads_invalid(self):
        """测试无效JSON解析"""
        json_str = "invalid json"
        result = SafeDataProcessor.safe_json_loads(json_str, {"default": "value"})
        assert result == {"default": "value"}

    def test_safe_json_loads_empty(self):
        """测试空JSON字符串"""
        result = SafeDataProcessor.safe_json_loads("", {"default": "value"})
        assert result == {"default": "value"}

    def test_safe_get_valid(self):
        """测试有效字典取值"""
        data = {"key": "value"}
        result = SafeDataProcessor.safe_get(data, "key", "default")
        assert result == "value"

    def test_safe_get_missing_key(self):
        """测试缺少键的字典取值"""
        data = {"other": "value"}
        result = SafeDataProcessor.safe_get(data, "key", "default")
        assert result == "default"

    def test_safe_get_not_dict(self):
        """测试非字典类型的安全取值"""
        data = "not a dict"
        result = SafeDataProcessor.safe_get(data, "key", "default")
        assert result == "default"

    def test_safe_float_conversion_valid(self):
        """测试有效浮点数转换"""
        assert SafeDataProcessor.safe_float_conversion("3.14") == 3.14
        assert SafeDataProcessor.safe_float_conversion(42) == 42.0
        assert SafeDataProcessor.safe_float_conversion(3.14) == 3.14

    def test_safe_float_conversion_invalid(self):
        """测试无效浮点数转换"""
        assert SafeDataProcessor.safe_float_conversion("invalid") == 0.0
        assert SafeDataProcessor.safe_float_conversion(None) == 0.0
        assert SafeDataProcessor.safe_float_conversion("invalid", 1.0) == 1.0

    def test_safe_int_conversion_valid(self):
        """测试有效整数转换"""
        assert SafeDataProcessor.safe_int_conversion("42") == 42
        assert SafeDataProcessor.safe_int_conversion(3.14) == 3
        assert SafeDataProcessor.safe_int_conversion("3.14") == 3

    def test_safe_int_conversion_invalid(self):
        """测试无效整数转换"""
        assert SafeDataProcessor.safe_int_conversion("invalid") == 0
        assert SafeDataProcessor.safe_int_conversion(None) == 0
        assert SafeDataProcessor.safe_int_conversion("invalid", 1) == 1

    def test_sanitize_filename_valid(self):
        """测试有效文件名清理"""
        filename = "test_file.txt"
        result = SafeDataProcessor.sanitize_filename(filename)
        assert result == "test_file.txt"

    def test_sanitize_filename_dangerous_chars(self):
        """测试包含危险字符的文件名"""
        filename = "test<>file|name.txt"
        result = SafeDataProcessor.sanitize_filename(filename)
        assert result == "test__file_name.txt"

    def test_sanitize_filename_empty(self):
        """测试空文件名"""
        result = SafeDataProcessor.sanitize_filename("")
        assert result == "default"

    def test_sanitize_filename_too_long(self):
        """测试过长文件名"""
        filename = "a" * 300
        result = SafeDataProcessor.sanitize_filename(filename)
        assert len(result) == 255

    def test_validate_and_sanitize_search_term_valid(self):
        """测试有效搜索词"""
        result = SafeDataProcessor.validate_and_sanitize_search_term("test search")
        assert result == "test search"

    def test_validate_and_sanitize_search_term_dangerous(self):
        """测试包含危险字符的搜索词"""
        result = SafeDataProcessor.validate_and_sanitize_search_term("test'; DROP TABLE;")
        assert result == "test DROP TABLE"

    def test_validate_and_sanitize_search_term_empty(self):
        """测试空搜索词"""
        result = SafeDataProcessor.validate_and_sanitize_search_term("")
        assert result is None

    def test_validate_and_sanitize_search_term_too_long(self):
        """测试过长搜索词"""
        long_term = "a" * 200
        result = SafeDataProcessor.validate_and_sanitize_search_term(long_term)
        assert len(result) == 100


class TestErrorHandler:
    """错误处理器测试"""

    def test_handle_database_error_duplicate(self):
        """测试重复数据错误"""
        error = Exception("duplicate key value violates unique constraint")
        message, code = ErrorHandler.handle_database_error(error)
        assert message == "数据已存在，请检查重复项"
        assert code == 409

    def test_handle_database_error_foreign_key(self):
        """测试外键约束错误"""
        error = Exception("foreign key constraint fails")
        message, code = ErrorHandler.handle_database_error(error)
        assert message == "关联数据不存在"
        assert code == 400

    def test_handle_database_error_not_null(self):
        """测试非空约束错误"""
        error = Exception("column 'name' cannot be null")
        message, code = ErrorHandler.handle_database_error(error)
        assert message == "必需字段不能为空"
        assert code == 400

    def test_handle_database_error_connection(self):
        """测试连接错误"""
        error = Exception("connection timeout")
        message, code = ErrorHandler.handle_database_error(error)
        assert message == "数据库连接失败"
        assert code == 503

    def test_handle_database_error_generic(self):
        """测试通用数据库错误"""
        error = Exception("some other database error")
        message, code = ErrorHandler.handle_database_error(error)
        assert message == "数据库操作失败"
        assert code == 500

    def test_handle_validation_error_with_field(self):
        """测试带字段的验证错误"""
        error = ValidationError("必须填写", "name")
        message, code = ErrorHandler.handle_validation_error(error)
        assert message == "字段 name 验证失败: 必须填写"
        assert code == 400

    def test_handle_validation_error_without_field(self):
        """测试不带字段的验证错误"""
        error = ValidationError("配置无效")
        message, code = ErrorHandler.handle_validation_error(error)
        assert message == "数据验证失败: 配置无效"
        assert code == 400

    def test_handle_file_error_permission(self):
        """测试文件权限错误"""
        error = Exception("permission denied")
        message, code = ErrorHandler.handle_file_error(error)
        assert message == "文件权限不足"
        assert code == 403

    def test_handle_file_error_not_found(self):
        """测试文件不存在错误"""
        error = Exception("no such file or directory")
        message, code = ErrorHandler.handle_file_error(error)
        assert message == "文件不存在"
        assert code == 404

    def test_handle_file_error_disk_space(self):
        """测试磁盘空间不足错误"""
        error = Exception("no space left on device")
        message, code = ErrorHandler.handle_file_error(error)
        assert message == "磁盘空间不足"
        assert code == 507

    def test_handle_file_error_generic(self):
        """测试通用文件错误"""
        error = Exception("some file error")
        message, code = ErrorHandler.handle_file_error(error)
        assert message == "文件操作失败"
        assert code == 500


class TestValidationError:
    """验证错误异常测试"""

    def test_validation_error_with_field(self):
        """测试带字段的验证错误"""
        error = ValidationError("必须填写", "name")
        assert error.message == "必须填写"
        assert error.field == "name"
        assert str(error) == "必须填写"

    def test_validation_error_without_field(self):
        """测试不带字段的验证错误"""
        error = ValidationError("配置无效")
        assert error.message == "配置无效"
        assert error.field is None
        assert str(error) == "配置无效"