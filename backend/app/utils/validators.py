"""
数据验证和错误处理工具
"""
from typing import Any, Dict, List, Optional, Tuple
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """验证错误异常"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)

class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_experiment_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证实验配置"""
        errors = []
        
        # 必须的配置项
        required_fields = ['model_config', 'data_config', 'strategy_config']
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需的配置项: {field}")
        
        # 验证模型配置
        if 'model_config' in config:
            model_errors = DataValidator._validate_model_config(config['model_config'])
            errors.extend(model_errors)
        
        # 验证数据配置
        if 'data_config' in config:
            data_errors = DataValidator._validate_data_config(config['data_config'])
            errors.extend(data_errors)
        
        # 验证策略配置
        if 'strategy_config' in config:
            strategy_errors = DataValidator._validate_strategy_config(config['strategy_config'])
            errors.extend(strategy_errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_model_config(model_config: Dict[str, Any]) -> List[str]:
        """验证模型配置"""
        errors = []
        
        if 'name' not in model_config:
            errors.append("模型配置缺少名称")
        
        if 'params' in model_config:
            params = model_config['params']
            if not isinstance(params, dict):
                errors.append("模型参数必须是字典类型")
            else:
                # 验证参数值
                for key, value in params.items():
                    if value is None:
                        errors.append(f"模型参数 {key} 不能为空")
        
        return errors
    
    @staticmethod
    def _validate_data_config(data_config: Dict[str, Any]) -> List[str]:
        """验证数据配置"""
        errors = []
        
        # 验证时间范围
        if 'start_date' in data_config and 'end_date' in data_config:
            try:
                start_date = datetime.fromisoformat(data_config['start_date'])
                end_date = datetime.fromisoformat(data_config['end_date'])
                
                if start_date >= end_date:
                    errors.append("开始日期必须早于结束日期")
                
                # 检查日期范围是否过短
                if (end_date - start_date).days < 30:
                    errors.append("数据时间范围至少需要30天")
                    
            except (ValueError, TypeError):
                errors.append("日期格式无效")
        
        # 验证股票池
        if 'stock_pool' in data_config:
            stock_pool = data_config['stock_pool']
            valid_pools = ['csi300', 'csi500', 'all_a', 'custom']
            if stock_pool not in valid_pools:
                errors.append(f"无效的股票池: {stock_pool}")
        
        return errors
    
    @staticmethod
    def _validate_strategy_config(strategy_config: Dict[str, Any]) -> List[str]:
        """验证策略配置"""
        errors = []
        
        if 'name' not in strategy_config:
            errors.append("策略配置缺少名称")
        
        if 'params' in strategy_config:
            params = strategy_config['params']
            if not isinstance(params, dict):
                errors.append("策略参数必须是字典类型")
        
        return errors
    
    @staticmethod
    def validate_pagination_params(page: int, page_size: int) -> Tuple[bool, Optional[str]]:
        """验证分页参数"""
        if page < 1:
            return False, "页码必须大于0"
        
        if page_size < 1 or page_size > 100:
            return False, "每页大小必须在1-100之间"
        
        return True, None
    
    @staticmethod
    def validate_experiment_name(name: str) -> Tuple[bool, Optional[str]]:
        """验证实验名称"""
        if not name or not name.strip():
            return False, "实验名称不能为空"
        
        if len(name.strip()) < 3:
            return False, "实验名称至少需要3个字符"
        
        if len(name.strip()) > 100:
            return False, "实验名称不能超过100个字符"
        
        # 检查特殊字符
        if not re.match(r'^[a-zA-Z0-9\u4e00-\u9fa5\-_\s]+$', name.strip()):
            return False, "实验名称只能包含字母、数字、中文、连字符、下划线和空格"
        
        return True, None
    
    @staticmethod
    def validate_template_data(template_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证模板数据"""
        errors = []
        
        # 必需字段
        required_fields = ['name', 'config']
        for field in required_fields:
            if field not in template_data:
                errors.append(f"缺少必需字段: {field}")
        
        # 验证名称
        if 'name' in template_data:
            is_valid, error = DataValidator.validate_experiment_name(template_data['name'])
            if not is_valid:
                errors.append(f"模板名称无效: {error}")
        
        # 验证配置
        if 'config' in template_data:
            is_valid, config_errors = DataValidator.validate_experiment_config(template_data['config'])
            if not is_valid:
                errors.extend([f"模板配置错误: {error}" for error in config_errors])
        
        return len(errors) == 0, errors

class SafeDataProcessor:
    """安全的数据处理器"""
    
    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        """安全的JSON解析"""
        try:
            return json.loads(json_str) if json_str else default
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"JSON解析失败: {e}")
            return default
    
    @staticmethod
    def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """安全的字典取值"""
        try:
            return data.get(key, default) if isinstance(data, dict) else default
        except Exception as e:
            logger.warning(f"获取字典值失败: {e}")
            return default
    
    @staticmethod
    def safe_float_conversion(value: Any, default: float = 0.0) -> float:
        """安全的浮点数转换"""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_int_conversion(value: Any, default: int = 0) -> int:
        """安全的整数转换"""
        try:
            if value is None:
                return default
            return int(float(value))  # 先转float再转int，处理字符串数字
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名，移除危险字符"""
        if not filename:
            return "default"
        
        # 移除危险字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 移除控制字符
        filename = ''.join(c for c in filename if ord(c) >= 32)
        
        # 限制长度
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename or "default"
    
    @staticmethod
    def validate_and_sanitize_search_term(search_term: str) -> Optional[str]:
        """验证并清理搜索词"""
        if not search_term:
            return None
        
        # 移除危险的SQL注入字符
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            search_term = search_term.replace(char, '')
        
        # 限制长度
        search_term = search_term.strip()[:100]
        
        return search_term if search_term else None

class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_database_error(error: Exception) -> Tuple[str, int]:
        """处理数据库错误"""
        error_msg = str(error).lower()
        
        if 'duplicate' in error_msg or 'unique constraint' in error_msg:
            return "数据已存在，请检查重复项", 409
        elif 'foreign key' in error_msg:
            return "关联数据不存在", 400
        elif 'not null' in error_msg:
            return "必需字段不能为空", 400
        elif 'connection' in error_msg:
            return "数据库连接失败", 503
        else:
            logger.error(f"数据库错误: {error}")
            return "数据库操作失败", 500
    
    @staticmethod
    def handle_validation_error(error: ValidationError) -> Tuple[str, int]:
        """处理验证错误"""
        if error.field:
            return f"字段 {error.field} 验证失败: {error.message}", 400
        return f"数据验证失败: {error.message}", 400
    
    @staticmethod
    def handle_file_error(error: Exception) -> Tuple[str, int]:
        """处理文件错误"""
        error_msg = str(error).lower()
        
        if 'permission' in error_msg:
            return "文件权限不足", 403
        elif 'not found' in error_msg or 'no such file' in error_msg:
            return "文件不存在", 404
        elif 'disk space' in error_msg or 'no space' in error_msg:
            return "磁盘空间不足", 507
        else:
            logger.error(f"文件错误: {error}")
            return "文件操作失败", 500

import json