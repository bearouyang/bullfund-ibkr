"""
Account and portfolio management endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import logging
import math

from fastapi import Request
from models import (
    AccountValueResponse,
    PositionResponse,
    AccountSummaryRequest
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/managed-accounts")
async def get_managed_accounts(request: Request):
    """Get list of managed accounts"""
    try:
        ib = request.app.state.ib
        accounts = await ib.managedAccountsAsync()
        return {
            "accounts": accounts,
            "count": len(accounts)
        }
    except Exception as e:
        logger.error(f"Error getting managed accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_account_summary(request: Request, account: Optional[str] = None):
    """Get account summary with key metrics"""
    try:
        ib = request.app.state.ib
        if account is None:
            accounts = await ib.managedAccountsAsync()
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts found")
            account = accounts[0]
        
        account_values = await ib.accountValuesAsync(account)
        summary = {}
        for av in account_values:
            if av.tag in [
                'NetLiquidation', 'TotalCashValue', 'SettledCash', 'AccruedCash',
                'BuyingPower', 'EquityWithLoanValue', 'PreviousDayEquityWithLoanValue',
                'GrossPositionValue', 'RegTEquity', 'RegTMargin', 'SMA', 'InitMarginReq',
                'MaintMarginReq', 'AvailableFunds', 'ExcessLiquidity', 'Cushion',
                'FullInitMarginReq', 'FullMaintMarginReq', 'FullAvailableFunds',
                'FullExcessLiquidity', 'LookAheadNextChange', 'DayTradesRemaining'
            ]:
                summary[av.tag] = {
                    "value": av.value,
                    "currency": av.currency,
                    "account": av.account
                }
        
        return {
            "account": account,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting account summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/values")
async def get_account_values(request: Request, account: Optional[str] = None):
    """Get detailed account values"""
    try:
        ib = request.app.state.ib
        if account is None:
            accounts = await ib.managedAccountsAsync()
            if not accounts:
                raise HTTPException(status_code=404, detail="No accounts found")
            account = accounts[0]
        
        account_values = await ib.accountValuesAsync(account)
        values_dict = {}
        for av in account_values:
            if av.tag not in values_dict:
                values_dict[av.tag] = []
            values_dict[av.tag].append({
                "value": av.value,
                "currency": av.currency,
                "account": av.account
            })
        
        return {
            "account": account,
            "values": values_dict
        }
    except Exception as e:
        logger.error(f"Error getting account values: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions")
async def get_positions(request: Request, account: Optional[str] = None):
    """Get current portfolio positions"""
    try:
        ib = request.app.state.ib
        positions = await ib.positionsAsync(account)
        position_list = []
        for pos in positions:
            position_list.append({
                "account": pos.account,
                "contract": {
                    "symbol": pos.contract.symbol,
                    "sec_type": pos.contract.secType,
                    "exchange": pos.contract.exchange,
                    "currency": pos.contract.currency,
                    "local_symbol": pos.contract.localSymbol,
                    "con_id": pos.contract.conId
                },
                "position": pos.position,
                "avg_cost": pos.avgCost
            })
        
        return {
            "positions": position_list,
            "count": len(position_list)
        }
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
async def get_portfolio(request: Request, account: Optional[str] = None):
    """Get portfolio items with P&L information"""
    try:
        ib = request.app.state.ib
        portfolio = await ib.portfolioAsync(account)
        portfolio_list = []
        for item in portfolio:
            portfolio_list.append({
                "account": item.account,
                "contract": {
                    "symbol": item.contract.symbol,
                    "sec_type": item.contract.secType,
                    "exchange": item.contract.exchange,
                    "currency": item.contract.currency,
                    "local_symbol": item.contract.localSymbol,
                    "con_id": item.contract.conId
                },
                "position": item.position,
                "market_price": item.marketPrice,
                "market_value": item.marketValue,
                "average_cost": item.averageCost,
                "unrealized_pnl": item.unrealizedPNL,
                "realized_pnl": item.realizedPNL
            })
        
        return {
            "portfolio": portfolio_list,
            "count": len(portfolio_list)
        }
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
