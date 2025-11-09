# IBKR API Service

完整的 FastAPI 封装的 Interactive Brokers API 服务，使用 `ib_async` 库。

## 🎯 特色：真实集成测试

本项目包含**完整的集成测试**，使用真实的 IB Gateway/TWS 连接测试所有功能！

```bash
# 启动 IB Gateway/TWS (纸交易账户)
# 然后运行集成测试
./test_integration.sh
```

查看真实的市场数据、账户信息、订单状态等！
📖 [集成测试快速指南](INTEGRATION_TESTS.md)

---

## 功能特性

### 1. 账户管理 (`/api/v1/account`)
- ✅ 获取管理账户列表
- ✅ 账户摘要信息
- ✅ 详细账户数值
- ✅ 持仓信息
- ✅ 投资组合详情（含盈亏）
- ✅ 实时盈亏追踪
- ✅ 单个持仓盈亏

### 2. 交易功能 (`/api/v1/trading`)
- ✅ 下单（市价、限价、止损、止损限价）
- ✅ 查询所有订单
- ✅ 查询未完成订单
- ✅ 取消订单
- ✅ 查询成交记录
- ✅ 合约验证和详情

### 3. 市场数据 (`/api/v1/market-data`)
- ✅ 实时行情订阅
- ✅ 历史K线数据
- ✅ 历史Tick数据
- ✅ 市场深度（Level 2）
- ✅ 实时5秒K线
- ✅ 设置数据类型（实时/延迟）

### 4. 研究数据 (`/api/v1/research`)
- ✅ 合约详细信息
- ✅ 基本面数据（财务报表、比率等）
- ✅ 新闻提供商列表
- ✅ 历史新闻
- ✅ 新闻文章内容
- ✅ 市场扫描器
- ✅ 期权链数据
- ✅ 价格直方图

## 安装

### 前置要求
- Python 3.10+
- IB Gateway 或 TWS (Trader Workstation)
- `uv` 包管理器

### 步骤

1. 克隆项目
```bash
cd bullfund-ibkr
```

2. 使用 uv 安装依赖
```bash
uv sync
```

3. 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
IB_HOST=127.0.0.1
IB_PORT=7497  # TWS: 7497, Gateway: 4001
IB_CLIENT_ID=1
IB_READONLY=false
```

4. 启动 IB Gateway 或 TWS
   - 配置 → API → 设置 → 启用 "Enable ActiveX and Socket Clients"
   - 设置端口: TWS = 7497, Gateway = 4001
   - 内存分配: 最少 4096 MB

## 运行

### 使用 uv 运行
```bash
uv run python main.py
```

### 使用 uvicorn 运行
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 使用示例

### 1. 获取账户信息
```bash
curl http://localhost:8000/api/v1/account/summary
```

### 2. 获取持仓
```bash
curl http://localhost:8000/api/v1/account/positions
```

### 3. 下市价单
```bash
curl -X POST http://localhost:8000/api/v1/trading/orders/place \
  -H "Content-Type: application/json" \
  -d '{
    "contract": {
      "symbol": "AAPL",
      "sec_type": "STK",
      "exchange": "SMART",
      "currency": "USD"
    },
    "action": "BUY",
    "order_type": "MKT",
    "quantity": 100
  }'
```

### 4. 获取实时行情
```bash
curl -X POST http://localhost:8000/api/v1/market-data/ticker \
  -H "Content-Type: application/json" \
  -d '{
    "contract": {
      "symbol": "AAPL",
      "sec_type": "STK",
      "exchange": "SMART",
      "currency": "USD"
    },
    "snapshot": false
  }'
```

### 5. 获取历史K线
```bash
curl -X POST http://localhost:8000/api/v1/market-data/historical-bars \
  -H "Content-Type: application/json" \
  -d '{
    "contract": {
      "symbol": "AAPL",
      "sec_type": "STK",
      "exchange": "SMART",
      "currency": "USD"
    },
    "bar_size": "1 hour",
    "duration": "1 D",
    "what_to_show": "TRADES"
  }'
```

### 6. 获取期权链
```bash
curl -X POST http://localhost:8000/api/v1/research/options-chain \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "sec_type": "STK",
    "exchange": "SMART",
    "currency": "USD"
  }'
```

## 项目结构

```
bullfund-ibkr/
├── main.py              # FastAPI 主应用
├── config.py            # 配置管理
├── models.py            # Pydantic 数据模型
├── ib_client.py         # IB 连接管理
├── routers/
│   ├── __init__.py
│   ├── account.py       # 账户相关端点
│   ├── trading.py       # 交易相关端点
│   ├── market_data.py   # 市场数据端点
│   └── research.py      # 研究数据端点
├── .env                 # 环境变量（需创建）
├── .env.example         # 环境变量示例
├── pyproject.toml       # uv 项目配置
└── README.md
```

## 注意事项

1. **连接管理**: 应用启动时会自动连接到 IB Gateway/TWS，关闭时自动断开
2. **错误处理**: 所有 API 都包含完整的错误处理和日志记录
3. **市场数据**: 某些市场数据需要订阅才能访问
4. **订单权限**: 如果设置 `IB_READONLY=true`，将无法下单
5. **Client ID**: 每个连接需要唯一的 Client ID

## 支持的合约类型

- ✅ 股票 (STK)
- ✅ 期权 (OPT)
- ✅ 期货 (FUT)
- ✅ 外汇 (CASH)
- ✅ 指数 (IND)
- ✅ 债券 (BOND)
- ✅ 基金 (FUND)
- ✅ 差价合约 (CFD)

## 支持的订单类型

- ✅ 市价单 (MKT)
- ✅ 限价单 (LMT)
- ✅ 止损单 (STP)
- ✅ 止损限价单 (STP LMT)
- ✅ 支持括号单、OCA组等高级订单

## 测试

项目包含两种类型的测试：

### 1. 单元测试（不需要 IB 连接）

测试数据模型、配置和 FastAPI 应用。

```bash
# 运行单元测试
uv run pytest tests/test_models.py tests/test_config.py tests/test_main.py -v

# 或使用快速测试脚本
./test.sh
```

**状态**: ✅ 21/21 测试通过

### 2. 集成测试（需要真实 IB 连接）

使用真实的 IB Gateway/TWS 连接测试所有 API 功能。

```bash
# 前置条件：
# 1. 启动 IB Gateway 或 TWS (推荐使用纸交易账户)
# 2. 配置 .env 文件
# 3. 启用 API 连接

# 运行集成测试
./test_integration.sh

# 或直接运行
uv run pytest tests/integration/ -v -s
```

**测试覆盖**:
- ✅ 账户管理（账户信息、持仓、盈亏）
- ✅ 市场数据（实时行情、历史K线、多周期）
- ✅ 交易功能（合约验证、订单查询、成交记录）
- ✅ 研究数据（合约详情、期权链、新闻、扫描器）

详细文档: [tests/integration/README.md](tests/integration/README.md)

### 测试覆盖率

```bash
# 查看覆盖率
uv run pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## 许可证

MIT
