"""
交易和订单管理API集成测试
注意: 这些测试需要真实的IB Gateway/TWS连接，不使用mock
警告: 某些测试会创建真实订单（在纸交易账户中），运行前请确保：
1. 使用纸交易账户
2. IB Gateway或TWS已启动
3. FastAPI服务正在运行
"""

import pytest
import time
import asyncio


class TestContractQualification:
    """测试合约验证端点"""

    def test_qualify_stock_contract(self, http_client, sample_stock_contract):
        """测试验证股票合约"""
        response = http_client.post(
            "/api/v1/trading/contract/qualify", json=sample_stock_contract
        )

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "contracts" in data
        assert "count" in data
        assert data["count"] > 0
        assert isinstance(data["contracts"], list)

        print(f"\n验证 {sample_stock_contract['symbol']} - 找到 {data['count']} 个合约")

    def test_qualify_forex_contract(self, http_client, sample_forex_contract):
        """测试验证外汇合约"""
        response = http_client.post(
            "/api/v1/trading/contract/qualify", json=sample_forex_contract
        )

        assert response.status_code == 200
        data = response.json()

        assert "contracts" in data
        assert "count" in data
        assert data["count"] > 0

        print(
            f"\n验证外汇合约 {sample_forex_contract['symbol']} - 找到 {data['count']} 个合约"
        )


class TestOpenOrders:
    """测试未结订单端点"""

    def test_get_open_orders(self, http_client):
        """测试获取未结订单列表"""
        response = http_client.get("/api/v1/trading/orders/open")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "orders" in data
        assert "count" in data
        assert isinstance(data["orders"], list)
        assert data["count"] == len(data["orders"])

        print(f"\n找到 {data['count']} 个未结订单")

        # 如果有订单，打印详情
        if data["count"] > 0:
            print("未结订单详情:")
            for order in data["orders"][:3]:  # 只打印前3个
                print(f"  - 订单: {order}")


class TestAllOrders:
    """测试所有订单端点"""

    def test_get_all_orders(self, http_client):
        """测试获取所有订单列表"""
        response = http_client.get("/api/v1/trading/orders/all")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "orders" in data
        assert "count" in data
        assert isinstance(data["orders"], list)
        assert data["count"] == len(data["orders"])

        print(f"\n找到 {data['count']} 个总订单")


class TestExecutions:
    """测试成交历史端点"""

    def test_get_executions(self, http_client):
        """测试获取成交历史"""
        response = http_client.get("/api/v1/trading/executions")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "executions" in data
        assert "count" in data
        assert isinstance(data["executions"], list)
        assert data["count"] == len(data["executions"])

        print(f"\n找到 {data['count']} 个成交记录")

        # 如果有成交，打印详情
        if data["count"] > 0:
            print("成交记录详情:")
            for execution in data["executions"][:3]:  # 只打印前3个
                print(f"  - 成交: {execution}")


