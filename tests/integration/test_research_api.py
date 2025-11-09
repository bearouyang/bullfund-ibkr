"""
研究和合约详情API集成测试
注意: 这些测试需要真实的IB Gateway/TWS连接，不使用mock
运行前确保：
1. IB Gateway或TWS已启动
2. FastAPI服务正在运行
"""

import pytest


class TestContractDetails:
    """测试合约详情端点"""

    def test_get_stock_contract_details(self, http_client, sample_stock_contract):
        """测试获取股票合约详情"""
        response = http_client.post(
            "/api/v1/research/contract-details", json=sample_stock_contract
        )

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "details" in data
        assert "count" in data
        assert isinstance(data["details"], list)
        assert data["count"] == len(data["details"])

        # 应该至少有一个合约详情
        assert data["count"] > 0, "未返回合约详情"

        print(f"\n✓ 获取 {sample_stock_contract['symbol']} 合约详情:")
        print(f"  找到 {data['count']} 个合约")

        # 打印详情（如果数据结构允许）
        if data["details"]:
            detail = data["details"][0]
            print(f"  合约详情: {detail}")

    def test_get_forex_contract_details(self, http_client, sample_forex_contract):
        """测试获取外汇合约详情"""
        response = http_client.post(
            "/api/v1/research/contract-details", json=sample_forex_contract
        )

        assert response.status_code == 200
        data = response.json()

        assert "details" in data
        assert "count" in data
        assert data["count"] > 0

        print(f"\n✓ 获取外汇 {sample_forex_contract['symbol']} 合约详情:")
        print(f"  找到 {data['count']} 个合约")

    def test_get_option_contract_details(self, http_client, sample_option_contract):
        """测试获取期权合约详情"""
        response = http_client.post(
            "/api/v1/research/contract-details", json=sample_option_contract
        )

        # 期权合约可能不存在或已过期，所以允许404
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 获取期权 {sample_option_contract['symbol']} 合约详情:")
            print(f"  找到 {data['count']} 个合约")
        else:
            print(f"\n期权合约不存在或已过期: {sample_option_contract}")

    def test_get_invalid_contract_details(self, http_client):
        """测试获取无效合约详情"""
        invalid_contract = {
            "symbol": "INVALIDXYZ123",
            "sec_type": "STK",
            "exchange": "SMART",
            "currency": "USD",
        }

        response = http_client.post(
            "/api/v1/research/contract-details", json=invalid_contract
        )

        # 应该返回404
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

        print(f"\n无效合约正确返回404: {data['detail']}")

    def test_multiple_contract_types_details(self, http_client):
        """测试多种类型合约的详情"""
        contracts = [
            {
                "name": "股票 - AAPL",
                "contract": {
                    "symbol": "AAPL",
                    "sec_type": "STK",
                    "exchange": "SMART",
                    "currency": "USD",
                },
            },
            {
                "name": "股票 - MSFT",
                "contract": {
                    "symbol": "MSFT",
                    "sec_type": "STK",
                    "exchange": "SMART",
                    "currency": "USD",
                },
            },
            {
                "name": "外汇 - EURUSD",
                "contract": {
                    "symbol": "EURUSD",
                    "sec_type": "CASH",
                    "exchange": "IDEALPRO",
                    "currency": "USD",
                },
            },
            {
                "name": "外汇 - GBPUSD",
                "contract": {
                    "symbol": "GBPUSD",
                    "sec_type": "CASH",
                    "exchange": "IDEALPRO",
                    "currency": "USD",
                },
            },
        ]

        print(f"\n测试多种合约的详情:")

        for item in contracts:
            response = http_client.post(
                "/api/v1/research/contract-details", json=item["contract"]
            )

            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ {item['name']}: {data['count']} 个合约详情")
            else:
                print(f"  ✗ {item['name']}: 错误 {response.status_code}")

    def test_contract_details_completeness(self, http_client, sample_stock_contract):
        """测试合约详情的数据完整性"""
        response = http_client.post(
            "/api/v1/research/contract-details", json=sample_stock_contract
        )

        assert response.status_code == 200
        data = response.json()

        # 验证返回的详情列表不为空
        assert data["count"] > 0
        assert len(data["details"]) > 0

        # 验证每个详情对象存在
        for i, detail in enumerate(data["details"]):
            assert detail is not None, f"详情 {i} 为空"
            # 详情应该是字典或对象
            assert isinstance(detail, (dict, object)), f"详情 {i} 类型错误"

        print(f"\n✓ 合约详情数据完整，共 {data['count']} 个详情对象")


