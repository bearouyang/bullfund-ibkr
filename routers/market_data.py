from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import logging
import asyncio
from typing import Dict, Set
from fastapi import Request
from models import BarDataRequest, MarketDataRequest, TickDataRequest, ContractRequest
from routers.trading import create_contract
from ib_async import util

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active subscriptions
active_subscriptions: Dict[str, Set[WebSocket]] = {}


@router.post("/historical-bars")
async def get_historical_bars(request: BarDataRequest, req: Request):
    """Get historical bar data for a contract."""
    error_occurred = False
    error_message = None

    def error_handler(reqId, errorCode, errorString, contract):
        nonlocal error_occurred, error_message
        # Error codes < 1000 are warnings, >= 1000 are errors
        if errorCode >= 1000 or errorCode == 200:  # 200 = No security definition found
            error_occurred = True
            error_message = f"Error {errorCode}: {errorString}"
            logger.error(f"IBKR Error for reqId {reqId}: {error_message}")

    try:
        contract = create_contract(request.contract)

        ib = req.app.state.ib

        # Subscribe to error events temporarily
        ib.errorEvent += error_handler

        try:
            bars = await ib.reqHistoricalDataAsync(
                contract=contract,
                endDateTime="",  # Empty string means current time
                durationStr=request.duration,
                barSizeSetting=request.bar_size,
                whatToShow=request.what_to_show,
                useRTH=request.use_rth,
            )
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


@router.post("/realtime-bars")
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


@router.post("/market-data")
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
        
        return {
            "symbol": contract.symbol,
            "bid": ticker.bid,
            "ask": ticker.ask,
            "last": ticker.last,
            "bid_size": ticker.bidSize,
            "ask_size": ticker.askSize,
            "last_size": ticker.lastSize,
            "volume": ticker.volume,
            "high": ticker.high,
            "low": ticker.low,
            "close": ticker.close,
            "open": ticker.open,
            "halted": ticker.halted,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tick-data")
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
        
        # Request tick data
        ticks = await ib.reqHistoricalTicksAsync(
            contract,
            startDateTime="",
            endDateTime="",
            numberOfTicks=request.number_of_ticks,
            whatToShow=request.tick_type,
            useRth=True,
            ignoreSize=request.ignore_size,
        )
        
        tick_list = [
            {
                "time": str(tick.time),
                "price": tick.price if hasattr(tick, "price") else None,
                "size": tick.size if hasattr(tick, "size") else None,
                "tickAttribLast": str(tick.tickAttribLast) if hasattr(tick, "tickAttribLast") else None,
                "exchange": tick.exchange if hasattr(tick, "exchange") else None,
                "specialConditions": tick.specialConditions if hasattr(tick, "specialConditions") else None,
            }
            for tick in ticks
        ]
        
        return {"ticks": tick_list, "count": len(tick_list)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tick data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-depth")
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
        
        dom_bids = [
            {"position": i, "price": level.price, "size": level.size, "market_maker": level.marketMaker}
            for i, level in enumerate(ticker.domBids)
        ] if ticker.domBids else []
        
        dom_asks = [
            {"position": i, "price": level.price, "size": level.size, "market_maker": level.marketMaker}
            for i, level in enumerate(ticker.domAsks)
        ] if ticker.domAsks else []
        
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
async def stream_market_data(websocket: WebSocket, symbol: str, req: Request):
    """WebSocket endpoint for streaming real-time market data."""
    await websocket.accept()
    
    try:
        ib = req.app.state.ib
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
        
        try:
            while True:
                # Send current ticker data
                data = {
                    "symbol": contract.symbol,
                    "time": str(ticker.time),
                    "bid": ticker.bid,
                    "ask": ticker.ask,
                    "last": ticker.last,
                    "volume": ticker.volume,
                    "high": ticker.high,
                    "low": ticker.low,
                    "close": ticker.close,
                }
                await websocket.send_json(data)
                await asyncio.sleep(1)  # Update every second
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {symbol}")
        finally:
            # Clean up subscription
            if symbol in active_subscriptions:
                active_subscriptions[symbol].discard(websocket)
                if not active_subscriptions[symbol]:
                    del active_subscriptions[symbol]
                    ib.cancelMktData(contract)
    except Exception as e:
        logger.error(f"WebSocket error for {symbol}: {e}")
        await websocket.send_json({"error": str(e)})
        await websocket.close()
