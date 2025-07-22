from typing import Dict

import inject
import redis

from app.config import get_config
from app.services.rate_limiter import RateLimiter
from app.source_connector import SourceConnector


def container_config(binder: inject.Binder) -> None:
    config = get_config()
    ratelimit_config = config.ratelimit

    if ratelimit_config.ssl:
        redis_client = redis.Redis(
            host=ratelimit_config.redis_host,
            port=ratelimit_config.redis_port,
            db=ratelimit_config.redis_db,
            decode_responses=True,
            ssl=True,
            ssl_certfile=ratelimit_config.cert,
            ssl_keyfile=ratelimit_config.key,
            ssl_ca_certs=ratelimit_config.cafile,
            ssl_cert_reqs="required",
        )
    else:
        redis_client = redis.Redis(
            host=ratelimit_config.redis_host,
            port=ratelimit_config.redis_port,
            db=ratelimit_config.redis_db,
            decode_responses=True,
        )
    binder.bind(
        RateLimiter,
        RateLimiter(
            redis_client=redis_client,
            default_reqs=ratelimit_config.default_reqs,
            default_window=ratelimit_config.default_window,
            enabled=ratelimit_config.enabled,
            circuit_break_threshold=ratelimit_config.circuit_break_threshold,
            circuit_break_window=ratelimit_config.circuit_break_window,
            circuit_break_duration=ratelimit_config.circuit_break_duration,
            half_open_allowance=ratelimit_config.half_open_allowance,
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
