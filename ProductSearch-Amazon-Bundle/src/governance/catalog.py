# =====================================================================
# Product Search Amazon — Governance: Unity Catalog Provisioner
# =====================================================================

from pyspark.sql import SparkSession


def ensure_catalog_and_schemas(spark: SparkSession, catalog: str):
    """
    Creates target Unity Catalog catalog and medallion schemas if missing.
    """
    print(f"🔒 Ensuring Unity Catalog '{catalog}' exists...")
    spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
    
    schemas = ["bronze", "silver", "gold", "operations"]
    for s in schemas:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{s}`")
        print(f"  └─ Schema `{catalog}`.`{s}` verified.")
