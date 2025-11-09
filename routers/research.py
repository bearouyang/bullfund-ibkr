from fastapi import APIRouter, HTTPException
import logging
from fastapi import Request
from models import ContractRequest
from routers.trading import create_contract

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


# ... (other routes would follow a similar pattern)