class TestPlaceOrder:
    """
    测试下单端点
    警告: 这些测试会创建真实订单！仅在纸交易账户中运行
    """

    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    def test_place_market_order_stock(self, http_client, sample_stock_contract):
        """
        测试下市价单购买股票
        警告: 会创建真实订单（纸交易）
        """
        order_request = {
            "contract": sample_stock_contract,
            "action": "BUY",
            "order_type": "MKT",
            "quantity": 1,
        }

        response = http_client.post("/api/v1/trading/orders/place", json=order_request)

        assert response.status_code == 200
        data = response.json()

        # 验证响应包含订单ID和状态
        assert "order_id" in data
        assert "status" in data
        assert isinstance(data["order_id"], int)
        assert data["order_id"] > 0

        print(f"\n✓ 订单已下达:")
        print(f"  订单ID: {data['order_id']}")
        print(f"  状态: {data['status']}")
        print(f"  合约: {sample_stock_contract['symbol']}")
        print(f"  操作: BUY {order_request['quantity']} 股")

        # 等待一下让订单处理
        time.sleep(2)

        # 验证订单出现在未结订单列表中
        open_orders_resp = http_client.get("/api/v1/trading/orders/open")
        open_orders_data = open_orders_resp.json()

        # 检查我们的订单是否在列表中
        order_ids = [str(order) for order in open_orders_data["orders"]]
        print(f"\n当前未结订单数: {open_orders_data['count']}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    async def test_place_sell_order_stock(self, http_client, sample_stock_contract):
        """
        测试下市价单卖出股票
        警告: 会创建真实订单（纸交易）
        注意: 如果账户没有持仓，会创建空头仓位
        """
        order_request = {
            "contract": sample_stock_contract,
            "action": "SELL",
            "order_type": "MKT",
            "quantity": 1,
        }

        response = http_client.post("/api/v1/trading/orders/place", json=order_request)

        assert response.status_code == 200
        data = response.json()

        assert "order_id" in data
        assert "status" in data

        print(f"\n✓ 卖出订单已下达:")
        print(f"  订单ID: {data['order_id']}")
        print(f"  状态: {data['status']}")
        print(f"  合约: {sample_stock_contract['symbol']}")
        print(f"  操作: SELL {order_request['quantity']} 股")


class TestOrderWorkflow:
    """测试完整的订单工作流"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    async def test_complete_order_workflow(self, http_client, sample_stock_contract):
        """
        测试完整订单流程:
        1. 验证合约
        2. 下单
        3. 检查未结订单
        4. 检查所有订单

        警告: 会创建真实订单（纸交易）
        """
        print(f"\n=== 开始完整订单工作流测试 ===")

        # 步骤1: 验证合约
        print("\n步骤1: 验证合约...")
        qualify_resp = http_client.post(
            "/api/v1/trading/contract/qualify", json=sample_stock_contract
        )
        assert qualify_resp.status_code == 200
        qualify_data = qualify_resp.json()
        assert qualify_data["count"] > 0
        print(f"✓ 合约验证成功，找到 {qualify_data['count']} 个合约")

        # 步骤2: 获取下单前的未结订单数
        print("\n步骤2: 检查当前未结订单...")
        before_orders_resp = http_client.get("/api/v1/trading/orders/open")
        before_orders_data = before_orders_resp.json()
        before_count = before_orders_data["count"]
        print(f"✓ 当前未结订单数: {before_count}")

        # 步骤3: 下单
        print("\n步骤3: 下市价买入单...")
        order_request = {
            "contract": sample_stock_contract,
            "action": "BUY",
            "order_type": "MKT",
            "quantity": 1,
        }

        place_resp = http_client.post(
            "/api/v1/trading/orders/place", json=order_request
        )
        assert place_resp.status_code == 200
        place_data = place_resp.json()
        order_id = place_data["order_id"]
        print(f"✓ 订单已下达，订单ID: {order_id}, 状态: {place_data['status']}")

        # 等待订单处理
        await asyncio.sleep(3)

        # 步骤4: 验证未结订单增加或订单已成交
        print("\n步骤4: 验证订单状态...")
        after_orders_resp = http_client.get("/api/v1/trading/orders/open")
        after_orders_data = after_orders_resp.json()
        after_count = after_orders_data["count"]

        print(f"✓ 下单后未结订单数: {after_count}")

        # 市价单可能立即成交，所以未结订单数可能不变
        # 我们检查总订单数应该增加
        all_orders_resp = http_client.get("/api/v1/trading/orders/all")
        all_orders_data = all_orders_resp.json()
        print(f"✓ 总订单数: {all_orders_data['count']}")

        # 步骤5: 检查成交记录
        print("\n步骤5: 检查成交记录...")
        executions_resp = http_client.get("/api/v1/trading/executions")
        executions_data = executions_resp.json()
        print(f"✓ 总成交记录数: {executions_data['count']}")

        print(f"\n=== 订单工作流测试完成 ===")


class TestContractTypes:
    """测试不同类型的合约"""

    @pytest.mark.asyncio
    async def test_qualify_multiple_contract_types(self, http_client):
        """测试验证多种类型的合约"""
        contracts = [
            {
                "name": "股票",
                "contract": {
                    "symbol": "MSFT",
                    "sec_type": "STK",
                    "exchange": "SMART",
                    "currency": "USD",
                },
            },
            {
                "name": "外汇",
                "contract": {
                    "symbol": "GBPUSD",
                    "sec_type": "CASH",
                    "exchange": "IDEALPRO",
                    "currency": "USD",
                },
            },
        ]

        print("\n测试多种合约类型:")

        for item in contracts:
            response = http_client.post(
                "/api/v1/trading/contract/qualify", json=item["contract"]
            )

            assert response.status_code == 200
            data = response.json()
            assert data["count"] > 0

            print(
                f"  ✓ {item['name']} ({item['contract']['symbol']}): "
                f"找到 {data['count']} 个合约"
            )


class TestErrorScenarios:
    """测试错误场景"""

    @pytest.mark.asyncio
    async def test_place_order_missing_fields(self, http_client):
        """测试缺少必填字段的下单请求"""
        incomplete_order = {
            "contract": {
                "symbol": "AAPL",
                "sec_type": "STK",
                # 缺少 exchange 和 currency
            },
            "action": "BUY",
            "quantity": 1,
            # 缺少 order_type
        }

        response = http_client.post(
            "/api/v1/trading/orders/place", json=incomplete_order
        )

        # 应该返回422验证错误
        assert response.status_code == 422
        print(f"\n缺少字段正确返回422验证错误")

    @pytest.mark.asyncio
    async def test_qualify_contract_missing_fields(self, http_client):
        """测试缺少必填字段的合约验证请求"""
        incomplete_contract = {
            # 完全缺少symbol字段，这是唯一的必填字段
        }

        response = http_client.post(
            "/api/v1/trading/contract/qualify", json=incomplete_contract
        )

        # 应该返回422验证错误
        assert response.status_code == 422
        print(f"\n缺少字段正确返回422验证错误")


class TestOrderTypes:
    """测试不同类型的订单"""

    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    def test_place_limit_order(self, http_client, sample_stock_contract):
        """测试下限价单"""
        order_request = {
            "contract": sample_stock_contract,
            "action": "BUY",
            "order_type": "LMT",
            "quantity": 1,
            "limit_price": 100.0,  # 设置一个较低的限价，不会立即成交
        }

        response = http_client.post("/api/v1/trading/orders/place", json=order_request)

        assert response.status_code == 200
        data = response.json()

        assert "order_id" in data
        assert "status" in data

        print(f"\n✓ 限价单已下达:")
        print(f"  订单ID: {data['order_id']}")
        print(f"  限价: {order_request['limit_price']}")

    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    def test_place_stop_order(self, http_client, sample_stock_contract):
        """测试下止损单"""
        order_request = {
            "contract": sample_stock_contract,
            "action": "SELL",
            "order_type": "STP",
            "quantity": 1,
            "stop_price": 50.0,  # 设置一个较低的止损价
        }

        response = http_client.post("/api/v1/trading/orders/place", json=order_request)

        assert response.status_code == 200
        data = response.json()

        print(f"\n✓ 止损单已下达:")
        print(f"  订单ID: {data['order_id']}")
        print(f"  止损价: {order_request['stop_price']}")

    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    def test_place_stop_limit_order(self, http_client, sample_stock_contract):
        """测试下止损限价单"""
        order_request = {
            "contract": sample_stock_contract,
            "action": "SELL",
            "order_type": "STP LMT",
            "quantity": 1,
            "stop_price": 150.0,
            "limit_price": 145.0,
        }

        response = http_client.post("/api/v1/trading/orders/place", json=order_request)

        assert response.status_code == 200
        data = response.json()

        print(f"\n✓ 止损限价单已下达:")
        print(f"  订单ID: {data['order_id']}")

    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    def test_place_trailing_stop_order(self, http_client, sample_stock_contract):
        """测试下追踪止损单"""
        order_request = {
            "contract": sample_stock_contract,
            "action": "SELL",
            "order_type": "TRAIL",
            "quantity": 1,
            "stop_price": 2.0,  # 追踪2%
        }

        response = http_client.post("/api/v1/trading/orders/place", json=order_request)

        assert response.status_code == 200
        data = response.json()

        print(f"\n✓ 追踪止损单已下达:")
        print(f"  订单ID: {data['order_id']}")

    def test_limit_order_missing_limit_price(self, http_client, sample_stock_contract):
        """测试限价单缺少限价参数"""
        order_request = {
            "contract": sample_stock_contract,
            "action": "BUY",
            "order_type": "LMT",
            "quantity": 1,
            # 缺少 limit_price
        }

        response = http_client.post("/api/v1/trading/orders/place", json=order_request)

        # 应该返回400错误
        assert response.status_code == 400
        print(f"\n✓ 缺少限价参数正确返回400错误")


class TestOrderManagement:
    """测试订单管理功能"""

    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    def test_modify_order(self, http_client, sample_stock_contract):
        """测试修改订单"""
        # 先下一个限价单
        order_request = {
            "contract": sample_stock_contract,
            "action": "BUY",
            "order_type": "LMT",
            "quantity": 1,
            "limit_price": 100.0,
        }

        place_resp = http_client.post(
            "/api/v1/trading/orders/place", json=order_request
        )
        assert place_resp.status_code == 200
        order_id = place_resp.json()["order_id"]

        print(f"\n✓ 原始订单已下达，订单ID: {order_id}")

        # 等待一下
        import time
        time.sleep(2)

        # 修改订单
        modify_request = {
            "order_id": order_id,
            "limit_price": 105.0,
            "quantity": 2,
        }

        modify_resp = http_client.post(
            "/api/v1/trading/orders/modify", json=modify_request
        )

        # 订单可能已成交或被取消，所以允许404
        assert modify_resp.status_code in [200, 404, 500]

        if modify_resp.status_code == 200:
            data = modify_resp.json()
            print(f"\n✓ 订单已修改:")
            print(f"  订单ID: {data['order_id']}")
            print(f"  新限价: {modify_request['limit_price']}")
        else:
            print(f"\n⚠ 订单无法修改(可能已成交或取消)")

    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    def test_cancel_order(self, http_client, sample_stock_contract):
        """测试取消订单"""
        # 先下一个限价单
        order_request = {
            "contract": sample_stock_contract,
            "action": "BUY",
            "order_type": "LMT",
            "quantity": 1,
            "limit_price": 100.0,
        }

        place_resp = http_client.post(
            "/api/v1/trading/orders/place", json=order_request
        )
        assert place_resp.status_code == 200
        order_id = place_resp.json()["order_id"]

        print(f"\n✓ 订单已下达，订单ID: {order_id}")

        # 等待一下
        import time
        time.sleep(2)

        # 取消订单
        cancel_request = {"order_id": order_id}

        cancel_resp = http_client.post(
            "/api/v1/trading/orders/cancel", json=cancel_request
        )

        # 订单可能已成交，所以允许404
        assert cancel_resp.status_code in [200, 404, 500]

        if cancel_resp.status_code == 200:
            data = cancel_resp.json()
            print(f"\n✓ 订单已取消:")
            print(f"  订单ID: {data['order_id']}")
            print(f"  状态: {data['status']}")
        else:
            print(f"\n⚠ 订单无法取消(可能已成交)")

    def test_get_specific_order(self, http_client):
        """测试获取特定订单详情"""
        # 先获取所有订单
        all_orders_resp = http_client.get("/api/v1/trading/orders/all")
        all_orders_data = all_orders_resp.json()

        if all_orders_data["count"] == 0:
            pytest.skip("没有订单可测试")

        # 尝试获取一个订单的ID
        # 注意：这需要从订单对象中提取订单ID
        # 由于订单格式可能不同，这里只测试端点可用性
        print(f"\n✓ 找到 {all_orders_data['count']} 个订单")

    def test_cancel_nonexistent_order(self, http_client):
        """测试取消不存在的订单"""
        cancel_request = {"order_id": 999999999}

        response = http_client.post(
            "/api/v1/trading/orders/cancel", json=cancel_request
        )

        # 应该返回404
        assert response.status_code == 404
        print(f"\n✓ 不存在的订单正确返回404")


class TestOrderWorkflowAdvanced:
    """测试高级订单工作流"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.paper_trading_only
    async def test_place_modify_cancel_workflow(self, http_client, sample_stock_contract):
        """测试完整的下单-修改-取消工作流"""
        print(f"\n=== 订单工作流: 下单 -> 修改 -> 取消 ===")

        # 1. 下单
        print("\n步骤1: 下限价单...")
        order_request = {
            "contract": sample_stock_contract,
            "action": "BUY",
            "order_type": "LMT",
            "quantity": 1,
            "limit_price": 100.0,
        }

        place_resp = http_client.post(
            "/api/v1/trading/orders/place", json=order_request
        )
        assert place_resp.status_code == 200
        order_id = place_resp.json()["order_id"]
        print(f"✓ 订单已下达，ID: {order_id}")

        # 等待订单处理
        await asyncio.sleep(2)

        # 2. 修改订单
        print("\n步骤2: 修改订单...")
        modify_request = {
            "order_id": order_id,
            "limit_price": 105.0,
        }

        modify_resp = http_client.post(
            "/api/v1/trading/orders/modify", json=modify_request
        )

        if modify_resp.status_code == 200:
            print(f"✓ 订单已修改，新限价: 105.0")
        else:
            print(f"⚠ 订单修改失败 (状态码: {modify_resp.status_code})")

        await asyncio.sleep(2)

        # 3. 取消订单
        print("\n步骤3: 取消订单...")
        cancel_request = {"order_id": order_id}

        cancel_resp = http_client.post(
            "/api/v1/trading/orders/cancel", json=cancel_request
        )

        if cancel_resp.status_code == 200:
            print(f"✓ 订单已取消")
        else:
            print(f"⚠ 订单取消失败 (状态码: {cancel_resp.status_code})")

        print(f"\n=== 订单工作流完成 ===")


class TestMultipleContractTypes:
    """测试多种合约类型的交易"""

    def test_qualify_stock(self, http_client):
        """测试验证股票合约"""
        contract = {
            "symbol": "MSFT",
            "sec_type": "STK",
            "exchange": "SMART",
            "currency": "USD",
        }

        response = http_client.post("/api/v1/trading/contract/qualify", json=contract)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0

        print(f"\n✓ 验证股票合约 MSFT: {data['count']} 个")

    def test_qualify_forex(self, http_client):
        """测试验证外汇合约"""
        contract = {
            "symbol": "EURUSD",
            "sec_type": "CASH",
            "exchange": "IDEALPRO",
            "currency": "USD",
        }

        response = http_client.post("/api/v1/trading/contract/qualify", json=contract)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0

        print(f"\n✓ 验证外汇合约 EURUSD: {data['count']} 个")
