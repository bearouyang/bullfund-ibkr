import pytest


class TestHistoricalBars:
    """测试历史K线数据端点"""

    def test_get_historical_bars_stock_daily(self, http_client, sample_stock_contract):
        """测试获取股票日线数据"""
        bar_request = {
            "contract": sample_stock_contract,
            "duration": "1 M",
            "bar_size": "1 day",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "bars" in data
        assert "count" in data
        assert isinstance(data["bars"], list)
        assert data["count"] == len(data["bars"])

        # 应该有数据
        assert data["count"] > 0, "未返回历史数据"

        # 验证K线数据结构
        bar = data["bars"][0]
        assert "date" in bar
        assert "open" in bar
        assert "high" in bar
        assert "low" in bar
        assert "close" in bar
        assert "volume" in bar

        # 验证OHLC关系
        assert bar["high"] >= bar["low"], "最高价应该 >= 最低价"
        assert bar["high"] >= bar["open"], "最高价应该 >= 开盘价"
        assert bar["high"] >= bar["close"], "最高价应该 >= 收盘价"
        assert bar["low"] <= bar["open"], "最低价应该 <= 开盘价"
        assert bar["low"] <= bar["close"], "最低价应该 <= 收盘价"

        print(
            f"\n✓ 获取 {sample_stock_contract['symbol']} 日线数据: {data['count']} 根K线"
        )
        print(
            f"  最新K线: 日期={bar['date']}, "
            f"开={bar['open']}, 高={bar['high']}, "
            f"低={bar['low']}, 收={bar['close']}, 量={bar['volume']}"
        )

    def test_get_historical_bars_stock_hourly(self, http_client, sample_stock_contract):
        """测试获取股票小时线数据"""
        bar_request = {
            "contract": sample_stock_contract,
            "duration": "1 W",
            "bar_size": "1 hour",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        assert response.status_code == 200
        data = response.json()

        assert "bars" in data
        assert "count" in data
        assert data["count"] > 0

        print(
            f"\n✓ 获取 {sample_stock_contract['symbol']} 小时线数据: {data['count']} 根K线"
        )

    def test_get_historical_bars_stock_minute(self, http_client, sample_stock_contract):
        """测试获取股票分钟线数据"""
        bar_request = {
            "contract": sample_stock_contract,
            "duration": "1 D",
            "bar_size": "5 mins",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        assert response.status_code == 200
        data = response.json()

        assert "bars" in data
        assert "count" in data

        print(
            f"\n✓ 获取 {sample_stock_contract['symbol']} 5分钟线数据: {data['count']} 根K线"
        )

    def test_get_historical_bars_forex(self, http_client, sample_forex_contract):
        """测试获取外汇历史数据"""
        bar_request = {
            "contract": sample_forex_contract,
            "duration": "1 M",
            "bar_size": "1 day",
            "what_to_show": "MIDPOINT",
            "use_rth": False,  # 外汇24小时交易
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        assert response.status_code == 200
        data = response.json()

        assert "bars" in data
        assert "count" in data

        # 外汇数据可能需要特殊权限,如果没有数据则跳过验证
        if data["count"] > 0:
            bar = data["bars"][0]
            print(
                f"\n✓ 获取外汇 {sample_forex_contract['symbol']} 数据: {data['count']} 根K线"
            )
            print(f"  最新K线: 日期={bar['date']}, 收盘={bar['close']}")
        else:
            print(f"\n⚠ 外汇数据不可用(可能需要市场数据订阅)")
            print(f"  注意: 这不是代码错误,而是账户权限限制")

    def test_get_historical_bars_different_durations(
        self, http_client, sample_stock_contract
    ):
        """测试不同时间周期的历史数据"""
        durations = [
            ("1 D", "1 min", "1天1分钟线"),
            ("5 D", "1 hour", "5天小时线"),
            ("1 M", "1 day", "1月日线"),
            ("1 Y", "1 week", "1年周线"),
        ]

        print(f"\n测试不同时间周期的 {sample_stock_contract['symbol']} 数据:")

        for duration, bar_size, description in durations:
            bar_request = {
                "contract": sample_stock_contract,
                "duration": duration,
                "bar_size": bar_size,
                "what_to_show": "TRADES",
                "use_rth": True,
            }

            response = http_client.post(
                "/api/v1/market-data/historical-bars", json=bar_request
            )

            assert response.status_code == 200
            data = response.json()

            print(f"  ✓ {description}: {data['count']} 根K线")

    def test_get_historical_bars_different_data_types(
        self, http_client, sample_stock_contract
    ):
        """测试不同类型的数据 (TRADES, BID, ASK, MIDPOINT)"""
        what_to_show_options = ["TRADES", "BID", "ASK", "MIDPOINT"]

        print(f"\n测试不同数据类型的 {sample_stock_contract['symbol']} 日线:")

        for what_to_show in what_to_show_options:
            bar_request = {
                "contract": sample_stock_contract,
                "duration": "5 D",
                "bar_size": "1 day",
                "what_to_show": what_to_show,
                "use_rth": True,
            }

            response = http_client.post(
                "/api/v1/market-data/historical-bars", json=bar_request
            )

            # 有些数据类型可能不可用，所以我们接受200或500
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ {what_to_show}: {data['count']} 根K线")
            else:
                print(f"  ✗ {what_to_show}: 不可用或出错")

    def test_get_historical_bars_rth_vs_all_hours(
        self, http_client, sample_stock_contract
    ):
        """测试常规交易时段 vs 全天候数据"""
        # 常规交易时段
        rth_request = {
            "contract": sample_stock_contract,
            "duration": "5 D",
            "bar_size": "1 hour",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        rth_response = http_client.post(
            "/api/v1/market-data/historical-bars", json=rth_request
        )

        assert rth_response.status_code == 200
        rth_data = rth_response.json()

        # 全天候数据
        all_hours_request = {
            "contract": sample_stock_contract,
            "duration": "5 D",
            "bar_size": "1 hour",
            "what_to_show": "TRADES",
            "use_rth": False,
        }

        all_hours_response = http_client.post(
            "/api/v1/market-data/historical-bars", json=all_hours_request
        )

        assert all_hours_response.status_code == 200
        all_hours_data = all_hours_response.json()

        print(f"\n✓ RTH数据: {rth_data['count']} 根K线")
        print(f"✓ 全天候数据: {all_hours_data['count']} 根K线")

        # 全天候数据应该 >= 常规时段数据
        assert (
            all_hours_data["count"] >= rth_data["count"]
        ), "全天候数据量应该 >= 常规时段数据量"


class TestHistoricalBarsValidation:
    """测试历史数据的数据验证"""

    def test_bars_chronological_order(self, http_client, sample_stock_contract):
        """测试K线数据是否按时间顺序排列"""
        bar_request = {
            "contract": sample_stock_contract,
            "duration": "1 M",
            "bar_size": "1 day",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        assert response.status_code == 200
        data = response.json()

        # 检查日期是否按顺序
        dates = [bar["date"] for bar in data["bars"]]

        # 验证日期递增（允许相等，某些情况下可能有重复）
        for i in range(1, len(dates)):
            assert (
                dates[i] >= dates[i - 1]
            ), f"K线日期应该递增: {dates[i-1]} -> {dates[i]}"

        print(f"\n✓ K线数据按时间顺序排列")
        print(f"  日期范围: {dates[0]} 到 {dates[-1]}")

    def test_bars_data_completeness(self, http_client, sample_stock_contract):
        """测试K线数据完整性"""
        bar_request = {
            "contract": sample_stock_contract,
            "duration": "1 M",
            "bar_size": "1 day",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        assert response.status_code == 200
        data = response.json()

        # 检查每根K线的数据完整性
        for i, bar in enumerate(data["bars"]):
            # 所有字段都应该存在且不为None
            assert bar["date"] is not None, f"K线 {i} 日期为空"
            assert bar["open"] is not None, f"K线 {i} 开盘价为空"
            assert bar["high"] is not None, f"K线 {i} 最高价为空"
            assert bar["low"] is not None, f"K线 {i} 最低价为空"
            assert bar["close"] is not None, f"K线 {i} 收盘价为空"
            assert bar["volume"] is not None, f"K线 {i} 成交量为空"

            # 价格应该 > 0
            assert bar["open"] > 0, f"K线 {i} 开盘价应该 > 0"
            assert bar["high"] > 0, f"K线 {i} 最高价应该 > 0"
            assert bar["low"] > 0, f"K线 {i} 最低价应该 > 0"
            assert bar["close"] > 0, f"K线 {i} 收盘价应该 > 0"

            # 成交量应该 >= 0
            assert bar["volume"] >= 0, f"K线 {i} 成交量应该 >= 0"

        print(f"\n✓ 所有 {data['count']} 根K线数据完整且有效")


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_contract(self, http_client):
        """测试无效合约"""
        bar_request = {
            "contract": {
                "symbol": "INVALIDXYZ123",
                "sec_type": "STK",
                "exchange": "SMART",
                "currency": "USD",
            },
            "duration": "1 M",
            "bar_size": "1 day",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        # 应该返回500错误
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

        print(f"\n无效合约正确返回500: {data['detail']}")

    def test_invalid_bar_size(self, http_client, sample_stock_contract):
        """测试无效的K线周期"""
        bar_request = {
            "contract": sample_stock_contract,
            "duration": "1 M",
            "bar_size": "invalid_size",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        # 应该返回错误
        assert response.status_code in [422, 500]

        print(f"\n无效K线周期正确返回错误: {response.status_code}")

    def test_invalid_duration(self, http_client, sample_stock_contract):
        """测试无效的时间范围"""
        bar_request = {
            "contract": sample_stock_contract,
            "duration": "invalid_duration",
            "bar_size": "1 day",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        # 应该返回错误
        assert response.status_code in [422, 500]

        print(f"\n无效时间范围正确返回错误: {response.status_code}")

    def test_missing_required_fields(self, http_client):
        """测试缺少必填字段"""
        incomplete_request = {
            "contract": {
                "symbol": "AAPL",
                "sec_type": "STK",
                # exchange 和 currency 有默认值,所以会使用默认值
            },
            "duration": "1 M",
            "bar_size": "1 day",
            # what_to_show 和 use_rth 有默认值,所以会使用默认值
        }

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=incomplete_request
        )

        # 应该返回200,因为所有字段都有默认值
        assert response.status_code == 200
        data = response.json()
        assert "bars" in data
        assert "count" in data

        print(f"\n✓ 缺少非必填字段使用默认值: {data['count']} 根K线")


class TestPerformance:
    """测试性能和响应时间"""

    @pytest.mark.slow
    def test_large_data_request(self, http_client, sample_stock_contract):
        """测试大量数据请求"""
        import time

        bar_request = {
            "contract": sample_stock_contract,
            "duration": "2 Y",
            "bar_size": "1 day",
            "what_to_show": "TRADES",
            "use_rth": True,
        }

        start_time = time.time()

        response = http_client.post(
            "/api/v1/market-data/historical-bars", json=bar_request
        )

        end_time = time.time()
        elapsed = end_time - start_time

        assert response.status_code == 200
        data = response.json()

        print(f"\n✓ 大数据请求性能测试:")
        print(f"  数据量: {data['count']} 根K线")
        print(f"  耗时: {elapsed:.2f} 秒")
        print(f"  速度: {data['count']/elapsed:.0f} K线/秒")

        # 基本性能要求：不应该超过30秒
        assert elapsed < 30, f"请求耗时 {elapsed:.2f} 秒超过30秒阈值"


class TestMultipleSymbols:
    """测试多个不同股票的数据"""

    def test_multiple_stocks(self, http_client):
        """测试获取多个股票的历史数据"""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

        print(f"\n测试多个股票的历史数据:")

        for symbol in symbols:
            bar_request = {
                "contract": {
                    "symbol": symbol,
                    "sec_type": "STK",
                    "exchange": "SMART",
                    "currency": "USD",
                },
                "duration": "5 D",
                "bar_size": "1 day",
                "what_to_show": "TRADES",
                "use_rth": True,
            }

            response = http_client.post(
                "/api/v1/market-data/historical-bars", json=bar_request
            )

            assert response.status_code == 200
            data = response.json()
            assert data["count"] > 0

            latest_bar = data["bars"][-1] if data["bars"] else None
            if latest_bar:
                print(
                    f"  ✓ {symbol}: {data['count']} 根K线, "
                    f"最新收盘={latest_bar['close']}"
                )
