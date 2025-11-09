from fastapi import APIRouter, HTTPException
import logging
from fastapi import Requestfrom models import BarDataRequest
from routers.trading import create_contract

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/historical-bars")
async def get_historical_bars(request: BarDataRequest, req: Request):
    """Get historical bar data for a contract (using the sync wrapper)."""
    try:
        contract = create_contract(request.contract)
        
        ib = req.app.state.ib
        bars = await ib.reqHistoricalDataAsync(            contract=contract,
            duration=request.duration,
            barSizeSetting=request.bar_size,
            whatToShow=request.what_to_show,
            useRTH=request.use_rth
        )
        
        logger.info(f"Received {len(bars)} bars from IBKR for {contract.symbol}")

        bar_list = [
            {
                "date": str(bar.date),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume
            }
            for bar in bars
        ]
        
        return {
            "bars": bar_list,
            "count": len(bar_list)
        }

    except Exception as e:
        logger.error(f"API Error getting historical bars: {e}")
        raise HTTPException(status_code=500, detail=str(e))
