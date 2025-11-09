import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from ib_async import IB
from config import settings


ib = IB()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not ib.isConnected():
        await ib.connectAsync(
            settings.ib_host, settings.ib_port, settings.ib_client_id, readonly=True
        )
    app.state.ib = ib
    yield
    if ib.isConnected():
        ib.disconnect()


app = FastAPI(lifespan=lifespan)

from routers import account, trading, market_data, research

app.include_router(account.router, prefix="/api/v1/account")
app.include_router(trading.router, prefix="/api/v1/trading")
app.include_router(market_data.router, prefix="/api/v1/market-data")
app.include_router(research.router, prefix="/api/v1/research")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
