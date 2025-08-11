"""
简化的测试配置文件，避免复杂依赖
"""
import pytest
from unittest.mock import Mock, MagicMock
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def db_session():
    """模拟数据库会话"""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_settings():
    """模拟设置"""
    settings = Mock()
    settings.DATABASE_URL = "sqlite:///test.db"
    settings.SECRET_KEY = "test-secret-key"
    settings.BACKUP_PATH = "/tmp/backups"
    settings.EXPERIMENTS_PATH = "/tmp/experiments"
    settings.LOG_LEVEL = "INFO"
    return settings


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = Mock()
    user.id = "user-123"
    user.username = "testuser"
    user.email = "test@example.com"
    user.is_active = True
    user.role = "ANALYST"
    return user


@pytest.fixture
def mock_experiment():
    """创建模拟实验"""
    experiment = Mock()
    experiment.id = "exp-123"
    experiment.name = "测试实验"
    experiment.status = "completed"
    experiment.config = {"test": "config"}
    experiment.results = {"test": "results"}
    experiment.user_id = "user-123"
    return experiment