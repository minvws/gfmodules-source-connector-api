import json
import logging

import anyio
from fastapi import APIRouter, Response
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import ratelimit
from app.source_connectors.kvk import KvkConnector

logger = logging.getLogger(__name__)
router = APIRouter()


def sync_get_json(request: Request):
    async def _async_get_json():
        return await request.json()

    return anyio.run(_async_get_json)

@router.post("/enrich")
@ratelimit.RateLimit(reqs=10, window=60)
def enrich(request: Request) -> Response:
    try:
        request_data = sync_get_json(request)
    except Exception as e:
        logger.error(f"Failed to parse request data: {e}")
        return JSONResponse({"error": "Invalid JSON data"}, status_code=422)

    connector = KvkConnector({
        "api_url": "https://api.kvk.nl",
        "api_key": "your_api_key_here"
    })
    connector.connect()
    enriched_data = connector.enrich(request_data)
    connector.close()

    return JSONResponse(enriched_data)
