from typing import Dict

import inject
import redis

from app.config import get_config
from app.services.rate_limiter import RateLimiter
from app.source_connector import SourceConnector


def container_config(binder: inject.Binder) -> None:
    config = get_config()

    redis_client = redis.Redis(
        host=config.ratelimit.redis_host,
        port=config.ratelimit.redis_port,
        db=config.ratelimit.redis_db,
        decode_responses=True,
    )
    binder.bind(
        RateLimiter,
        RateLimiter(
            redis_client=redis_client,
            default_reqs=config.ratelimit.default_reqs,
            default_window=config.ratelimit.default_window,
            enabled=config.ratelimit.enabled,
        ),
    )

    # Setup plugins
    plugins: Dict[str, SourceConnector] = {}

    if config.plugin_zorgab.enabled:
        from app.source_connectors.zorgab import ZorgABConnector

        plugins["zorgab"] = ZorgABConnector(config.plugin_zorgab.model_dump())

    if config.plugin_kvk.enabled:
        from app.source_connectors.kvk import KvkConnector

        plugins["kvk"] = KvkConnector(config.plugin_kvk.model_dump())

    binder.bind(dict[str, SourceConnector], plugins)


def get_plugins() -> dict[str, SourceConnector]:
    """
    Returns a dictionary of available plugins.
    """
    return inject.instance(dict[str, SourceConnector])


def get_rate_limiter() -> RateLimiter:
    return inject.instance(RateLimiter)


def setup_container() -> None:
    inject.configure(container_config, once=True)
