from fastapi import APIRouter, HTTPException
import logging
from fastapi import Request
from models import BarDataRequest
from routers.trading import create_contract

router = APIRouter()
logger = logging.getLogger(__name__)


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
