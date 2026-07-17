"""
Application configuration management
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Databricks Configuration
    databricks_host: str = Field(..., env="DATABRICKS_HOST")
    databricks_token: str = Field(..., env="DATABRICKS_TOKEN")
    vector_search_endpoint: str = Field(..., env="VECTOR_SEARCH_ENDPOINT")
    vector_search_index_name: str = Field(
        default="product_search_dev.gold.product_search_catalog_index",
        env="VECTOR_SEARCH_INDEX_NAME"
    )
    sql_warehouse_id: str = Field(..., env="SQL_WAREHOUSE_ID")
    unity_catalog_name: str = Field(default="product_search_dev", env="UNITY_CATALOG_NAME")
    unity_schema_name: str = Field(default="gold", env="UNITY_SCHEMA_NAME")

    # Application Configuration
    app_name: str = Field(default="ProductSearch Enterprise", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")

    # Security
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="ALLOWED_ORIGINS"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")

    # Cache Configuration
    cache_enabled: bool = Field(default=False, env="CACHE_ENABLED")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")

    # Search Configuration
    max_query_length: int = Field(default=200, env="MAX_QUERY_LENGTH")
    max_results_per_page: int = Field(default=50, env="MAX_RESULTS_PER_PAGE")
    default_page_size: int = Field(default=20, env="DEFAULT_PAGE_SIZE")
    vector_search_top_k: int = Field(default=100, env="VECTOR_SEARCH_TOP_K")
    similarity_threshold: float = Field(default=0.3, env="SIMILARITY_THRESHOLD")

    # Performance
    databricks_connection_timeout: int = Field(default=30, env="DATABRICKS_CONNECTION_TIMEOUT")
    databricks_read_timeout: int = Field(default=60, env="DATABRICKS_READ_TIMEOUT")
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")

    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    enable_request_logging: bool = Field(default=True, env="ENABLE_REQUEST_LOGGING")
    slow_query_threshold_ms: int = Field(default=2000, env="SLOW_QUERY_THRESHOLD_MS")

    class Config:
        env_file = ".env"
        case_sensitive = False

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "allowed_origins":
                return [x.strip() for x in raw_val.split(",")]
            return raw_val

    @property
    def databricks_url(self) -> str:
        """Full Databricks workspace URL — strips any accidental https:// prefix from env var"""
        host = self.databricks_host.rstrip("/")
        if host.startswith("https://") or host.startswith("http://"):
            return host
        return f"https://{host}"

    @property
    def gold_table(self) -> str:
        """Full path to the Gold product search catalog table"""
        return f"{self.unity_catalog_name}.{self.unity_schema_name}.product_search_catalog"

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
