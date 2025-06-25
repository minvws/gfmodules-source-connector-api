import logging
from typing import Any

import anyio
from fastapi import APIRouter, Response
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import container, ratelimit

logger = logging.getLogger(__name__)
router = APIRouter()


def sync_get_json(request: Request) -> dict:  # type: ignore
    async def _async_get_json() -> Any:
        return await request.json()

    return anyio.run(_async_get_json)


@router.post("/enrich/{plugin}")
@ratelimit.RateLimit(reqs=10, window=60)
def enrich(request: Request, plugin: str) -> Response:
    # Check if the plugin is enabled / existing
    plugins = container.get_plugins()
    if plugin not in plugins:
        logger.error(f"Plugin {plugin} is not enabled or does not exist.")
        return JSONResponse({"error": "Plugin not found"}, status_code=404)

    # Make sure the request data is valid JSON
    try:
        request_data = sync_get_json(request)
    except Exception as e:
        logger.error(f"Failed to parse request data: {e}")
        return JSONResponse({"error": "Invalid JSON data"}, status_code=422)

    # Connect to the plugin and enrich the data
    plugins[plugin].connect()
    enriched_data = plugins[plugin].enrich(request_data)
    plugins[plugin].close()

    return JSONResponse(enriched_data)
