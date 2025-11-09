from fastapi import APIRouter, HTTPException
import logging
from fastapi import Request
from models import ContractRequest, FundamentalDataRequest, NewsRequest
from routers.trading import create_contract
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/contract-details")
async def get_contract_details(contract_req: ContractRequest, request: Request):
    """Get detailed contract information using the thread-safe sync wrapper."""
    try:
        contract = create_contract(contract_req)
        # Correctly call the sync wrapper method
        ib = request.app.state.ib
        details_list = await ib.reqContractDetailsAsync(contract)

        if not details_list:
            raise HTTPException(status_code=404, detail="Contract details not found")

        return {"details": details_list, "count": len(details_list)}
    except HTTPException:
        # Re-raise HTTPExceptions (like 404) without converting to 500
        raise
    except Exception as e:
        logger.error(f"Error getting contract details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fundamental-data")
async def get_fundamental_data(request: FundamentalDataRequest, req: Request):
    """Get fundamental data for a contract."""
    try:
        contract = create_contract(request.contract)
        ib = req.app.state.ib

        # Qualify the contract first
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")

        contract = qualified_contracts[0]

        # Request fundamental data
        fundamental_data = await ib.reqFundamentalDataAsync(
            contract, request.report_type
        )

        return {
            "symbol": contract.symbol,
            "report_type": request.report_type,
            "data": fundamental_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fundamental data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news/historical")
async def get_historical_news(request: NewsRequest, req: Request):
    """Get historical news articles."""
    try:
        ib = req.app.state.ib

        if request.contract:
            contract = create_contract(request.contract)
            # Qualify the contract first
            qualified_contracts = await ib.qualifyContractsAsync(contract)
            if not qualified_contracts:
                raise HTTPException(status_code=404, detail="Contract not found")
            contract = qualified_contracts[0]
        else:
            contract = None

        # Request historical news
        news_articles = await ib.reqHistoricalNewsAsync(
            conId=contract.conId if contract else 0,
            providerCodes=request.provider_codes,
            startDateTime=request.start_time or "",
            endDateTime=request.end_time or "",
            totalResults=request.total_results,
        )

        articles = [
            {
                "time": str(article.time),
                "provider_code": article.providerCode,
                "article_id": article.articleId,
                "headline": article.headline,
            }
            for article in news_articles
        ]

        return {"articles": articles, "count": len(articles)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/article/{provider_code}/{article_id}")
async def get_news_article(provider_code: str, article_id: str, req: Request):
    """Get a specific news article by provider code and article ID."""
    try:
        ib = req.app.state.ib

        article = await ib.reqNewsArticleAsync(
            providerCode=provider_code, articleId=article_id
        )

        return {
            "provider_code": provider_code,
            "article_id": article_id,
            "article_type": article.articleType,
            "article_text": article.articleText,
        }
    except Exception as e:
        logger.error(f"Error getting news article: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/providers")
async def get_news_providers(req: Request):
    """Get available news providers."""
    try:
        ib = req.app.state.ib
        providers = await ib.reqNewsProvidersAsync()

        provider_list = [
            {"code": provider.code, "name": provider.name} for provider in providers
        ]

        return {"providers": provider_list, "count": len(provider_list)}
    except Exception as e:
        logger.error(f"Error getting news providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/option-chain")
async def get_option_chain(contract_req: ContractRequest, req: Request):
    """Get option chain parameters for a contract."""
    try:
        contract = create_contract(contract_req)
        ib = req.app.state.ib

        # Qualify the contract first
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")

        contract = qualified_contracts[0]

        # Request option parameters
        chains = await ib.reqSecDefOptParamsAsync(
            underlyingSymbol=contract.symbol,
            futFopExchange="",
            underlyingSecType=contract.secType,
            underlyingConId=contract.conId,
        )

        chain_list = [
            {
                "exchange": chain.exchange,
                "underlying_con_id": chain.underlyingConId,
                "trading_class": chain.tradingClass,
                "multiplier": chain.multiplier,
                "expirations": sorted(chain.expirations),
                "strikes": sorted(chain.strikes),
            }
            for chain in chains
        ]

        return {"chains": chain_list, "count": len(chain_list)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting option chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{pattern}")
async def search_contracts(pattern: str, req: Request):
    """Search for contracts by pattern (symbol search)."""
    try:
        ib = req.app.state.ib

        matches = await ib.reqMatchingSymbolsAsync(pattern)

        contract_list = [
            {
                "contract": {
                    "con_id": match.contract.conId,
                    "symbol": match.contract.symbol,
                    "sec_type": match.contract.secType,
                    "primary_exchange": match.contract.primaryExchange,
                    "currency": match.contract.currency,
                },
                "derivative_sec_types": match.derivativeSecTypes,
            }
            for match in matches
        ]

        return {"matches": contract_list, "count": len(contract_list)}
    except Exception as e:
        logger.error(f"Error searching contracts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/histogram")
async def get_histogram_data(
    contract_req: ContractRequest,
    req: Request,
    use_rth: bool = True,
    period: str = "1 day",
):
    """Get histogram data for a contract."""
    try:
        contract = create_contract(contract_req)
        ib = req.app.state.ib

        # Qualify the contract first
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")

        contract = qualified_contracts[0]

        # Request histogram data
        histogram = await ib.reqHistogramDataAsync(
            contract=contract, useRTH=use_rth, timePeriod=period
        )

        histogram_list = [
            {"price": item.price, "count": item.count} for item in histogram
        ]

        return {"histogram": histogram_list, "count": len(histogram_list)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting histogram data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dividends")
async def get_dividends(
    contract_req: ContractRequest,
    req: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get dividend data for a stock."""
    try:
        contract = create_contract(contract_req)
        ib = req.app.state.ib

        # Qualify the contract first
        qualified_contracts = await ib.qualifyContractsAsync(contract)
        if not qualified_contracts:
            raise HTTPException(status_code=404, detail="Contract not found")

        contract = qualified_contracts[0]

        # Request dividends using fundamental data
        divs = await ib.reqFundamentalDataAsync(contract, "CalendarReport")

        return {
            "symbol": contract.symbol,
            "dividends": divs,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dividends: {e}")
        raise HTTPException(status_code=500, detail=str(e))
