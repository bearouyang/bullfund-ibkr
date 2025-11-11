from fastapi import APIRouter, HTTPException
import logging
from fastapi import Request
from models import ScannerRequest
from ib_async import ScannerSubscription
from typing import List
from pydantic import BaseModel


class ScannerResultContract(BaseModel):
    con_id: int
    symbol: str
    sec_type: str
    exchange: str
    currency: str
    local_symbol: str


class ScannerResult(BaseModel):
    rank: int
    contract: ScannerResultContract
    distance: str
    benchmark: str
    projection: str
    legs: str


class ScannerResponse(BaseModel):
    results: List[ScannerResult]
    count: int


class ScannerParametersResponse(BaseModel):
    parameters: str


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/scan", response_model=ScannerResponse)
async def run_scanner(request: ScannerRequest, req: Request):
    """Run a market scanner to find contracts matching criteria."""
    try:
        ib = req.app.state.ib

        # Create scanner subscription
        sub = ScannerSubscription(
            instrument=request.instrument,
            locationCode=request.location_code,
            scanCode=request.scan_code,
        )

        # Set optional parameters
        if request.above_price is not None:
            sub.abovePrice = request.above_price
        if request.below_price is not None:
            sub.belowPrice = request.below_price
        if request.above_volume is not None:
            sub.aboveVolume = request.above_volume
        if request.market_cap_above is not None:
            sub.marketCapAbove = request.market_cap_above
        if request.market_cap_below is not None:
            sub.marketCapBelow = request.market_cap_below
        if request.number_of_rows:
            sub.numberOfRows = request.number_of_rows

        # Request scanner data
        scan_data = await ib.reqScannerDataAsync(sub)

        # Check if we got an empty result which might indicate an error
        # IB API sometimes returns empty list for invalid parameters instead of raising
        if scan_data is None or len(scan_data) == 0:
            raise HTTPException(
                status_code=400,
                detail="Scanner request failed - invalid parameters or no results",
            )

        results = [
            {
                "rank": item.rank,
                "contract": {
                    "con_id": item.contractDetails.contract.conId,
                    "symbol": item.contractDetails.contract.symbol,
                    "sec_type": item.contractDetails.contract.secType,
                    "exchange": item.contractDetails.contract.exchange,
                    "currency": item.contractDetails.contract.currency,
                    "local_symbol": item.contractDetails.contract.localSymbol,
                },
                "distance": item.distance,
                "benchmark": item.benchmark,
                "projection": item.projection,
                "legs": item.legsStr,
            }
            for item in scan_data
        ]

        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error running scanner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scanner-parameters", response_model=ScannerParametersResponse)
async def get_scanner_parameters(req: Request):
    """Get available scanner parameters."""
    try:
        ib = req.app.state.ib
        params = await ib.reqScannerParametersAsync()

        return {"parameters": params}
    except Exception as e:
        logger.error(f"Error getting scanner parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))
