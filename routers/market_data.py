from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import logging
import asyncio
from typing import Dict, Set, List, Any, Optional
from fastapi import Request
from models import BarDataRequest, MarketDataRequest, TickDataRequest, ContractRequest
from routers.trading import create_contract
import math
from pydantic import BaseModel


class Bar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class HistoricalBarsResponse(BaseModel):
    bars: List[Bar]
    count: int

class RealtimeBar(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    wap: float
    count: int

class RealtimeBarsResponse(BaseModel):
    bars: List[RealtimeBar]
    count: int

class MarketDataResponse(BaseModel):
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

class Tick(BaseModel):
    time: str
    price: Optional[float] = None
    size: Optional[float] = None
    tickAttribLast: Optional[str] = None
    exchange: Optional[str] = None
    specialConditions: Optional[str] = None

class TickDataResponse(BaseModel):
    ticks: List[Tick]
    count: int
    
class MarketDepthLevel(BaseModel):
    position: int
    price: float
    size: float
    market_maker: str

class MarketDepthResponse(BaseModel):
    symbol: str
    bids: List[MarketDepthLevel]
    asks: List[MarketDepthLevel]

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active subscriptions
active_subscriptions: Dict[str, Set[WebSocket]] = {}


def clean_float(value) -> float | None:
    """Convert NaN and inf to None for JSON serialization."""
    if value is None:
        return None
    try:
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except (TypeError, ValueError):
        return None


@router.post("/historical-bars", response_model=HistoricalBarsResponse)
async def get_historical_bars(request: BarDataRequest, req: Request):
    """Get historical bar data for a contract."""
    error_occurred = False
    error_message = None

    def error_handler(reqId, errorCode, errorString, contract):
        nonlocal error_occurred, error_message
        # Ignore connection status messages (2104, 2105, 2106, 2107, 2108, 2119)
        # Ignore market data farm connection messages (2103, 2106)
        if errorCode in [2103, 2104, 2105, 2106, 2107, 2108, 2119, 2157, 2158]:
            logger.info(f"IBKR Status for reqId {reqId}: {errorCode} - {errorString}")
            return
        # Error codes that indicate actual errors
        # 162 = No market data permissions
        # 200 = No security definition found
        # 366 = No historical data query found (invalid parameters)
        # >= 1000 = Errors
        if errorCode >= 1000 or errorCode in [162, 200, 366]:
            error_occurred = True
            error_message = f"Error {errorCode}: {errorString}"
            logger.error(f"IBKR Error for reqId {reqId}: {error_message}")

    try:
        contract = create_contract(request.contract)
        ib = req.app.state.ib
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        qualified_contracts = [c for c in qualified_contracts if c.conId != 0]
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")
        contract = qualified_contracts[0]

        ib = req.app.state.ib

        # Subscribe to error events temporarily
        ib.errorEvent += error_handler

        try:
            # Add timeout to prevent hanging on invalid requests
            bars = await asyncio.wait_for(
                ib.reqHistoricalDataAsync(
                    contract=contract,
                    endDateTime="",  # Empty string means current time
                    durationStr=request.duration,
                    barSizeSetting=request.bar_size,
                    whatToShow=request.what_to_show,
                    useRTH=request.use_rth,
                ),
                timeout=30.0,  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Historical data request timed out for {contract.symbol}")
            if error_occurred:
                raise HTTPException(status_code=500, detail=error_message)
            raise HTTPException(status_code=500, detail="Request timed out")
        finally:
            # Unsubscribe from error events
            ib.errorEvent -= error_handler

        # Check if error occurred during the request
        if error_occurred:
            raise HTTPException(status_code=500, detail=error_message)

        logger.info(f"Received {len(bars)} bars from IBKR for {contract.symbol}")

        bar_list = [
            {
                "date": str(bar.date),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ]

        return {"bars": bar_list, "count": len(bar_list)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API Error getting historical bars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/realtime-bars", response_model=RealtimeBarsResponse)
async def get_realtime_bars(request: BarDataRequest, req: Request):
    """Get real-time 5-second bars for a contract."""
    try:
        contract = create_contract(request.contract)
        ib = req.app.state.ib

        bars = ib.reqRealTimeBars(
            contract=contract,
            barSize=5,  # Only 5 seconds is supported
            whatToShow=request.what_to_show,
            useRTH=request.use_rth,
        )

        # Wait a bit to get some bars
        await asyncio.sleep(2)

        bar_list = [
            {
                "time": str(bar.time),
                "open": bar.open_,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "wap": bar.wap,
                "count": bar.count,
            }
            for bar in bars
        ]

        return {"bars": bar_list, "count": len(bar_list)}
    except Exception as e:
        logger.error(f"Error getting real-time bars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-data", response_model=MarketDataResponse)
async def get_market_data(request: MarketDataRequest, req: Request):
    """Get market data snapshot for a contract."""
    try:
        contract = create_contract(request.contract)
        ib = req.app.state.ib

        # Qualify the contract first
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")

        contract = qualified_contracts[0]

        # Request market data
        ticker = ib.reqMktData(
            contract,
            genericTickList=request.generic_tick_list,
            snapshot=request.snapshot,
            regulatorySnapshot=request.regulatory_snapshot,
        )

        # Wait for data to populate
        await asyncio.sleep(2)

        result = {
            "symbol": contract.symbol,
            "bid": clean_float(ticker.bid),
            "ask": clean_float(ticker.ask),
            "last": clean_float(ticker.last),
            "bid_size": clean_float(ticker.bidSize),
            "ask_size": clean_float(ticker.askSize),
            "last_size": clean_float(ticker.lastSize),
            "volume": clean_float(ticker.volume),
            "high": clean_float(ticker.high),
            "low": clean_float(ticker.low),
            "close": clean_float(ticker.close),
            "open": clean_float(ticker.open),
            "halted": clean_float(ticker.halted),
        }

        logger.debug(f"Market data result: {result}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tick-data", response_model=TickDataResponse)
async def get_tick_data(request: TickDataRequest, req: Request):
    """Get historical tick data for a contract."""
    try:
        contract = create_contract(request.contract)
        ib = req.app.state.ib

        # Qualify the contract first
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")

        contract = qualified_contracts[0]

        # Request tick data with timeout
        try:
            ticks = await asyncio.wait_for(
                ib.reqHistoricalTicksAsync(
                    contract,
                    startDateTime="",
                    endDateTime="",
                    numberOfTicks=request.number_of_ticks,
                    whatToShow=request.tick_type,
                    useRth=True,
                    ignoreSize=request.ignore_size,
                ),
                timeout=30.0,  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Tick data request timed out for {contract.symbol}")
            return {"ticks": [], "count": 0}

        tick_list = [
            {
                "time": str(tick.time),
                "price": tick.price if hasattr(tick, "price") else None,
                "size": tick.size if hasattr(tick, "size") else None,
                "tickAttribLast": (
                    str(tick.tickAttribLast)
                    if hasattr(tick, "tickAttribLast")
                    else None
                ),
                "exchange": tick.exchange if hasattr(tick, "exchange") else None,
                "specialConditions": (
                    tick.specialConditions
                    if hasattr(tick, "specialConditions")
                    else None
                ),
            }
            for tick in ticks
        ]

        return {"ticks": tick_list, "count": len(tick_list)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tick data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-depth", response_model=MarketDepthResponse)
async def get_market_depth(contract_req: MarketDataRequest, req: Request):
    """Get market depth (Level 2) data for a contract."""
    try:
        contract = create_contract(contract_req.contract)
        ib = req.app.state.ib

        # Qualify the contract first
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")

        contract = qualified_contracts[0]

        # Request market depth
        ticker = ib.reqMktDepth(contract)

        # Wait for data to populate
        await asyncio.sleep(2)

        dom_bids = (
            [
                {
                    "position": i,
                    "price": level.price,
                    "size": level.size,
                    "market_maker": level.marketMaker,
                }
                for i, level in enumerate(ticker.domBids)
            ]
            if ticker.domBids
            else []
        )

        dom_asks = (
            [
                {
                    "position": i,
                    "price": level.price,
                    "size": level.size,
                    "market_maker": level.marketMaker,
                }
                for i, level in enumerate(ticker.domAsks)
            ]
            if ticker.domAsks
            else []
        )

        return {
            "symbol": contract.symbol,
            "bids": dom_bids,
            "asks": dom_asks,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market depth: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream/market-data/{symbol}")
async def stream_market_data(websocket: WebSocket, symbol: str):
    """WebSocket endpoint for streaming real-time market data (event-driven)."""
    await websocket.accept()

    try:
        ib = websocket.app.state.ib
        contract = create_contract(ContractRequest(symbol=symbol))

        # Qualify the contract
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            await websocket.send_json({"error": "Contract not found"})
            await websocket.close()
            return

        contract = qualified_contracts[0]
        ticker = ib.reqMktData(contract, "", False, False)

        # Track this subscription
        if symbol not in active_subscriptions:
            active_subscriptions[symbol] = set()
        active_subscriptions[symbol].add(websocket)

        loop = asyncio.get_running_loop()

        def on_update(_):
            """Send updates to the client when ticker changes."""
            data = {
                "symbol": contract.symbol,
                "time": str(ticker.time),
                "bid": clean_float(ticker.bid),
                "ask": clean_float(ticker.ask),
                "last": clean_float(ticker.last),
                "volume": clean_float(ticker.volume),
                "high": clean_float(ticker.high),
                "low": clean_float(ticker.low),
                "close": clean_float(ticker.close),
            }
            # Schedule send in the event loop (non-blocking)
            loop.create_task(websocket.send_json(data))

        # Subscribe to ticker update events (event-driven push)
        ticker.updateEvent += on_update

        try:
            # Keep the connection open; react to client pings/messages
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {symbol}")
        finally:
            # Unsubscribe and clean up
            ticker.updateEvent -= on_update
            if symbol in active_subscriptions:
                active_subscriptions[symbol].discard(websocket)
                if not active_subscriptions[symbol]:
                    del active_subscriptions[symbol]
                    ib.cancelMktData(contract)
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        finally:
            await websocket.close()
