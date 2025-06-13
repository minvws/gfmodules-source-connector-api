import json
import logging
from pathlib import Path

from fastapi import APIRouter, Response
from starlette.requests import Request

from app import ratelimit
from app.container import get_rate_limiter

logger = logging.getLogger(__name__)
router = APIRouter()

# https://www.patorjk.com/software/taag/#p=display&f=Doom&t=Skeleton
LOGO = r"""
 _____                          _____                             _
/  ___|                        /  __ \                           | |
\ `--.  ___  _   _ _ __ ___ ___| /  \/ ___  _ __  _ __   ___  ___| |_ ___  _ __
 `--. \/ _ \| | | | '__/ __/ _ \ |    / _ \| '_ \| '_ \ / _ \/ __| __/ _ \| '__|
/\__/ / (_) | |_| | | | (_|  __/ \__/\ (_) | | | | | | |  __/ (__| || (_) | |
\____/ \___/ \__,_|_|  \___\___|\____/\___/|_| |_|_| |_|\___|\___|\__\___/|_|

"""

@router.get("/")
@ratelimit.RateLimit(reqs=10, window=60)
def index(request: Request) -> Response:
    content = LOGO

    try:
        with open(Path(__file__).parent.parent.parent / "version.json", "r") as file:
            data = json.load(file)
            content += "\nVersion: %s\nCommit: %s" % (data["version"], data["git_ref"])
    except BaseException as e:
        content += "\nNo version information found"
        logger.info("Version info could not be loaded: %s" % e)

    return Response(content)


@router.get("/version.json")
@ratelimit.RateLimit()
def version_json(request: Request) -> Response:
    try:
        with open(Path(__file__).parent.parent.parent / "version.json", "r") as file:
            content = file.read()
    except BaseException as e:
        logger.info("Version info could not be loaded: %s" % e)
        return Response(status_code=404)

    return Response(content)
