import redis
import inject

from app.config import get_config
from app.services.rate_limiter import RateLimiter


def container_config(binder: inject.Binder) -> None:
    config = get_config()

    redis_client = redis.Redis(host=config.ratelimit.redis_host, port=config.ratelimit.redis_port, db=config.ratelimit.redis_db)
    binder.bind(
        RateLimiter,
        RateLimiter(
            redis = redis_client,
            default_reqs=config.ratelimit.default_reqs,
            default_window=config.ratelimit.default_window,
            enabled=config.ratelimit.enabled
        )
    )


def get_rate_limiter() -> RateLimiter:
    return inject.instance(RateLimiter)


def setup_container() -> None:
    inject.configure(container_config, once=True)
