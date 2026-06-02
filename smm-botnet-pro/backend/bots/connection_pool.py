"""
Connection Pool - Manages aiohttp connection pools for efficient HTTP requests.
"""

import logging
import asyncio
from typing import Optional
import aiohttp
from django.conf import settings

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Manages aiohttp connection pools for efficient HTTP requests."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize the connection pool."""
        if self.initialized:
            return
        
        try:
            # Create TCP connector with connection limits
            self.connector = aiohttp.TCPConnector(
                limit=50,  # Max simultaneous connections
                limit_per_host=10,  # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
            )
            
            # Create client session
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            self.initialized = True
            logger.info("HTTP connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            await self.close()
    
    async def close(self):
        """Close the connection pool."""
        if self.session:
            await self.session.close()
            self.session = None
        
        if self.connector:
            await self.connector.close()
            self.connector = None
        
        self.initialized = False
        logger.info("HTTP connection pool closed")
    
    def get_session(self) -> Optional[aiohttp.ClientSession]:
        """Get the aiohttp session."""
        if not self.initialized or not self.session:
            logger.warning("Connection pool not initialized")
            return None
        
        return self.session
    
    async def get(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Perform a GET request."""
        session = self.get_session()
        if not session:
            return None
        
        try:
            return await session.get(url, **kwargs)
        except Exception as e:
            logger.error(f"GET request failed for {url}: {e}")
            return None
    
    async def post(self, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Perform a POST request."""
        session = self.get_session()
        if not session:
            return None
        
        try:
            return await session.post(url, **kwargs)
        except Exception as e:
            logger.error(f"POST request failed for {url}: {e}")
            return None
    
    async def request(self, method: str, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Perform a generic HTTP request."""
        session = self.get_session()
        if not session:
            return None
        
        try:
            return await session.request(method, url, **kwargs)
        except Exception as e:
            logger.error(f"{method} request failed for {url}: {e}")
            return None


# Global instance
connection_pool = ConnectionPool()

# Async helper functions for easy usage
async def http_get(url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
    """Perform a GET request using the global connection pool."""
    return await connection_pool.get(url, **kwargs)

async def http_post(url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
    """Perform a POST request using the global connection pool."""
    return await connection_pool.post(url, **kwargs)

async def http_request(method: str, url: str, **kwargs) -> Optional[aiohttp.ClientResponse]:
    """Perform a generic HTTP request using the global connection pool."""
    return await connection_pool.request(method, url, **kwargs)