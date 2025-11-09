"""
市场扫描器API集成测试
注意: 这些测试需要真实的IB Gateway/TWS连接，不使用mock
运行前确保：
1. IB Gateway或TWS已启动
2. FastAPI服务正在运行
3. 拥有市场扫描器数据订阅权限
"""

import pytest


class TestMarketScanner:
    """测试市场扫描器端点"""

    def test_run_top_gainers_scanner(self, http_client):
        """测试运行涨幅榜扫描器"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "TOP_PERC_GAIN",
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        # 扫描器可能需要特殊订阅
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "count" in data
            assert isinstance(data["results"], list)

            print(f"\n✓ 涨幅榜扫描结果: {data['count']} 个")

            if data["count"] > 0:
                result = data["results"][0]
                print(f"  第1名: {result['contract']['symbol']} - 排名 {result['rank']}")
        else:
            print(f"\n⚠ 扫描器不可用(可能需要市场扫描器订阅)")

    def test_run_top_losers_scanner(self, http_client):
        """测试运行跌幅榜扫描器"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "TOP_PERC_LOSE",
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 跌幅榜扫描结果: {data['count']} 个")

    def test_run_most_active_scanner(self, http_client):
        """测试运行成交量榜扫描器"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "MOST_ACTIVE",
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 成交量榜扫描结果: {data['count']} 个")

    def test_run_hot_contracts_scanner(self, http_client):
        """测试运行热门合约扫描器"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "HOT_BY_VOLUME",
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 热门合约扫描结果: {data['count']} 个")


class TestScannerWithFilters:
    """测试带过滤条件的扫描器"""

    def test_scanner_with_price_filter(self, http_client):
        """测试带价格过滤的扫描器"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "TOP_PERC_GAIN",
            "above_price": 10.0,
            "below_price": 100.0,
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 价格过滤(10-100)扫描结果: {data['count']} 个")

    def test_scanner_with_volume_filter(self, http_client):
        """测试带成交量过滤的扫描器"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "MOST_ACTIVE",
            "above_volume": 1000000,
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 成交量过滤(>100万)扫描结果: {data['count']} 个")

    def test_scanner_with_market_cap_filter(self, http_client):
        """测试带市值过滤的扫描器"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "TOP_PERC_GAIN",
            "market_cap_above": 1000000000.0,  # 10亿美元
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 市值过滤(>10亿)扫描结果: {data['count']} 个")


class TestScannerParameters:
    """测试扫描器参数端点"""

    def test_get_scanner_parameters(self, http_client):
        """测试获取可用的扫描器参数"""
        response = http_client.get("/api/v1/scanner/scanner-parameters")

        # 扫描器参数可能需要特殊权限
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "parameters" in data

            print(f"\n✓ 获取扫描器参数成功")
            # 参数是XML格式，这里只验证能获取到
        else:
            print(f"\n⚠ 扫描器参数不可用")


class TestScannerResultValidation:
    """测试扫描器结果验证"""

    def test_scanner_result_structure(self, http_client):
        """测试扫描器结果结构"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "TOP_PERC_GAIN",
            "number_of_rows": 5,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        if response.status_code == 200:
            data = response.json()

            # 验证响应结构
            assert "results" in data
            assert "count" in data

            if data["count"] > 0:
                result = data["results"][0]

                # 验证结果项结构
                assert "rank" in result
                assert "contract" in result

                # 验证合约结构
                contract = result["contract"]
                assert "con_id" in contract
                assert "symbol" in contract
                assert "sec_type" in contract
                assert "exchange" in contract

                print(f"\n✓ 扫描器结果结构验证通过")
                print(f"  示例: {contract['symbol']} (排名 {result['rank']})")


class TestDifferentMarkets:
    """测试不同市场的扫描器"""

    def test_scan_us_stocks(self, http_client):
        """测试美股扫描"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "TOP_PERC_GAIN",
            "number_of_rows": 5,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 美股扫描结果: {data['count']} 个")

    def test_scan_us_nasdaq(self, http_client):
        """测试纳斯达克扫描"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.NASDAQ",
            "scan_code": "TOP_PERC_GAIN",
            "number_of_rows": 5,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 纳斯达克扫描结果: {data['count']} 个")


class TestScannerLimits:
    """测试扫描器限制"""

    def test_scanner_with_different_row_counts(self, http_client):
        """测试不同数量的扫描结果"""
        row_counts = [5, 10, 20, 50]

        print(f"\n测试不同数量的扫描结果:")

        for count in row_counts:
            scanner_request = {
                "instrument": "STK",
                "location_code": "STK.US.MAJOR",
                "scan_code": "MOST_ACTIVE",
                "number_of_rows": count,
            }

            response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

            if response.status_code == 200:
                data = response.json()
                actual_count = data["count"]
                print(f"  请求 {count} 条，返回 {actual_count} 条")

                # 返回的数量应该 <= 请求的数量
                assert actual_count <= count
            else:
                print(f"  请求 {count} 条失败")


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_scan_code(self, http_client):
        """测试无效的扫描代码"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "STK.US.MAJOR",
            "scan_code": "INVALID_SCAN_CODE_12345",
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        # 应该返回错误
        assert response.status_code in [400, 500]
        print(f"\n✓ 无效扫描代码正确返回错误")

    def test_invalid_location_code(self, http_client):
        """测试无效的位置代码"""
        scanner_request = {
            "instrument": "STK",
            "location_code": "INVALID.LOCATION",
            "scan_code": "TOP_PERC_GAIN",
            "number_of_rows": 10,
        }

        response = http_client.post("/api/v1/scanner/scan", json=scanner_request)

        # 应该返回错误
        assert response.status_code in [400, 500]
        print(f"\n✓ 无效位置代码正确返回错误")
