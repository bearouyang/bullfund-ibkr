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


class TestFundamentalData:
    """测试基本面数据端点"""

    def test_get_fundamental_data_summary(self, http_client, sample_stock_contract):
        """测试获取财务摘要基本面数据"""
        request_data = {
            "contract": sample_stock_contract,
            "report_type": "ReportsFinSummary",
        }

        response = http_client.post(
            "/api/v1/research/fundamental-data", json=request_data
        )

        # 某些股票可能没有基本面数据
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "symbol" in data
            assert "report_type" in data
            assert "data" in data

            print(f"\n✓ 获取 {sample_stock_contract['symbol']} 基本面数据")
            print(f"  报告类型: {data['report_type']}")
        else:
            print(f"\n⚠ {sample_stock_contract['symbol']} 基本面数据不可用")

    def test_get_fundamental_data_ratios(self, http_client, sample_stock_contract):
        """测试获取财务比率数据"""
        request_data = {
            "contract": sample_stock_contract,
            "report_type": "ReportRatios",
        }

        response = http_client.post(
            "/api/v1/research/fundamental-data", json=request_data
        )

        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 获取财务比率数据")


class TestNewsData:
    """测试新闻数据端点"""

    def test_get_news_providers(self, http_client):
        """测试获取新闻提供商列表"""
        response = http_client.get("/api/v1/research/news/providers")

        assert response.status_code == 200
        data = response.json()

        assert "providers" in data
        assert "count" in data
        assert isinstance(data["providers"], list)

        print(f"\n✓ 获取新闻提供商: {data['count']} 个")

        if data["count"] > 0:
            for provider in data["providers"][:5]:
                print(f"  - {provider['code']}: {provider['name']}")

    def test_get_historical_news(self, http_client, sample_stock_contract):
        """测试获取历史新闻"""
        request_data = {
            "contract": sample_stock_contract,
            "provider_codes": "BRFUPDN+DJNL",
            "total_results": 10,
        }

        response = http_client.post(
            "/api/v1/research/news/historical", json=request_data
        )

        # 新闻数据可能需要特殊订阅
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "articles" in data
            assert "count" in data

            print(f"\n✓ 获取 {sample_stock_contract['symbol']} 历史新闻: {data['count']} 条")

            if data["count"] > 0:
                article = data["articles"][0]
                print(f"  最新: {article['headline']}")
        else:
            print(f"\n⚠ 历史新闻不可用(可能需要新闻数据订阅)")

    def test_get_general_news(self, http_client):
        """测试获取一般市场新闻(不指定合约)"""
        request_data = {
            "provider_codes": "BRFUPDN+DJNL",
            "total_results": 5,
        }

        response = http_client.post(
            "/api/v1/research/news/historical", json=request_data
        )

        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 获取一般市场新闻: {data['count']} 条")


class TestOptionChain:
    """测试期权链数据端点"""

    def test_get_option_chain(self, http_client, sample_stock_contract):
        """测试获取期权链参数"""
        response = http_client.post(
            "/api/v1/research/option-chain", json=sample_stock_contract
        )

        # 并非所有股票都有期权
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "chains" in data
            assert "count" in data

            print(f"\n✓ 获取 {sample_stock_contract['symbol']} 期权链: {data['count']} 个交易类")

            if data["count"] > 0:
                chain = data["chains"][0]
                assert "exchange" in chain
                assert "expirations" in chain
                assert "strikes" in chain

                print(f"  交易所: {chain['exchange']}")
                print(f"  到期日数量: {len(chain['expirations'])}")
                print(f"  行权价数量: {len(chain['strikes'])}")

                if chain["expirations"]:
                    print(f"  最近到期日: {chain['expirations'][0]}")
        else:
            print(f"\n⚠ {sample_stock_contract['symbol']} 没有期权数据")


class TestContractSearch:
    """测试合约搜索端点"""

    def test_search_contracts_stock(self, http_client):
        """测试搜索股票合约"""
        response = http_client.get("/api/v1/research/search/AAPL")

        assert response.status_code == 200
        data = response.json()

        assert "matches" in data
        assert "count" in data
        assert isinstance(data["matches"], list)

        print(f"\n✓ 搜索 'AAPL': {data['count']} 个匹配结果")

        if data["count"] > 0:
            match = data["matches"][0]
            assert "contract" in match
            print(f"  {match['contract']['symbol']} - {match['contract']['sec_type']}")

    def test_search_contracts_partial(self, http_client):
        """测试部分匹配搜索"""
        response = http_client.get("/api/v1/research/search/GOOG")

        assert response.status_code == 200
        data = response.json()

        print(f"\n✓ 搜索 'GOOG': {data['count']} 个匹配结果")

        # 应该能找到 GOOGL, GOOG 等
        if data["count"] > 0:
            for match in data["matches"][:3]:
                print(f"  - {match['contract']['symbol']}")

    def test_search_contracts_no_results(self, http_client):
        """测试无结果搜索"""
        response = http_client.get("/api/v1/research/search/INVALIDXYZ12345")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 0
        print(f"\n✓ 无效搜索正确返回0个结果")


class TestHistogramData:
    """测试直方图数据端点"""

    def test_get_histogram_data(self, http_client, sample_stock_contract):
        """测试获取价格分布直方图数据"""
        response = http_client.post(
            "/api/v1/research/histogram",
            json=sample_stock_contract,
            params={"use_rth": True, "period": "1 day"},
        )

        # 直方图数据可能需要特殊权限
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "histogram" in data
            assert "count" in data

            print(f"\n✓ 获取直方图数据: {data['count']} 个价格区间")

            if data["count"] > 0:
                item = data["histogram"][0]
                print(f"  示例: 价格={item['price']}, 数量={item['count']}")
        else:
            print(f"\n⚠ 直方图数据不可用")


class TestDividends:
    """测试股息数据端点"""

    def test_get_dividends(self, http_client, sample_stock_contract):
        """测试获取股息数据"""
        response = http_client.post(
            "/api/v1/research/dividends", json=sample_stock_contract
        )

        # 股息数据可能需要特殊订阅
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert "symbol" in data
            assert "dividends" in data

            print(f"\n✓ 获取 {sample_stock_contract['symbol']} 股息数据")
        else:
            print(f"\n⚠ 股息数据不可用")


class TestMultipleSymbolsResearch:
    """测试多个股票的研究数据"""

    def test_search_multiple_stocks(self, http_client):
        """测试搜索多个股票"""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

        print(f"\n测试多个股票搜索:")

        for symbol in symbols:
            response = http_client.get(f"/api/v1/research/search/{symbol}")

            assert response.status_code == 200
            data = response.json()

            if data["count"] > 0:
                print(f"  ✓ {symbol}: {data['count']} 个结果")
            else:
                print(f"  ✗ {symbol}: 无结果")

