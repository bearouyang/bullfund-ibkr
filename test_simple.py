#!/usr/bin/env python3
"""Simplest possible test"""
import asyncio
from ib_async import IB
from routers.trading import create_contract
from routers.market_data import get_historical_bars
from models import BarDataRequest, ContractRequest

async def main():
    print("Connecting...")
    ib = IB()
    await ib.connectAsync("127.0.0.1", 7497, 1, readonly=True)
    print("Connected!")
    
    request = BarDataRequest(
        contract=ContractRequest(
            symbol="AAPL",
            sec_type="STK",
            exchange="SMART",
            currency="USD"
        ),
        bar_size="1 day",
        duration="5 D",
        what_to_show="TRADES",
        use_rth=True
    )
    
    print("Requesting historical data...")
    # get_historical_bars now expects a FastAPI Request; calling directly isn't appropriate in this test.
    # Replace with a direct call for demonstration
    bars = await ib.reqHistoricalDataAsync(
        contract=create_contract(request.contract),
        duration=request.duration,
        barSizeSetting=request.bar_size,
        whatToShow=request.what_to_show,
        useRTH=request.use_rth
    )
    result = {"bars": [
        {
            "date": str(bar.date),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        } for bar in bars
    ], "count": len(bars)}
    print(f"Got {result['count']} bars")
    
    for bar in result["bars"][-3:]:
        print(f"  {bar['date']}: ${bar['close']:.2f}")
    
    ib.disconnect()
    print("Done!")

if __name__ == '__main__':
    asyncio.run(main())
