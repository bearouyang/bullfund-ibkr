from fastapi import APIRouter, HTTPException
import logging
from typing import List, Dict, Any

from ib_async import (
    Stock,
    Option,
    Forex,
    Future,
    Index,
    CFD,
    Bond,
    MarketOrder,
    LimitOrder,
    StopOrder,
    StopLimitOrder,
    Order,
)

from fastapi import Request
from models import (
    ContractRequest,
    OrderRequest,
    OrderModifyRequest,
    OrderCancelRequest,
    SecType,
    OrderType,
)
from pydantic import BaseModel


class QualifiedContract(BaseModel):
    conId: int
    symbol: str
    secType: str
    primaryExchange: str
    currency: str


class QualifiedContractsResponse(BaseModel):
    contracts: List[QualifiedContract]
    count: int


class PlaceOrderResponse(BaseModel):
    order_id: int
    status: str
    perm_id: int


class OpenOrdersResponse(BaseModel):
    orders: List[Any]  # Trade objects from ib_async
    count: int


class AllOrdersResponse(BaseModel):
    orders: List[Any]  # Trade objects from ib_async
    count: int


class ExecutionsResponse(BaseModel):
    executions: List[Any]  # Fill objects from ib_async
    count: int


class ModifyOrderResponse(BaseModel):
    order_id: int
    status: str


class CancelOrderResponse(BaseModel):
    order_id: int
    status: str


class CancelAllOrdersResponse(BaseModel):
    status: str


class GetOrderResponse(BaseModel):
    order_id: int
    perm_id: int
    status: str
    filled: float
    remaining: float
    avg_fill_price: float
    contract: Dict[str, Any]
    order: Dict[str, Any]


router = APIRouter()
logger = logging.getLogger(__name__)


def create_contract(contract_req: ContractRequest):
    if contract_req.sec_type == SecType.STOCK:
        return Stock(
            symbol=contract_req.symbol,
            exchange=contract_req.exchange,
            currency=contract_req.currency,
        )
    elif contract_req.sec_type == SecType.OPTION:
        return Option(
            symbol=contract_req.symbol,
            lastTradeDateOrContractMonth=contract_req.last_trade_date,
            strike=contract_req.strike,
            right=contract_req.right,
            exchange=contract_req.exchange,
        )
    elif contract_req.sec_type == SecType.CASH:
        return Forex(contract_req.symbol)
    elif contract_req.sec_type == SecType.FUTURE:
        return Future(
            symbol=contract_req.symbol,
            lastTradeDateOrContractMonth=contract_req.last_trade_date,
            exchange=contract_req.exchange,
            currency=contract_req.currency,
        )
    elif contract_req.sec_type == SecType.INDEX:
        return Index(
            symbol=contract_req.symbol,
            exchange=contract_req.exchange,
            currency=contract_req.currency,
        )
    elif contract_req.sec_type == SecType.CFD:
        return CFD(
            symbol=contract_req.symbol,
            exchange=contract_req.exchange,
            currency=contract_req.currency,
        )
    elif contract_req.sec_type == SecType.BOND:
        return Bond(
            symbol=contract_req.symbol,
            exchange=contract_req.exchange,
            currency=contract_req.currency,
        )
    else:
        raise ValueError(f"Unsupported security type: {contract_req.sec_type}")


def create_order(order_req: OrderRequest):
    """Create an order based on the order request."""
    if order_req.order_type == OrderType.MARKET:
        order = MarketOrder(order_req.action.value, order_req.quantity)
    elif order_req.order_type == OrderType.LIMIT:
        if order_req.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        order = LimitOrder(
            order_req.action.value, order_req.quantity, order_req.limit_price
        )
    elif order_req.order_type == OrderType.STOP:
        if order_req.stop_price is None:
            raise ValueError("stop_price is required for stop orders")
        order = StopOrder(
            order_req.action.value, order_req.quantity, order_req.stop_price
        )
    elif order_req.order_type == OrderType.STOP_LIMIT:
        if order_req.limit_price is None or order_req.stop_price is None:
            raise ValueError(
                "limit_price and stop_price are required for stop-limit orders"
            )
        order = StopLimitOrder(
            order_req.action.value,
            order_req.quantity,
            order_req.limit_price,
            order_req.stop_price,
        )
    elif order_req.order_type == OrderType.TRAILING_STOP:
        if order_req.stop_price is None:
            raise ValueError(
                "stop_price (trailing amount) is required for trailing stop orders"
            )
        order = Order()
        order.action = order_req.action.value
        order.totalQuantity = order_req.quantity
        order.orderType = "TRAIL"
        order.trailingPercent = (
            order_req.stop_price
        )  # Use stop_price as trailing percent
    else:
        raise ValueError(f"Unsupported order type: {order_req.order_type}")

    # Set common order properties
    order.tif = order_req.time_in_force.value
    order.transmit = order_req.transmit

    if order_req.account:
        order.account = order_req.account
    if order_req.parent_id:
        order.parentId = order_req.parent_id
    if order_req.oca_group:
        order.ocaGroup = order_req.oca_group

    return order


