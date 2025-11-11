from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional, List, Dict
import logging
import asyncio
import math
from pydantic import BaseModel

from fastapi import Request

# Pydantic Models for Response Bodies


class ManagedAccountsResponse(BaseModel):
    accounts: List[str]
    count: int


class AccountValue(BaseModel):
    value: str
    currency: str
    account: str


class AccountSummaryResponse(BaseModel):
    account: str
    summary: Dict[str, AccountValue]


class AccountValuesResponse(BaseModel):
    account: str
    values: Dict[str, List[AccountValue]]


class Contract(BaseModel):
    symbol: str
    sec_type: str
    exchange: str
    currency: str
    local_symbol: str
    con_id: int


class Position(BaseModel):
    account: str
    contract: Contract
    position: float
    avg_cost: float


class PositionsResponse(BaseModel):
    positions: List[Position]
    count: int


class PortfolioItem(BaseModel):
    account: str
    contract: Contract
    position: float
    market_price: float
    market_value: float
    average_cost: float
    unrealized_pnl: float
    realized_pnl: float


class PortfolioResponse(BaseModel):
    portfolio: List[PortfolioItem]
    count: int


class PnlResponse(BaseModel):
    account: str
    daily_pnl: float
    unrealized_pnl: float
    realized_pnl: float


