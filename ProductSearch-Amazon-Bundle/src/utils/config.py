# =====================================================================
# Product Search Amazon — Utils: Configuration Resolution
# =====================================================================

import os
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_amazon_config(key: str, default: Any = None) -> Any:
    """
    Resolves configuration values with priority:
      1. Environment variable
      2. Default value
    """
    env_key = f"AMAZON_{key.upper()}"
    return os.getenv(env_key, default)


def get_embedding_config() -> Dict[str, Any]:
    """Returns the embedding model configuration."""
    return {
        "model_name": get_amazon_config("EMBEDDING_MODEL", "databricks-bge-large-en"),
        "endpoint": get_amazon_config("EMBEDDING_ENDPOINT", "databricks-bge-large-en"),
        "dimension": int(get_amazon_config("EMBEDDING_DIMENSION", "1024")),
        "max_input_length": int(get_amazon_config("MAX_INPUT_LENGTH", "8192")),
    }


def get_search_config() -> Dict[str, Any]:
    """Returns search pipeline configuration."""
    return {
        "default_num_results": int(get_amazon_config("DEFAULT_NUM_RESULTS", "10")),
        "min_score": float(get_amazon_config("MIN_SCORE", "0.0")),
        "hybrid_keyword_weight": float(get_amazon_config("KEYWORD_WEIGHT", "0.3")),
        "hybrid_semantic_weight": float(get_amazon_config("SEMANTIC_WEIGHT", "0.7")),
        "max_query_length": int(get_amazon_config("MAX_QUERY_LENGTH", "512")),
    }