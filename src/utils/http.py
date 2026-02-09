"""
Modern HTTP Client using httpx
Simple wrapper around httpx for consistent usage across the application.
"""

from typing import Any, Dict, Optional
import httpx
from src.utils.loguru_config import get_logger
logger = get_logger(__name__)
class HTTPClient:
    """Modern HTTP client using httpx with async support."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        self.logger = logger
        self.base_url = base_url
        self.timeout = timeout
        
        # Create async client
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            follow_redirects=True)
        
        logger.info(f"HTTP client initialized with base_url: {base_url}")
    
    async def get(self, url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Async GET request."""
        try:
            logger.info(f"GET {url}")
            response = await self._client.get(url, params=params, headers=headers)
            logger.info(f"GET {url} -> {response.status_code}")
            return response
        except Exception as e:
            logger.exception(f"GET {url} failed: {e}")
            raise
    
    async def post(self, url: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None, 
                   headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Async POST request."""
        try:
            logger.info(f"POST {url}")
            response = await self._client.post(url, json=json, data=data, headers=headers)
            logger.info(f"POST {url} -> {response.status_code}")
            return response
        except Exception as e:
            logger.exception(f"POST {url} failed: {e}")
            raise
    
    async def put(self, url: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None,
                  headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Async PUT request."""
        try:
            logger.info(f"PUT {url}")
            response = await self._client.put(url, json=json, data=data, headers=headers)
            logger.info(f"PUT {url} -> {response.status_code}")
            return response
        except Exception as e:
            logger.exception(f"PUT {url} failed: {e}")
            raise
    
    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Async DELETE request."""
        try:
            logger.info(f"DELETE {url}")
            response = await self._client.delete(url, headers=headers)
            logger.info(f"DELETE {url} -> {response.status_code}")
            return response
        except Exception as e:
            logger.exception(f"DELETE {url} failed: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
        logger.info("HTTP client closed")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, _exc_val, _exc_tb):
        await self.close()


# Convenience functions for simple requests
async def get(url: str, **kwargs) -> httpx.Response:
    """Simple async GET request."""
    async with HTTPClient() as client:
        return await client.get(url, **kwargs)


async def post(url: str, **kwargs) -> httpx.Response:
    """Simple async POST request."""
    async with HTTPClient() as client:
        return await client.post(url, **kwargs)