class SinglePnlResponse(BaseModel):
    account: str
    con_id: int
    position: float
    daily_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    value: float


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/managed-accounts", response_model=ManagedAccountsResponse)
async def get_managed_accounts(request: Request):
    """Get list of managed accounts"""
    try:
        ib = request.app.state.ib
        accounts = ib.managedAccounts()
        return {"accounts": accounts, "count": len(accounts)}
    except Exception as e:
        logger.error(f"Error getting managed accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=AccountSummaryResponse)
async def get_account_summary(request: Request, account: Optional[str] = None):
    """Get account summary with key metrics"""
    try:
        ib = request.app.state.ib
        if account is None:
            accounts = ib.managedAccounts()
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts found")
            account = accounts[0]

        account_values = ib.accountValues(account)
        summary = {}
        for av in account_values:
            if av.tag in [
                "NetLiquidation",
                "TotalCashValue",
                "SettledCash",
                "AccruedCash",
                "BuyingPower",
                "EquityWithLoanValue",
                "PreviousDayEquityWithLoanValue",
                "GrossPositionValue",
                "RegTEquity",
                "RegTMargin",
                "SMA",
                "InitMarginReq",
                "MaintMarginReq",
                "AvailableFunds",
                "ExcessLiquidity",
                "Cushion",
                "FullInitMarginReq",
                "FullMaintMarginReq",
                "FullAvailableFunds",
                "FullExcessLiquidity",
                "LookAheadNextChange",
                "DayTradesRemaining",
            ]:
                summary[av.tag] = {
                    "value": av.value,
                    "currency": av.currency,
                    "account": av.account,
                }

        return {"account": account, "summary": summary}
    except Exception as e:
        logger.error(f"Error getting account summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/values", response_model=AccountValuesResponse)
async def get_account_values(request: Request, account: Optional[str] = None):
    """Get detailed account values"""
    try:
        ib = request.app.state.ib
        if account is None:
            accounts = ib.managedAccounts()
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts found")
            account = accounts[0]

        account_values = ib.accountValues(account)
        values_dict = {}
        for av in account_values:
            if av.tag not in values_dict:
                values_dict[av.tag] = []
            values_dict[av.tag].append(
                {"value": av.value, "currency": av.currency, "account": av.account}
            )

        return {"account": account, "values": values_dict}
    except Exception as e:
        logger.error(f"Error getting account values: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions", response_model=PositionsResponse)
async def get_positions(request: Request, account: Optional[str] = None):
    """Get current portfolio positions"""
    try:
        ib = request.app.state.ib
        positions = ib.positions()
        position_list = []
        for pos in positions:
            # 如果指定了account，只返回该账户的持仓
            if account and pos.account != account:
                continue
            position_list.append(
                {
                    "account": pos.account,
                    "contract": {
                        "symbol": pos.contract.symbol,
                        "sec_type": pos.contract.secType,
                        "exchange": pos.contract.exchange,
                        "currency": pos.contract.currency,
                        "local_symbol": pos.contract.localSymbol,
                        "con_id": pos.contract.conId,
                    },
                    "position": pos.position,
                    "avg_cost": pos.avgCost,
                }
            )

        return {"positions": position_list, "count": len(position_list)}
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(request: Request, account: Optional[str] = None):
    """Get portfolio items with P&L information"""
    try:
        ib = request.app.state.ib
        portfolio = ib.portfolio()
        portfolio_list = []
        for item in portfolio:
            # 如果指定了account，只返回该账户的投资组合
            if account and item.account != account:
                continue
            portfolio_list.append(
                {
                    "account": item.account,
                    "contract": {
                        "symbol": item.contract.symbol,
                        "sec_type": item.contract.secType,
                        "exchange": item.contract.exchange,
                        "currency": item.contract.currency,
                        "local_symbol": item.contract.localSymbol,
                        "con_id": item.contract.conId,
                    },
                    "position": item.position,
                    "market_price": item.marketPrice,
                    "market_value": item.marketValue,
                    "average_cost": item.averageCost,
                    "unrealized_pnl": item.unrealizedPNL,
                    "realized_pnl": item.realizedPNL,
                }
            )

        return {"portfolio": portfolio_list, "count": len(portfolio_list)}
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pnl", response_model=PnlResponse)
async def get_pnl(
    request: Request, account: Optional[str] = None, model_code: Optional[str] = None
):
    """Get real-time PnL for account."""
    try:
        ib = request.app.state.ib

        if account is None:
            accounts = ib.managedAccounts()
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts found")
            account = accounts[0]

        # Cancel any existing PnL subscription for this account
        # to avoid "key already exists" assertion error
        for pnl_obj in ib.pnl():
            if pnl_obj.account == account and pnl_obj.modelCode == (model_code or ""):
                ib.cancelPnL(account, modelCode=model_code or "")
                break

        # Request PnL
        pnl = ib.reqPnL(account, modelCode=model_code or "")

        # Wait a bit for data to populate
        await asyncio.sleep(1)

        # Helper function to handle NaN and None values
        def safe_float(value, default=0.0):
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return default
            return float(value)

        return {
            "account": account,
            "daily_pnl": safe_float(pnl.dailyPnL),
            "unrealized_pnl": safe_float(pnl.unrealizedPnL),
            "realized_pnl": safe_float(pnl.realizedPnL),
        }
    except Exception as e:
        logger.error(f"Error getting PnL: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=str(e) if str(e) else f"{type(e).__name__} occurred"
        )


@router.get("/pnl/single", response_model=SinglePnlResponse)
async def get_single_pnl(
    request: Request,
    account: Optional[str] = None,
    model_code: Optional[str] = None,
    con_id: Optional[int] = None,
):
    """Get real-time PnL for a single position."""
    try:
        ib = request.app.state.ib

        if account is None:
            accounts = ib.managedAccounts()
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts found")
            account = accounts[0]

        if con_id is None:
            raise HTTPException(status_code=400, detail="con_id is required")

        # Request single PnL
        pnl_single = ib.reqPnLSingle(account, modelCode=model_code or "", conId=con_id)

        # Wait a bit for data to populate
        await asyncio.sleep(1)

        # Helper function to handle NaN and None values
        def safe_float(value, default=0.0):
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return default
            return float(value)

        return {
            "account": account,
            "con_id": con_id,
            "position": safe_float(pnl_single.position),
            "daily_pnl": safe_float(pnl_single.dailyPnL),
            "unrealized_pnl": safe_float(pnl_single.unrealizedPnL),
            "realized_pnl": safe_float(pnl_single.realizedPnL),
            "value": safe_float(pnl_single.value),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting single PnL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream/pnl/{account}")
async def stream_pnl(websocket: WebSocket, account: str, request: Request):
    """WebSocket endpoint for streaming real-time PnL updates."""
    await websocket.accept()

    try:
        ib = request.app.state.ib
        pnl = ib.reqPnL(account, modelCode="")

        try:
            while True:
                data = {
                    "account": account,
                    "daily_pnl": pnl.dailyPnL,
                    "unrealized_pnl": pnl.unrealizedPnL,
                    "realized_pnl": pnl.realizedPnL,
                }
                await websocket.send_json(data)
                await asyncio.sleep(1)  # Update every second

        except WebSocketDisconnect:
            logger.info(f"PnL WebSocket disconnected for {account}")
        finally:
            ib.cancelPnL(pnl)
    except Exception as e:
        logger.error(f"PnL WebSocket error for {account}: {e}")
        await websocket.send_json({"error": str(e)})
        await websocket.close()
