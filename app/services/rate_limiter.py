import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import redis

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class RateLimitResult:
    allowed: bool
    reason: Optional[str]
    remaining: Optional[int] = None
    reset_time: Optional[float] = None


class RateLimiter:
    def __init__(
        self,
        enabled: bool = True,
        redis: redis.Redis = None,
        default_reqs: int = 100,
        default_window: int = 60,
        circuit_break_threshold: int = 10,
        circuit_break_window: int = 60,
        circuit_break_duration: int = 300,
        half_open_allowance: int = 5
    ):
        self.redis = redis
        self.enabled = enabled
        self.default_reqs = default_reqs
        self.default_window = default_window
        self.circuit_break_threshold = circuit_break_threshold
        self.circuit_break_window = circuit_break_window
        self.circuit_break_duration = circuit_break_duration
        self.half_open_allowance = half_open_allowance

    def _get_circuit_key(self, key: str) -> str:
        return f"circuit:{key}"

    def _get_error_count_key(self, key: str) -> str:
        return f"circuit_errors:{key}"

    def _get_rate_limit_key(self, key: str) -> str:
        return f"rate_limit:{key}"

    def _get_state(self, circuit_key: str) -> CircuitState:
        state = self.redis.hget(circuit_key, "state")
        print(f"Current state for key {circuit_key}: {state}")
        return CircuitState(state.decode('utf-8')) if state else CircuitState.CLOSED

    def record_success(self, key: str) -> None:
        circuit_key = self._get_circuit_key(key)
        error_count_key = self._get_error_count_key(key)
        state = self._get_state(circuit_key)

        if state == CircuitState.HALF_OPEN:
            with self.redis.pipeline() as pipe:
                pipe.hset(circuit_key, "state", CircuitState.CLOSED.value)
                pipe.hdel(circuit_key, "opened_at", "tested")
                pipe.delete(error_count_key)
                pipe.execute()

    def record_error(self, key: str) -> None:
        error_count_key = self._get_error_count_key(key)
        circuit_key = self._get_circuit_key(key)
        now = time.time()
        state = self._get_state(circuit_key)
        print(f"Recording error for key: {key}, current state: {state.name}")

        if state == CircuitState.HALF_OPEN:
            with self.redis.pipeline() as pipe:
                pipe.hset(circuit_key, "state", CircuitState.OPEN.value)
                pipe.hset(circuit_key, "opened_at", now)
                pipe.execute()
            print("blaat")
            return


        with self.redis.pipeline() as pipe:
            pipe.zadd(error_count_key, {now: now})
            pipe.zremrangebyscore(error_count_key, 0, now - self.circuit_break_window)
            pipe.expire(error_count_key, self.circuit_break_window)
            pipe.execute()

        error_count = self.redis.zcard(error_count_key) or 0
        print(f"Error count for key {key}: {error_count}")
        if error_count >= self.circuit_break_threshold:
            circuit_key = self._get_circuit_key(key)
            with self.redis.pipeline() as pipe:
                pipe.hset(circuit_key, "state", CircuitState.OPEN.value)
                pipe.hset(circuit_key, "opened_at", now)
                pipe.execute()

    def check_circuit(self, key: str) -> Tuple[bool, Optional[str]]:
        circuit_key = self._get_circuit_key(key)
        # error_count_key = self._get_error_count_key(key)
        state = self._get_state(circuit_key)

        if state == CircuitState.OPEN:
            opened_at = float(self.redis.hget(circuit_key, "opened_at") or 0)
            if time.time() - opened_at < self.circuit_break_duration:
                return False, "circuit_open"

            with self.redis.pipeline() as pipe:
                pipe.hset(circuit_key, "state", CircuitState.HALF_OPEN.value)
                pipe.hset(circuit_key, "tested", 0)
                pipe.execute()
            state = CircuitState.HALF_OPEN

        if state == CircuitState.HALF_OPEN:
            tested = int(self.redis.hget(circuit_key, "tested") or 0)
            if tested >= self.half_open_allowance:
                now = time.time()
                with self.redis.pipeline() as pipe:
                    pipe.hset(circuit_key, "state", CircuitState.OPEN.value)
                    pipe.hset(circuit_key, "opened_at", now)
                    pipe.execute()
                return False, "half_open_limit"

            with self.redis.pipeline() as pipe:
                pipe.hincrby(circuit_key, "tested", 1)
                pipe.execute()

        return True, None

    def limit(
        self,
        key: str,
        reqs: Optional[int] = None,
        window: Optional[int] = None
    ) -> RateLimitResult:

        # Just continue when the rate limiter is not enabled
        if not self.enabled:
            return RateLimitResult(allowed=True, reason="rate_limiter_disabled")

        allowed, reason = self.check_circuit(key)
        if not allowed:
            print(f"Circuit is {reason} for key: {key}")
            return RateLimitResult(allowed=False, reason=reason)

        rate_limit_key = self._get_rate_limit_key(key)
        reqs = reqs or self.default_reqs
        window = window or self.default_window
        now = time.time()
        window_start = now - window

        with self.redis.pipeline() as pipe:
            pipe.zremrangebyscore(rate_limit_key, 0, window_start)
            pipe.zcard(rate_limit_key)
            pipe.zadd(rate_limit_key, {now: now})
            pipe.expire(rate_limit_key, window)
            _, current_count, _, _ = pipe.execute()

        remaining = max(0, reqs - current_count)
        reset_time = window_start + window

        if current_count >= reqs:
            self.record_error(key)
            return RateLimitResult(allowed=False, reason="rate_limit_exceeded", remaining=remaining, reset_time=reset_time)

        if self._get_state(self._get_circuit_key(key)) == CircuitState.HALF_OPEN:
            self.record_success(key)

        return RateLimitResult(allowed=True, reason="allowed", remaining=remaining, reset_time=reset_time)

    def reset(self, key: str) -> None:
        circuit_key = self._get_circuit_key(key)
        error_count_key = self._get_error_count_key(key)
        rate_limit_key = self._get_rate_limit_key(key)

        with self.redis.pipeline() as pipe:
            pipe.delete(circuit_key)
            pipe.delete(error_count_key)
            pipe.delete(rate_limit_key)
            pipe.execute()
