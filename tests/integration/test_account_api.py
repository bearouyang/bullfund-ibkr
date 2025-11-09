import pytest


class TestManagedAccounts:
    """测试管理账户端点"""

    def test_get_managed_accounts_success(self, http_client, wait_for_api_ready):
        """测试获取管理账户列表 - 成功场景"""
        response = http_client.get("/api/v1/account/managed-accounts")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "accounts" in data
        assert "count" in data
        assert isinstance(data["accounts"], list)
        assert data["count"] == len(data["accounts"])

        # 纸交易账户应该至少有一个账户
        assert data["count"] > 0

        # 打印账户信息供调试
        print(f"\n找到 {data['count']} 个管理账户: {data['accounts']}")


class TestAccountSummary:
    """测试账户摘要端点"""

    def test_get_account_summary_default(self, http_client):
        """测试获取默认账户摘要"""
        response = http_client.get("/api/v1/account/summary")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "account" in data
        assert "summary" in data
        assert isinstance(data["summary"], dict)

        # 验证关键指标存在
        summary = data["summary"]
        expected_keys = ["NetLiquidation", "TotalCashValue", "BuyingPower"]

        # 至少应该有一些关键指标
        assert any(
            key in summary for key in expected_keys
        ), f"摘要中缺少关键指标。实际键: {list(summary.keys())}"

        print(f"\n账户: {data['account']}")
        print(f"净清算价值: {summary.get('NetLiquidation', {}).get('value', 'N/A')}")
        print(f"总现金: {summary.get('TotalCashValue', {}).get('value', 'N/A')}")

    def test_get_account_summary_specific_account(self, http_client, test_config):
        """测试获取指定账户摘要"""
        # 先获取可用账户
        accounts_resp = http_client.get("/api/v1/account/managed-accounts")
        accounts = accounts_resp.json()["accounts"]

        if not accounts:
            pytest.skip("没有可用账户")

        # 使用第一个账户
        test_account = accounts[0]
        response = http_client.get(
            "/api/v1/account/summary", params={"account": test_account}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["account"] == test_account


class TestAccountValues:
    """测试账户详细值端点"""

    def test_get_account_values_default(self, http_client):
        """测试获取默认账户的详细值"""
        response = http_client.get("/api/v1/account/values")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "account" in data
        assert "values" in data
        assert isinstance(data["values"], dict)

        # values应该包含多个标签
        assert len(data["values"]) > 0

        # 每个值应该是列表
        for tag, value_list in data["values"].items():
            assert isinstance(value_list, list)
            assert len(value_list) > 0

            # 验证每个值的结构
            for value_item in value_list:
                assert "value" in value_item
                assert "currency" in value_item
                assert "account" in value_item

        print(f"\n账户值标签数量: {len(data['values'])}")

    def test_get_account_values_specific_account(self, http_client):
        """测试获取指定账户的详细值"""
        # 先获取可用账户
        accounts_resp = http_client.get("/api/v1/account/managed-accounts")
        accounts = accounts_resp.json()["accounts"]

        if not accounts:
            pytest.skip("没有可用账户")

        test_account = accounts[0]
        response = http_client.get(
            "/api/v1/account/values", params={"account": test_account}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["account"] == test_account


class TestPositions:
    """测试持仓端点"""

    def test_get_positions_default(self, http_client):
        """测试获取默认账户持仓"""
        response = http_client.get("/api/v1/account/positions")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "positions" in data
        assert "count" in data
        assert isinstance(data["positions"], list)
        assert data["count"] == len(data["positions"])

        print(f"\n找到 {data['count']} 个持仓")

        # 如果有持仓，验证结构
        if data["count"] > 0:
            position = data["positions"][0]
            assert "account" in position
            assert "contract" in position
            assert "position" in position
            assert "avg_cost" in position

            # 验证合约结构
            contract = position["contract"]
            assert "symbol" in contract
            assert "sec_type" in contract
            assert "exchange" in contract
            assert "currency" in contract

            print(
                f"示例持仓: {contract['symbol']} ({contract['sec_type']}) - "
                f"数量: {position['position']}, 均价: {position['avg_cost']}"
            )

    def test_get_positions_specific_account(self, http_client):
        """测试获取指定账户持仓"""
        # 先获取可用账户
        accounts_resp = http_client.get("/api/v1/account/managed-accounts")
        accounts = accounts_resp.json()["accounts"]

        if not accounts:
            pytest.skip("没有可用账户")

        test_account = accounts[0]
        response = http_client.get(
            "/api/v1/account/positions", params={"account": test_account}
        )

        assert response.status_code == 200
        data = response.json()

        # 如果有持仓，验证账户匹配
        if data["count"] > 0:
            for position in data["positions"]:
                assert position["account"] == test_account


class TestPortfolio:
    """测试投资组合端点"""

    def test_get_portfolio_default(self, http_client):
        """测试获取默认账户投资组合"""
        response = http_client.get("/api/v1/account/portfolio")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "portfolio" in data
        assert "count" in data
        assert isinstance(data["portfolio"], list)
        assert data["count"] == len(data["portfolio"])

        print(f"\n找到 {data['count']} 个投资组合项目")

        # 如果有投资组合项目，验证结构
        if data["count"] > 0:
            item = data["portfolio"][0]
            assert "account" in item
            assert "contract" in item
            assert "position" in item
            assert "market_price" in item
            assert "market_value" in item
            assert "average_cost" in item
            assert "unrealized_pnl" in item
            assert "realized_pnl" in item

            # 验证合约结构
            contract = item["contract"]
            assert "symbol" in contract
            assert "sec_type" in contract

            print(
                f"示例投资组合: {contract['symbol']} - "
                f"市值: {item['market_value']}, "
                f"未实现盈亏: {item['unrealized_pnl']}"
            )

    def test_get_portfolio_specific_account(self, http_client):
        """测试获取指定账户投资组合"""
        # 先获取可用账户
        accounts_resp = http_client.get("/api/v1/account/managed-accounts")
        accounts = accounts_resp.json()["accounts"]

        if not accounts:
            pytest.skip("没有可用账户")

        test_account = accounts[0]
        response = http_client.get(
            "/api/v1/account/portfolio", params={"account": test_account}
        )

        assert response.status_code == 200
        data = response.json()

        # 如果有投资组合项目，验证账户匹配
        if data["count"] > 0:
            for item in data["portfolio"]:
                assert item["account"] == test_account

    def test_portfolio_vs_positions_consistency(self, http_client):
        """测试投资组合和持仓的一致性"""
        positions_resp = http_client.get("/api/v1/account/positions")
        portfolio_resp = http_client.get("/api/v1/account/portfolio")

        positions_data = positions_resp.json()
        portfolio_data = portfolio_resp.json()

        # 投资组合和持仓数量应该一致
        assert (
            positions_data["count"] == portfolio_data["count"]
        ), f"持仓数量 ({positions_data['count']}) 与投资组合数量 ({portfolio_data['count']}) 不一致"

        # 如果有数据，验证符号匹配
        if positions_data["count"] > 0:
            position_symbols = {
                p["contract"]["symbol"] for p in positions_data["positions"]
            }
            portfolio_symbols = {
                p["contract"]["symbol"] for p in portfolio_data["portfolio"]
            }

            assert (
                position_symbols == portfolio_symbols
            ), f"持仓符号 {position_symbols} 与投资组合符号 {portfolio_symbols} 不匹配"


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_account_summary(self, http_client):
        """测试使用无效账户获取摘要"""
        response = http_client.get(
            "/api/v1/account/summary", params={"account": "INVALID_ACCOUNT_123"}
        )

        # 可能返回500错误或空数据
        # 具体行为取决于IB API的实现
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            # 如果成功返回，摘要应该为空或包含错误信息
            print(f"\n无效账户响应: {data}")
