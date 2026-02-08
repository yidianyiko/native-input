import time

import httpx

from app.service import ServiceManager


class TestServiceManager:
    def test_service_starts_and_stops(self):
        manager = ServiceManager(port=18099)  # Use different port for testing

        manager.start()

        deadline = time.time() + 5
        while time.time() < deadline:
            if manager.is_running():
                try:
                    response = httpx.get("http://127.0.0.1:18099/health", timeout=0.5)
                    assert response.status_code == 200
                    break
                except Exception:
                    time.sleep(0.1)
            else:
                time.sleep(0.05)
        else:
            raise AssertionError("Service not responding")

        manager.stop()
        time.sleep(0.2)

        assert not manager.is_running()

    def test_service_not_running_initially(self):
        manager = ServiceManager(port=18098)
        assert not manager.is_running()