@router.post("/orders/place", response_model=PlaceOrderResponse)
async def place_order(order_req: OrderRequest, request: Request):
    """Place an order."""
    try:
        ib = request.app.state.ib
        contract = create_contract(order_req.contract)
        order = create_order(order_req)

        qualified_contracts = await ib.qualifyContractsAsync(contract)
        # Filter out contracts that weren't actually qualified (conId == 0)
        qualified_contracts = [c for c in qualified_contracts if c.conId != 0]
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")

        trade = ib.placeOrder(qualified_contracts[0], order)
        return {
            "order_id": trade.order.orderId,
            "status": trade.orderStatus.status,
            "perm_id": trade.order.permId,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/open", response_model=OpenOrdersResponse)
async def get_open_orders(request: Request):
    ib = request.app.state.ib
    trades = ib.openTrades()
    return {"orders": trades, "count": len(trades)}


@router.get("/orders/all", response_model=AllOrdersResponse)
async def get_all_orders(request: Request):
    ib = request.app.state.ib
    trades = ib.trades()
    return {"orders": trades, "count": len(trades)}


@router.get("/executions", response_model=ExecutionsResponse)
async def get_executions(request: Request):
    ib = request.app.state.ib
    fills = ib.fills()
    return {"executions": fills, "count": len(fills)}


@router.post("/contract/qualify", response_model=QualifiedContractsResponse)
async def qualify_contract(contract_req: ContractRequest, request: Request):
    try:
        ib = request.app.state.ib
        contract = create_contract(contract_req)
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        # Filter out contracts that weren't actually qualified (conId == 0)
        qualified_contracts = [c for c in qualified_contracts if c.conId != 0]
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")
        return {"contracts": qualified_contracts, "count": len(qualified_contracts)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error qualifying contract: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/modify", response_model=ModifyOrderResponse)
async def modify_order(modify_req: OrderModifyRequest, request: Request):
    """Modify an existing order."""
    try:
        ib = request.app.state.ib

        # Find the trade by order_id
        trade = None
        for t in ib.trades():
            if t.order.orderId == modify_req.order_id:
                trade = t
                break

        if not trade:
            raise HTTPException(status_code=404, detail="Order not found")

        # Modify order parameters
        if modify_req.quantity is not None:
            trade.order.totalQuantity = modify_req.quantity
        if modify_req.limit_price is not None:
            trade.order.lmtPrice = modify_req.limit_price
        if modify_req.stop_price is not None:
            trade.order.auxPrice = modify_req.stop_price

        # Place the modified order
        modified_trade = ib.placeOrder(trade.contract, trade.order)

        return {
            "order_id": modified_trade.order.orderId,
            "status": modified_trade.orderStatus.status,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modifying order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/cancel", response_model=CancelOrderResponse)
async def cancel_order(cancel_req: OrderCancelRequest, request: Request):
    """Cancel an order."""
    try:
        ib = request.app.state.ib

        # Find the trade by order_id
        trade = None
        for t in ib.trades():
            if t.order.orderId == cancel_req.order_id:
                trade = t
                break

        if not trade:
            raise HTTPException(status_code=404, detail="Order not found")

        # Cancel the order
        ib.cancelOrder(trade.order)

        return {
            "order_id": cancel_req.order_id,
            "status": "Cancelled",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/cancel-all", response_model=CancelAllOrdersResponse)
async def cancel_all_orders(request: Request):
    """Cancel all open orders."""
    try:
        ib = request.app.state.ib
        ib.reqGlobalCancel()

        return {"status": "All orders cancelled"}
    except Exception as e:
        logger.error(f"Error cancelling all orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=GetOrderResponse)
async def get_order(order_id: int, request: Request):
    """Get details of a specific order."""
    try:
        ib = request.app.state.ib

        # Find the trade by order_id
        for trade in ib.trades():
            if trade.order.orderId == order_id:
                return {
                    "order_id": trade.order.orderId,
                    "perm_id": trade.order.permId,
                    "status": trade.orderStatus.status,
                    "filled": trade.orderStatus.filled,
                    "remaining": trade.orderStatus.remaining,
                    "avg_fill_price": trade.orderStatus.avgFillPrice,
                    "contract": {
                        "symbol": trade.contract.symbol,
                        "sec_type": trade.contract.secType,
                        "exchange": trade.contract.exchange,
                    },
                    "order": {
                        "action": trade.order.action,
                        "order_type": trade.order.orderType,
                        "total_quantity": trade.order.totalQuantity,
                        "limit_price": trade.order.lmtPrice,
                        "stop_price": trade.order.auxPrice,
                    },
                }

        raise HTTPException(status_code=404, detail="Order not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