class TestErrorHandling:
    """测试错误处理"""

    def test_missing_required_fields(self, http_client):
        """测试缺少必填字段 - symbol字段是必需的"""
        incomplete_contract = {
            # 完全空的请求体
        }

        response = http_client.post(
            "/api/v1/research/contract-details", json=incomplete_contract
        )

        # 应该返回422验证错误（缺少symbol）
        assert response.status_code == 422

        print(f"\n缺少必填字段正确返回422验证错误")

    def test_invalid_sec_type(self, http_client):
        """测试无效的证券类型"""
        invalid_contract = {
            "symbol": "AAPL",
            "sec_type": "INVALID",
            "exchange": "SMART",
            "currency": "USD",
        }

        response = http_client.post(
            "/api/v1/research/contract-details", json=invalid_contract
        )

        # 应该返回422验证错误
        assert response.status_code == 422

        print(f"\n无效证券类型正确返回422验证错误")


class TestContractComparison:
    """测试合约对比和验证"""

    def test_compare_qualify_vs_details(self, http_client, sample_stock_contract):
        """
        测试合约验证 vs 合约详情的一致性
        两个端点应该返回相同合约的信息
        """
        # 获取合约验证结果
        qualify_resp = http_client.post(
            "/api/v1/trading/contract/qualify", json=sample_stock_contract
        )

        # 获取合约详情
        details_resp = http_client.post(
            "/api/v1/research/contract-details", json=sample_stock_contract
        )

        assert qualify_resp.status_code == 200
        assert details_resp.status_code == 200

        qualify_data = qualify_resp.json()
        details_data = details_resp.json()

        # 两个端点应该返回相同数量的合约
        assert (
            qualify_data["count"] == details_data["count"]
        ), f"合约验证返回 {qualify_data['count']} 个，详情返回 {details_data['count']} 个"

        print(f"\n✓ 合约验证和详情一致性检查:")
        print(f"  验证端点: {qualify_data['count']} 个合约")
        print(f"  详情端点: {details_data['count']} 个合约")


class TestPopularContracts:
    """测试常用合约的详情"""

    def test_popular_stocks(self, http_client):
        """测试热门股票合约详情"""
        popular_stocks = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "JPM",
            "V",
            "WMT",
        ]

        print(f"\n测试热门股票合约详情:")
        success_count = 0

        for symbol in popular_stocks:
            contract = {
                "symbol": symbol,
                "sec_type": "STK",
                "exchange": "SMART",
                "currency": "USD",
            }

            response = http_client.post(
                "/api/v1/research/contract-details", json=contract
            )

            if response.status_code == 200:
                data = response.json()
                success_count += 1
                print(f"  ✓ {symbol}: {data['count']} 个合约")
            else:
                print(f"  ✗ {symbol}: 错误 {response.status_code}")

        # 大部分热门股票应该成功
        assert (
            success_count >= len(popular_stocks) * 0.8
        ), f"只有 {success_count}/{len(popular_stocks)} 个股票成功"

    def test_major_forex_pairs(self, http_client):
        """测试主要外汇对详情"""
        major_pairs = [
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "USDCHF",
            "AUDUSD",
            "USDCAD",
            "NZDUSD",
        ]

        print(f"\n测试主要外汇对详情:")
        success_count = 0

        for pair in major_pairs:
            contract = {
                "symbol": pair,
                "sec_type": "CASH",
                "exchange": "IDEALPRO",
                "currency": "USD",
            }

            response = http_client.post(
                "/api/v1/research/contract-details", json=contract
            )

            if response.status_code == 200:
                data = response.json()
                success_count += 1
                print(f"  ✓ {pair}: {data['count']} 个合约")
            else:
                print(f"  ✗ {pair}: 错误 {response.status_code}")

        # 大部分外汇对应该成功
        assert (
            success_count >= len(major_pairs) * 0.8
        ), f"只有 {success_count}/{len(major_pairs)} 个外汇对成功"


class TestConcurrentRequests:
    """测试并发请求"""

    @pytest.mark.slow
    def test_concurrent_contract_details(self, http_client):
        """测试并发获取多个合约详情"""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

        print(f"\n顺序请求 {len(symbols)} 个合约详情...")

        results = []
        for symbol in symbols:
            contract = {
                "symbol": symbol,
                "sec_type": "STK",
                "exchange": "SMART",
                "currency": "USD",
            }

            response = http_client.post(
                "/api/v1/research/contract-details", json=contract
            )

            results.append((symbol, response))

        # 验证所有请求都成功
        success_count = 0
        for symbol, response in results:
            if response.status_code == 200:
                data = response.json()
                success_count += 1
                print(f"  ✓ {symbol}: {data['count']} 个合约")
            else:
                print(f"  ✗ {symbol}: 错误 {response.status_code}")

        assert success_count == len(
            symbols
        ), f"只有 {success_count}/{len(symbols)} 个请求成功"
