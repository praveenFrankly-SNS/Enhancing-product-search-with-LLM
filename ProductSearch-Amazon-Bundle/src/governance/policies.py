# =====================================================================
# Product Search Amazon — Governance: Security & Data Masking Policies
# =====================================================================

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def mask_sensitive_user_info(df: DataFrame) -> DataFrame:
    """Masks user_id and user_name fields if present for PII governance compliance."""
    res = df
    if "user_id" in res.columns:
        res = res.withColumn("user_id", F.sha2(F.col("user_id"), 256))
    if "user_name" in res.columns:
        res = res.withColumn("user_name", F.lit("[REDACTED]"))
    return res
