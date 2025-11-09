#!/usr/bin/env python3
"""Test with direct IB instance like the working example"""
import asyncio
from ib_async import IB, Stock

async def main():
    # Create fresh IB instance like test_historical_debug.py
    ib = IB()
    
    print("Connecting...")
    await ib.connectAsync('127.0.0.1', 4002, clientId=888)
    print("Connected!")
    
    # Create contract
    contract = Stock('AAPL', 'SMART', 'USD')
    print(f"Contract: {contract}")
    
    # Qualify
    print("Qualifying...")
    qualified = await ib.qualifyContractsAsync(contract)
    print(f"Qualified: {qualified}")
    
    if qualified:
        contract = qualified[0]
        print("Requesting historical data...")
        bars = await ib.reqHistoricalDataAsync(
            contract,
            endDateTime='',
            durationStr='5 D',
            barSizeSetting='1 day',
            whatToShow='TRADES',
            useRTH=True,
            formatDate=1
        )
        print(f"Got {len(bars)} bars")
        for bar in bars[-3:]:
            print(f"  {bar.date}: ${bar.close:.2f}")
    
    ib.disconnect()
    print("Done!")

if __name__ == '__main__':
    asyncio.run(main())
