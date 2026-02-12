import time
import unittest
from typing import Any
from unittest.mock import MagicMock

from app.services.rate_limiter import RateLimiter


class TestRateLimiter(unittest.TestCase):
    def setUp(self) -> None:
        self.redis = MagicMock()
        self.limiter = RateLimiter(redis_client=self.redis)

    def test_limit_allows_within_threshold(self) -> None:
        self.redis.hget.return_value = None
        self.redis.pipeline.return_value.__enter__.return_value.execute.return_value = [None, 0, None, None]

        result = self.limiter.limit("test-key")

        self.assertTrue(result.allowed)
        self.assertEqual(result.reason, "allowed")

    def test_limit_blocks_when_exceeded(self) -> None:
        self.redis.hget.return_value = None
        self.redis.pipeline.return_value.__enter__.return_value.execute.return_value = [None, 100, None, None]
        self.redis.zcard.return_value = 100

        result = self.limiter.limit("test-key", reqs=100)

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "rate_limit_exceeded")

    def test_circuit_breaker_opens_on_errors(self) -> None:
        self.redis.hget.side_effect = lambda key, field=None: "half_open" if field == "state" else None

        self.limiter.record_error("test-key")

        pipe = self.redis.pipeline.return_value.__enter__.return_value
        pipe.hset.assert_any_call("circuit:test-key", "state", "open")

    def test_half_open_fails_if_tested_exceeds(self) -> None:
        self.redis.hget.side_effect = lambda key, field=None: (
            "half_open" if field == "state" else "5" if field == "tested" else None
        )

        allowed, reason = self.limiter.check_circuit("test-key")
        self.assertFalse(allowed)
        self.assertEqual(reason, "half_open_limit")

    def test_check_circuit_closed(self) -> None:
        self.redis.hget.side_effect = lambda key, field=None: "closed" if field == "state" else None

        allowed, reason = self.limiter.check_circuit("test-key")
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_reset_deletes_keys(self) -> None:
        pipe = self.redis.pipeline.return_value.__enter__.return_value
        self.limiter.reset("foobar")

        pipe.delete.assert_any_call("circuit:foobar")
        pipe.delete.assert_any_call("circuit_errors:foobar")
        pipe.delete.assert_any_call("rate_limit:foobar")

    def test_half_open_increments_tested(self) -> None:
        def mock_hget(key: Any, field: str | None = None) -> str | None:
            if field == "state":
                return "half_open"
            elif field == "opened_at":
                return str(round(time.time()) - 1000)
            elif field == "tested":
                return "2"
            return None

        self.redis.hget.side_effect = mock_hget

        pipe = self.redis.pipeline.return_value.__enter__.return_value

        allowed, reason = self.limiter.check_circuit("test-key")

        self.assertTrue(allowed)
        pipe.hincrby.assert_called_once_with("circuit:test-key", "tested", 1)

    def test_open_circuit_within_duration_blocks(self) -> None:
        now = time.time()
        self.redis.hget.side_effect = lambda key, field=None: "open" if field == "state" else str(now)

        allowed, reason = self.limiter.check_circuit("test-key")

        self.assertFalse(allowed)
        self.assertEqual(reason, "circuit_open")

    def test_open_circuit_transitions_to_half_open_after_duration(self) -> None:
        def mock_hget(key: Any, field: str | None = None) -> str | None:
            if field == "state":
                return "open"
            elif field == "opened_at":
                return str(round(time.time()) - 1000)
            elif field == "tested":
                return "0"
            return None

        self.redis.hget.side_effect = mock_hget

        pipe = self.redis.pipeline.return_value.__enter__.return_value
        allowed, reason = self.limiter.check_circuit("test-key")

        self.assertTrue(allowed)
        pipe.hset.assert_any_call("circuit:test-key", "state", "half_open")
        pipe.hset.assert_any_call("circuit:test-key", "tested", "0")

    def test_record_success_in_half_open_resets_state(self) -> None:
        self.redis.hget.side_effect = lambda key, field=None: "half_open" if field == "state" else None

        pipe = self.redis.pipeline.return_value.__enter__.return_value
        self.limiter.record_success("test-key")

        pipe.hset.assert_called_with("circuit:test-key", "state", "closed")
        pipe.hdel.assert_called_with("circuit:test-key", "opened_at", "tested")
        pipe.delete.assert_called_with("circuit_errors:test-key")

    def test_limit_skips_when_disabled(self) -> None:
        self.limiter.enabled = False
        result = self.limiter.limit("abc")

        self.assertTrue(result.allowed)
        self.assertEqual(result.reason, "rate_limiter_disabled")

    def test_record_error_opens_circuit_when_threshold_exceeded(self) -> None:
        self.redis.hget.side_effect = lambda key, field=None: "closed" if field == "state" else None
        self.redis.zcard.return_value = 10  # >= threshold

        pipe = self.redis.pipeline.return_value.__enter__.return_value
        self.limiter.record_error("test-key")

        pipe.hset.assert_any_call("circuit:test-key", "state", "open")
