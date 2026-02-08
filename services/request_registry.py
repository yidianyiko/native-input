# services/request_registry.py
import asyncio


class RequestRegistry:
    def __init__(self):
        self._active_requests: dict[str, str] = {}  # user_id -> request_id
        self._cancel_events: dict[str, asyncio.Event] = {}  # request_id -> Event

    def get_active_request(self, user_id: str) -> str | None:
        return self._active_requests.get(user_id)

    def register(self, user_id: str, request_id: str) -> asyncio.Event:
        # Cancel existing request for this user
        if old_request_id := self._active_requests.get(user_id):
            if old_event := self._cancel_events.get(old_request_id):
                old_event.set()
            self._cancel_events.pop(old_request_id, None)

        # Create new cancel event
        event = asyncio.Event()
        self._active_requests[user_id] = request_id
        self._cancel_events[request_id] = event
        return event

    def cancel(self, user_id: str, request_id: str) -> bool:
        if self._active_requests.get(user_id) != request_id:
            return False

        if event := self._cancel_events.get(request_id):
            event.set()
            return True
        return False

    def complete(self, user_id: str, request_id: str) -> None:
        if self._active_requests.get(user_id) == request_id:
            del self._active_requests[user_id]
            self._cancel_events.pop(request_id, None)
