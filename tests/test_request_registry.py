# tests/test_request_registry.py
import asyncio
import pytest
from services.request_registry import RequestRegistry


@pytest.fixture
def registry():
    return RequestRegistry()


class TestRequestRegistry:
    def test_register_creates_cancel_event(self, registry):
        event = registry.register("user1", "req1")
        assert not event.is_set()
        assert registry.get_active_request("user1") == "req1"

    def test_register_cancels_previous_request(self, registry):
        event1 = registry.register("user1", "req1")
        event2 = registry.register("user1", "req2")

        assert event1.is_set()  # old request cancelled
        assert not event2.is_set()  # new request active
        assert registry.get_active_request("user1") == "req2"

    def test_cancel_sets_event(self, registry):
        event = registry.register("user1", "req1")
        result = registry.cancel("user1", "req1")

        assert result is True
        assert event.is_set()

    def test_cancel_wrong_request_id_returns_false(self, registry):
        registry.register("user1", "req1")
        result = registry.cancel("user1", "wrong_id")

        assert result is False

    def test_cancel_unknown_user_returns_false(self, registry):
        result = registry.cancel("unknown", "req1")
        assert result is False

    def test_complete_clears_request(self, registry):
        registry.register("user1", "req1")
        registry.complete("user1", "req1")

        assert registry.get_active_request("user1") is None

    def test_complete_wrong_request_id_does_nothing(self, registry):
        registry.register("user1", "req1")
        registry.complete("user1", "wrong_id")

        assert registry.get_active_request("user1") == "req1"
