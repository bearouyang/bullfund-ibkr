"""
Trading and order management endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import logging

from ib_async import Stock, Option, Future, Forex, Index, Bond, MarketOrder, LimitOrder, StopOrder, StopLimitOrder

from fastapi import Requestfrom models import ContractRequest, OrderRequest, SecType, OrderType, OrderAction

router = APIRouter()
logger = logging.getLogger(__name__)

def create_contract(contract_req: ContractRequest):
    if contract_req.sec_type == SecType.STOCK:
        return Stock(symbol=contract_req.symbol, exchange=contract_req.exchange, currency=contract_req.currency)
    elif contract_req.sec_type == SecType.OPTION:
        return Option(symbol=contract_req.symbol, lastTradeDateOrContractMonth=contract_req.last_trade_date, strike=contract_req.strike, right=contract_req.right, exchange=contract_req.exchange)
    elif contract_req.sec_type in [SecType.FOREX, SecType.CASH]:
        return Forex(contract_req.symbol)
    else:
        raise ValueError(f"Unsupported security type: {contract_req.sec_type}")

@router.post("/orders/place")
async def place_order(order_req: OrderRequest, request: Request):
    try:
        ib = request.app.state.ib
        contract = create_contract(order_req.contract)
        order = MarketOrder(order_req.action.value, order_req.quantity)

        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        trade = ib.placeOrder(qualified_contracts[0], order)
        return {"order_id": trade.order.orderId, "status": trade.orderStatus.status}
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/open")
async def get_open_orders(request: Request):
    ib = request.app.state.ib
    trades = await ib.openTradesAsync()
    return {"orders": trades, "count": len(trades)}

@router.get("/orders/all")
async def get_all_orders(request: Request):
    ib = request.app.state.ib
    trades = await ib.tradesAsync()
    return {"orders": trades, "count": len(trades)}

@router.get("/executions")
async def get_executions(request: Request):
    ib = request.app.state.ib
    fills = await ib.fillsAsync()
    return {"executions": fills, "count": len(fills)}

@router.post("/contract/qualify")
async def qualify_contract(contract_req: ContractRequest, request: Request):
    ib = request.app.state.ib
    contract = create_contract(contract_req)
    qualified_contracts = await ib.qualifyContractsAsync(contract)
    if not qualified_contracts:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"contracts": qualified_contracts, "count": len(qualified_contracts)}
