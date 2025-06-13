import logging

from fastapi import APIRouter, Response
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import ratelimit
from app.source_connectors.kvk import KvkConnector

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/enrich")
@ratelimit.RateLimit(reqs=10, window=60)
async def enrich(request: Request) -> Response:
    try:
        request_data = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse request data: {e}")
        return JSONResponse({"error": "Invalid JSON data"}, status_code=400)

    connector = KvkConnector({
        "api_url": "https://api.kvk.nl",
        "api_key": "your_api_key_here"
    })
    connector.connect()
    enriched_data = connector.enrich(request_data)
    connector.close()

    return JSONResponse(enriched_data)
