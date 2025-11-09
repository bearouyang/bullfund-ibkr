from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class OrderAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP LMT"
    TRAILING_STOP = "TRAIL"

class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    GTD = "GTD"

class SecType(str, Enum):
    STOCK = "STK"
    OPTION = "OPT"
    FUTURE = "FUT"
    FOREX = "CASH"
    CASH = "CASH"  # Alias for FOREX
    INDEX = "IND"
    CFD = "CFD"
    COMMODITY = "CMDTY"
    BOND = "BOND"
    FUND = "FUND"

# Contract Models
class ContractRequest(BaseModel):
    symbol: str
    sec_type: SecType = SecType.STOCK
    exchange: str = "SMART"
    currency: str = "USD"
    last_trade_date: Optional[str] = None
    strike: Optional[float] = None
    right: Optional[str] = None  # "C" or "P" for options
    multiplier: Optional[str] = None
    primary_exchange: Optional[str] = None

# Order Models
class OrderRequest(BaseModel):
    contract: ContractRequest
    action: OrderAction
    order_type: OrderType
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    account: Optional[str] = None
    transmit: bool = True
    parent_id: Optional[int] = None
    oca_group: Optional[str] = None

class OrderModifyRequest(BaseModel):
    order_id: int
    quantity: Optional[float] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

class OrderCancelRequest(BaseModel):
    order_id: int

# Market Data Models
class MarketDataRequest(BaseModel):
    contract: ContractRequest
    generic_tick_list: str = ""
    snapshot: bool = False
    regulatory_snapshot: bool = False

class BarDataRequest(BaseModel):
    contract: ContractRequest
    bar_size: str = "1 min"  # 1 sec, 5 secs, 10 secs, 15 secs, 30 secs, 1 min, 2 mins, 3 mins, 5 mins, 10 mins, 15 mins, 20 mins, 30 mins, 1 hour, 2 hours, 3 hours, 4 hours, 8 hours, 1 day, 1 week, 1 month
    duration: str = "1 D"  # S (seconds), D (days), W (weeks), M (months), Y (years)
    what_to_show: str = "TRADES"  # TRADES, MIDPOINT, BID, ASK, BID_ASK, HISTORICAL_VOLATILITY, OPTION_IMPLIED_VOLATILITY
    use_rth: bool = True
    end_datetime: Optional[str] = None

class TickDataRequest(BaseModel):
    contract: ContractRequest
    tick_type: str = "Last"  # Last, AllLast, BidAsk, MidPoint
    number_of_ticks: int = 100
    ignore_size: bool = False

# Account Models
class AccountSummaryRequest(BaseModel):
    account: Optional[str] = "All"
    tags: str = "AccountType,NetLiquidation,TotalCashValue,SettledCash,AccruedCash,BuyingPower,EquityWithLoanValue,PreviousDayEquityWithLoanValue,GrossPositionValue,ReqTEquity,ReqTMargin,SMA,InitMarginReq,MaintMarginReq,AvailableFunds,ExcessLiquidity,Cushion,FullInitMarginReq,FullMaintMarginReq,FullAvailableFunds,FullExcessLiquidity,LookAheadNextChange,LookAheadInitMarginReq,LookAheadMaintMarginReq,LookAheadAvailableFunds,LookAheadExcessLiquidity,HighestSeverity,DayTradesRemaining,Leverage"

# Fundamental Data Models
class FundamentalDataRequest(BaseModel):
    contract: ContractRequest
    report_type: str = "ReportsFinSummary"  # ReportSnapshot, ReportsFinSummary, ReportRatios, ReportsFinStatements, RESC, CalendarReport

class NewsRequest(BaseModel):
    contract: Optional[ContractRequest] = None
    provider_codes: str = "BRFUPDN+DJNL"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_results: int = 10

class HistogramRequest(BaseModel):
    contract: ContractRequest
    use_rth: bool = True
    period: str = "1 day"

# Scanner Models
class ScannerRequest(BaseModel):
    instrument: str = "STK"
    location_code: str = "STK.US.MAJOR"
    scan_code: str = "TOP_PERC_GAIN"
    above_price: Optional[float] = None
    below_price: Optional[float] = None
    above_volume: Optional[int] = None
    market_cap_above: Optional[float] = None
    market_cap_below: Optional[float] = None
    moody_rating_above: Optional[str] = None
    moody_rating_below: Optional[str] = None
    sp_rating_above: Optional[str] = None
    sp_rating_below: Optional[str] = None
    maturity_date_above: Optional[str] = None
    maturity_date_below: Optional[str] = None
    coupon_rate_above: Optional[float] = None
    coupon_rate_below: Optional[float] = None
    exclude_convertible: Optional[bool] = None
    scanner_setting_pairs: Optional[str] = None
    stock_type_filter: Optional[str] = None
    number_of_rows: int = 50

# Response Models
class ConnectionStatus(BaseModel):
    connected: bool
    client_id: int
    host: str
    port: int

class PositionResponse(BaseModel):
    account: str
    symbol: str
    sec_type: str
    position: float
    avg_cost: float
    market_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None

class OrderResponse(BaseModel):
    order_id: int
    perm_id: int
    client_id: int
    symbol: str
    sec_type: str
    action: str
    order_type: str
    total_quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    status: str
    filled: float
    remaining: float
    avg_fill_price: float
    last_fill_price: float
    why_held: str

class ExecutionResponse(BaseModel):
    exec_id: str
    time: str
    account: str
    symbol: str
    sec_type: str
    side: str
    shares: float
    price: float
    perm_id: int
    client_id: int
    order_id: int
    liquidation: int
    cum_qty: float
    avg_price: float

class TickerResponse(BaseModel):
    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    bid_size: Optional[float] = None
    ask_size: Optional[float] = None
    last_size: Optional[float] = None
    volume: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    open: Optional[float] = None
    halted: Optional[float] = None

class BarResponse(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    average: float
    bar_count: int

class AccountValueResponse(BaseModel):
    account: str
    tag: str
    value: str
    currency: str
    model_code: str
