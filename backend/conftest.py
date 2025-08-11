"""
pytest 配置文件 - 全局测试设置和固件
"""
import pytest
import tempfile
import shutil
from typing import Generator
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models.user import User, UserRole, UserStatus, Team
from app.models.experiment import Experiment
from app.models.share import ExperimentShare, SharePermission
from app.models.comment import ExperimentComment, CommentLike, ExperimentFavorite
from app.services.auth import auth_service


@pytest.fixture(scope="session")
def temp_db() -> Generator[str, None, None]:
    """创建临时测试数据库"""
    # 创建临时数据库文件
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_db_path = temp_file.name
    temp_file.close()
    
    # 创建数据库引擎
    engine = create_engine(f"sqlite:///{temp_db_path}", echo=False)
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    yield temp_db_path
    
    # 清理临时数据库
    Path(temp_db_path).unlink(missing_ok=True)


@pytest.fixture(scope="function")
def db_session(temp_db: str):
    """创建测试数据库会话"""
    engine = create_engine(f"sqlite:///{temp_db}", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_experiment_config():
    """示例实验配置"""
    return {
        "name": "测试实验",
        "description": "这是一个测试实验",
        "config": {
            "data_config": {
                "stock_pool": "CSI300",
                "start_time": "2020-01-01",
                "end_time": "2021-12-31"
            },
            "model_config": {
                "name": "LightGBM",
                "params": {
                    "n_estimators": 100,
                    "learning_rate": 0.1
                }
            },
            "strategy_config": {
                "name": "TopkDropoutStrategy",
                "params": {
                    "topk": 50
                }
            },
            "backtest_config": {
                "trade_cost": 0.0015,
                "benchmark": "CSI300",
                "initial_cash": 1000000
            }
        },
        "tags": ["测试", "示例"]
    }


@pytest.fixture
def sample_experiment_response():
    """示例实验响应数据"""
    return {
        "id": "test-experiment-123",
        "name": "测试实验",
        "description": "这是一个测试实验",
        "status": "completed",
        "progress": 100,
        "results": {
            "performance": {
                "total_return": 0.156,
                "annual_return": 0.078,
                "sharpe_ratio": 1.25,
                "max_drawdown": -0.08,
                "volatility": 0.15
            }
        }
    }


@pytest.fixture
def mock_qlib_data():
    """模拟Qlib数据"""
    return {
        "stock_data": [
            {"symbol": "000001.SZ", "date": "2020-01-01", "price": 10.0},
            {"symbol": "000002.SZ", "date": "2020-01-01", "price": 15.0},
        ],
        "features": ["close", "volume", "open", "high", "low"],
        "predictions": [0.1, -0.05, 0.08, 0.02, -0.12]
    }


# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line("markers", "unit: 单元测试")
    config.addinivalue_line("markers", "integration: 集成测试")
    config.addinivalue_line("markers", "slow: 慢速测试")


# 测试钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 自动为tests/unit/目录下的测试添加unit标记
        if "tests/unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # 自动为tests/integration/目录下的测试添加integration标记
        elif "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# 用户相关 fixtures
@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=auth_service.hash_password("testpassword"),
        role=UserRole.ANALYST,
        status=UserStatus.ACTIVE,
        is_email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session):
    """创建第二个测试用户"""
    user = User(
        username="testuser2",
        email="test2@example.com",
        full_name="Test User 2",
        hashed_password=auth_service.hash_password("testpassword2"),
        role=UserRole.ANALYST,
        status=UserStatus.ACTIVE,
        is_email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session):
    """创建测试管理员用户"""
    user = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=auth_service.hash_password("adminpass"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_team(db_session, test_user):
    """创建测试团队"""
    team = Team(
        name="Test Team",
        description="A test team",
        is_public=True,
        max_members=10,
        owner_id=test_user.id
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


# 实验相关 fixtures
@pytest.fixture
def test_experiment(db_session, test_user):
    """创建测试实验"""
    experiment = Experiment(
        id="test-exp-001",
        name="Test Experiment",
        description="A test experiment",
        creator_id=test_user.id,
        status="completed",
        config={"model": "lgb", "dataset": "csi300"},
        is_deleted=False
    )
    db_session.add(experiment)
    db_session.commit()
    db_session.refresh(experiment)
    return experiment


@pytest.fixture
def test_experiment_with_likes(db_session, test_user, test_user2):
    """创建带点赞的测试实验"""
    from app.models.comment import ExperimentLike
    
    experiment = Experiment(
        id="test-exp-likes",
        name="Popular Experiment",
        description="An experiment with likes",
        creator_id=test_user.id,
        status="completed",
        config={"model": "lgb", "dataset": "csi300"},
        is_deleted=False
    )
    db_session.add(experiment)
    db_session.commit()
    
    # 添加点赞
    like1 = ExperimentLike(experiment_id=experiment.id, user_id=test_user.id)
    like2 = ExperimentLike(experiment_id=experiment.id, user_id=test_user2.id)
    db_session.add_all([like1, like2])
    db_session.commit()
    db_session.refresh(experiment)
    return experiment


@pytest.fixture  
def test_experiment_with_comments(db_session, test_user):
    """创建带评论的测试实验"""
    experiment = Experiment(
        id="test-exp-comments",
        name="Commented Experiment", 
        description="An experiment with comments",
        creator_id=test_user.id,
        status="completed",
        config={"model": "lgb", "dataset": "csi300"},
        is_deleted=False
    )
    db_session.add(experiment)
    db_session.commit()
    
    # 添加评论
    comment = ExperimentComment(
        experiment_id=experiment.id,
        author_id=test_user.id,
        content="Great experiment!",
        content_type="text"
    )
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(experiment)
    return experiment


# 分享相关 fixtures
@pytest.fixture
def test_share(db_session, test_user, test_experiment):
    """创建测试分享"""
    share = ExperimentShare(
        experiment_id=test_experiment.id,
        owner_id=test_user.id,
        title="Test Share",
        description="A test share",
        is_public=True,
        is_active=True,
        permissions=SharePermission.VIEW.value,
        max_views=100,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)
    return share


@pytest.fixture
def test_share_with_experiment(db_session, test_user, test_experiment):
    """创建带实验信息的测试分享"""
    share = ExperimentShare(
        experiment_id=test_experiment.id,
        owner_id=test_user.id,
        title="Test Share with Experiment",
        description="A test share with experiment",
        is_public=True,
        is_active=True,
        permissions=SharePermission.VIEW.value,
        max_views=100,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)
    return share


@pytest.fixture
def test_share_with_password(db_session, test_user, test_experiment):
    """创建带密码的测试分享"""
    from app.services.share import share_service
    
    share = ExperimentShare(
        experiment_id=test_experiment.id,
        owner_id=test_user.id,
        title="Password Protected Share",
        description="A password protected share",
        is_public=True,
        is_active=True,
        permissions=SharePermission.VIEW.value,
        password=share_service._hash_password("testpassword"),
        max_views=100,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)
    return share


@pytest.fixture
def test_expired_share(db_session, test_user, test_experiment):
    """创建已过期的测试分享"""
    share = ExperimentShare(
        experiment_id=test_experiment.id,
        owner_id=test_user.id,
        title="Expired Share",
        description="An expired share",
        is_public=True,
        is_active=True,
        permissions=SharePermission.VIEW.value,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # 已过期
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)
    return share


@pytest.fixture
def test_share_max_views(db_session, test_user, test_experiment):
    """创建已达最大访问次数的测试分享"""
    share = ExperimentShare(
        experiment_id=test_experiment.id,
        owner_id=test_user.id,
        title="Max Views Share",
        description="A share that reached max views",
        is_public=True,
        is_active=True,
        permissions=SharePermission.VIEW.value,
        max_views=5,
        current_views=5,  # 已达最大访问次数
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)
    return share


@pytest.fixture
def test_private_share(db_session, test_user, test_experiment):
    """创建私有分享"""
    share = ExperimentShare(
        experiment_id=test_experiment.id,
        owner_id=test_user.id,
        title="Private Share",
        description="A private share",
        is_public=False,  # 私有分享
        is_active=True,
        permissions=SharePermission.VIEW.value,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)
    return share


# 评论相关 fixtures
@pytest.fixture
def test_comment(db_session, test_user, test_experiment):
    """创建测试评论"""
    comment = ExperimentComment(
        experiment_id=test_experiment.id,
        author_id=test_user.id,
        content="This is a test comment",
        content_type="text",
        is_deleted=False
    )
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)
    return comment


@pytest.fixture
def test_favorite(db_session, test_user, test_experiment):
    """创建测试收藏"""
    favorite = ExperimentFavorite(
        experiment_id=test_experiment.id,
        user_id=test_user.id,
        folder_name="My Favorites",
        notes="A favorite experiment"
    )
    db_session.add(favorite)
    db_session.commit()
    db_session.refresh(favorite)
    return favorite