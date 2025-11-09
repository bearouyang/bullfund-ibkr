#!/usr/bin/env python3
"""Debug script to test historical data request"""

import asyncio
from ib_async import IB, Stock

async def test_historical():
    ib = IB()
    
    print("Connecting to IB Gateway...")
    await ib.connectAsync('127.0.0.1', 4002, clientId=999)
    print("Connected!")
    
    # Create contract
    contract = Stock('AAPL', 'SMART', 'USD')
    print(f"Created contract: {contract}")
    
    # Qualify contract
    print("Qualifying contract...")
    qualified = await ib.qualifyContractsAsync(contract)
    print(f"Qualified: {qualified}")
    
    if qualified:
        contract = qualified[0]
        print(f"Using qualified contract: {contract}")
        
        # Request historical data
        print("Requesting historical data...")
        try:
            bars = await asyncio.wait_for(
                ib.reqHistoricalDataAsync(
                    contract,
                    endDateTime='',
                    durationStr='5 D',
                    barSizeSetting='1 day',
                    whatToShow='TRADES',
                    useRTH=True
                ),
                timeout=10.0
            )
            print(f"Got {len(bars)} bars")
            for bar in bars[-3:]:
                print(f"  {bar.date}: C=${bar.close:.2f}")
        except asyncio.TimeoutError:
            print("ERROR: Request timed out after 10 seconds")
    
    ib.disconnect()
    print("Disconnected")

if __name__ == '__main__':
    asyncio.run(test_historical())
