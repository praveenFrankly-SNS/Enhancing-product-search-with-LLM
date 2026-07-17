"""
Caching service for search results and product data
"""
import json
import hashlib
from typing import Any, Optional
from redis import Redis
from redis.exceptions import RedisError
from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class CacheService:
    """Service for caching search results and product data"""
    
    def __init__(self):
        """Initialize Redis connection"""
        if settings.cache_enabled:
            try:
                self.redis_client = Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password if settings.redis_password else None,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                
                logger.info(
                    "Cache service initialized",
                    redis_host=settings.redis_host,
                    redis_port=settings.redis_port
                )
            
            except RedisError as e:
                logger.warning(
                    "Redis connection failed, caching disabled",
                    error=str(e)
                )
                self.enabled = False
        else:
            self.enabled = False
            logger.info("Cache service disabled by configuration")
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and parameters
        
        Args:
            prefix: Key prefix (e.g., 'search', 'product')
            args: Positional arguments to include in key
            kwargs: Keyword arguments to include in key
            
        Returns:
            Cache key string
        """
        # Create a string representation of all parameters
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_string = ":".join(key_parts)
        
        # Hash the key string for consistent length
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            
            if value:
                logger.debug("Cache hit", key=key)
                return json.loads(value)
            else:
                logger.debug("Cache miss", key=key)
                return None
        
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning("Cache get failed", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        if ttl is None:
            ttl = settings.cache_ttl_seconds
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            
            logger.debug("Cache set", key=key, ttl=ttl)
            return True
        
        except (RedisError, TypeError, json.JSONEncodeError) as e:
            logger.warning("Cache set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug("Cache delete", key=key)
            return True
        
        except RedisError as e:
            logger.warning("Cache delete failed", key=key, error=str(e))
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., 'search:*')
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info("Cache cleared", pattern=pattern, count=count)
                return count
            return 0
        
        except RedisError as e:
            logger.warning("Cache clear failed", pattern=pattern, error=str(e))
            return 0
    
    async def get_search_results(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[dict] = None
    ) -> Optional[dict]:
        """
        Get cached search results
        
        Args:
            query: Search query
            page: Page number
            page_size: Results per page
            filters: Optional filters
            
        Returns:
            Cached search results or None
        """
        key = self._generate_cache_key(
            "search",
            query=query.lower().strip(),
            page=page,
            page_size=page_size,
            filters=filters
        )
        
        return await self.get(key)
    
    async def set_search_results(
        self,
        query: str,
        results: dict,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[dict] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache search results
        
        Args:
            query: Search query
            results: Search results to cache
            page: Page number
            page_size: Results per page
            filters: Optional filters
            ttl: Cache TTL in seconds
            
        Returns:
            True if successful
        """
        key = self._generate_cache_key(
            "search",
            query=query.lower().strip(),
            page=page,
            page_size=page_size,
            filters=filters
        )
        
        return await self.set(key, results, ttl)
    
    async def get_product(self, product_id: str) -> Optional[dict]:
        """
        Get cached product details
        
        Args:
            product_id: Product ID
            
        Returns:
            Cached product details or None
        """
        key = self._generate_cache_key("product", product_id)
        return await self.get(key)
    
    async def set_product(
        self,
        product_id: str,
        product: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache product details
        
        Args:
            product_id: Product ID
            product: Product details to cache
            ttl: Cache TTL in seconds
            
        Returns:
            True if successful
        """
        key = self._generate_cache_key("product", product_id)
        return await self.set(key, product, ttl)
    
    async def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "total_keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        
        except RedisError as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {"enabled": True, "error": str(e)}
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global service instance
cache_service = CacheService()
