"""
pytest配置和fixtures for集成测试
注意: 这些测试需要真实的IB Gateway/TWS连接，不使用mock
"""
import pytest
from fastapi.testclient import TestClient
import os


# 配置测试环境变量
@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "ib_host": os.getenv("TEST_IB_HOST", "127.0.0.1"),
        "ib_port": int(os.getenv("TEST_IB_PORT", "4002")),  # IB Gateway默认端口
        "test_account": os.getenv("TEST_ACCOUNT", "DU123456"),  # 默认纸交易账号
        "timeout": 30.0,  # API超时时间（秒）
    }


@pytest.fixture(scope="session")
def http_client():
    """
    HTTP客户端fixture - 使用FastAPI的TestClient
    会自动触发lifespan事件
    """
    import random
    from main import app, ib
    
    # Disconnect if already connected to avoid client ID conflicts
    if ib.isConnected():
        ib.disconnect()
    
    # Use a random client ID for tests to avoid conflicts
    original_client_id = None
    from config import settings
    if hasattr(settings, 'ib_client_id'):
        original_client_id = settings.ib_client_id
        settings.ib_client_id = random.randint(100, 999)
    
    try:
        with TestClient(app) as client:
            yield client
    finally:
        # Restore original client ID
        if original_client_id is not None:
            settings.ib_client_id = original_client_id


@pytest.fixture(scope="session")
def wait_for_api_ready(http_client):
    """
    验证FastAPI应用已就绪
    检查IB连接是否成功
    """
    try:
        # 尝试访问docs端点确认应用正常
        response = http_client.get("/docs")
        if response.status_code == 200:
            print("\n✓ API应用已就绪")
            
            # 尝试访问管理账户，检查IB连接
            accounts_response = http_client.get("/api/v1/account/managed-accounts")
            if accounts_response.status_code == 200:
                print("✓ IB连接成功")
                data = accounts_response.json()
                print(f"  找到 {data.get('count', 0)} 个账户")
            else:
                print(f"⚠ IB连接可能失败: {accounts_response.status_code}")
                print(f"  响应: {accounts_response.text}")
                print("  请确保IB Gateway/TWS正在运行")
            
            return True
    except Exception as e:
        print(f"\n✗ API应用初始化失败: {e}")
        raise
    
    return True


# 通用测试数据
@pytest.fixture
def sample_stock_contract():
    """示例股票合约"""
    return {
        "symbol": "AAPL",
        "sec_type": "STK",
        "exchange": "SMART",
        "currency": "USD"
    }


@pytest.fixture
def sample_forex_contract():
    """示例外汇合约"""
    return {
        "symbol": "EURUSD",
        "sec_type": "CASH",
        "exchange": "IDEALPRO",
        "currency": "USD"
    }


@pytest.fixture
def sample_option_contract():
    """示例期权合约"""
    return {
        "symbol": "AAPL",
        "sec_type": "OPT",
        "exchange": "SMART",
        "currency": "USD",
        "last_trade_date": "20250117",
        "strike": 150.0,
        "right": "C"
    }
