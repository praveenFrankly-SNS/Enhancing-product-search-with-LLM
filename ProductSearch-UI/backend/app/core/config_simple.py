"""
Simple configuration without pydantic-settings
"""
import os
from typing import List


class Settings:
    """Application settings from environment variables"""
    
    def __init__(self):
        # Databricks Configuration
        self.databricks_host = os.getenv("DATABRICKS_HOST", "")
        self.databricks_token = os.getenv("DATABRICKS_TOKEN", "")
        self.vector_search_endpoint = os.getenv("VECTOR_SEARCH_ENDPOINT", "")
        self.sql_warehouse_id = os.getenv("SQL_WAREHOUSE_ID", "")
        self.unity_catalog_name = os.getenv("UNITY_CATALOG_NAME", "main")
        self.unity_schema_name = os.getenv("UNITY_SCHEMA_NAME", "product_search")
        
        # Application Configuration
        self.app_name = os.getenv("APP_NAME", "ProductSearch Enterprise")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # API Configuration
        self.api_v1_prefix = os.getenv("API_V1_PREFIX", "/api/v1")
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        
        # Security
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        
        # Rate Limiting
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        self.rate_limit_per_hour = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
        
        # Cache Configuration
        self.cache_enabled = os.getenv("CACHE_ENABLED", "False").lower() == "true"
        self.cache_ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")
        
        # Search Configuration
        self.max_query_length = int(os.getenv("MAX_QUERY_LENGTH", "200"))
        self.max_results_per_page = int(os.getenv("MAX_RESULTS_PER_PAGE", "50"))
        self.default_page_size = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
        self.vector_search_top_k = int(os.getenv("VECTOR_SEARCH_TOP_K", "100"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))
        
        # Performance
        self.databricks_connection_timeout = int(os.getenv("DATABRICKS_CONNECTION_TIMEOUT", "30"))
        self.databricks_read_timeout = int(os.getenv("DATABRICKS_READ_TIMEOUT", "60"))
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        
        # Monitoring
        self.enable_metrics = os.getenv("ENABLE_METRICS", "True").lower() == "true"
        self.metrics_port = int(os.getenv("METRICS_PORT", "9090"))
        self.enable_request_logging = os.getenv("ENABLE_REQUEST_LOGGING", "True").lower() == "true"
        self.slow_query_threshold_ms = int(os.getenv("SLOW_QUERY_THRESHOLD_MS", "2000"))
    
    @property
    def databricks_url(self) -> str:
        """Full Databricks workspace URL"""
        return f"https://{self.databricks_host}"
    
    @property
    def full_schema_name(self) -> str:
        """Full schema name in Unity Catalog format"""
        return f"{self.unity_catalog_name}.{self.unity_schema_name}"
    
    @property
    def redis_url(self) -> str:
        """Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Global settings instance
settings = Settings()
