# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Feature Engineering Pipeline (AI-Ready Datasets)
# MAGIC **Responsibility**: Loads conformed Silver tables, generates rolled-up attributes summaries, compiles the canonical `searchable_text` embedding input, maps query evaluations, and writes clean Gold datasets.
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Add project root to sys.path to allow imports when run in Databricks context
try:
    notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    project_root = "/Workspace" + notebook_path.split("/notebooks/")[0]
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    except NameError:
        pass

from src.shared.config import get_config
from src.shared.constants import SILVER, GOLD, OPERATIONS
from src.shared.logger import get_logger

# Import feature engineering helper modules
from src.feature_engineering.search_features import (
    calculate_attribute_summary,
    map_label_scores,
    assemble_product_search_catalog,
    validate_search_catalog
)
from src.transformation.quality import log_dq_report
# COMMAND ----------
# Initialize Spark
spark = SparkSession.builder.getOrCreate()
logger = get_logger("gold_features")
# COMMAND ----------
# Setup widgets
dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment", "dev", "Environment (dev/staging/prod)")

config = get_config(dbutils)
catalog = config.catalog
run_id = str(uuid.uuid4())

logger.info(f"Starting Gold Feature Engineering pipeline (Run ID: {run_id})")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Load conformed Silver DataFrames
# COMMAND ----------
products_df = spark.table(f"{catalog}.{SILVER}.product")
pricing_df = spark.table(f"{catalog}.{SILVER}.product_pricing")
master_df = spark.table(f"{catalog}.{SILVER}.product_master")
brands_df = spark.table(f"{catalog}.{SILVER}.brand")
attributes_df = spark.table(f"{catalog}.{SILVER}.product_attributes")
reviews_df = spark.table(f"{catalog}.{SILVER}.product_review_summary")
queries_df = spark.table(f"{catalog}.{SILVER}.query")
labels_df = spark.table(f"{catalog}.{SILVER}.label")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Calculate Attribute summaries and assemble Gold Product Catalog
# COMMAND ----------
logger.info("Computing attribute summaries from product_attributes...")
attribute_summary_df = calculate_attribute_summary(attributes_df)

logger.info("Assembling canonical Gold Product Search Catalog...")
gold_catalog_df = assemble_product_search_catalog(
    products_df=products_df,
    pricing_df=pricing_df,
    master_df=master_df,
    brands_df=brands_df,
    attributes_summary_df=attribute_summary_df,
    reviews_df=reviews_df
)

# Audit searchable_text presence
logger.info("Verifying searchable_text non-null/non-empty constraint...")
try:
    gold_catalog_df = validate_search_catalog(gold_catalog_df)
except ValueError as err:
    logger.error(str(err))
    log_dq_report(
        spark=spark, catalog=catalog, ops_schema=OPERATIONS, run_id=run_id,
        table_name="product_search_catalog", stage="gold",
        records_read=products_df.count(), records_written=0,
        duplicates=0, invalid_records=products_df.count(),
        status="FAILED", error_message=str(err)
    )
    raise err
# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Assemble Gold Query and Label tables for evaluation
# COMMAND ----------
logger.info("Assembling Gold query table...")
gold_queries_df = queries_df.select(
    "query_id",
    F.col("query").alias("original_query"),
    "normalized_query"
)

logger.info("Mapping numeric relevance weights to label table...")
gold_labels_df = map_label_scores(labels_df)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 4. Write Gold Tables
# COMMAND ----------
# Product catalog dataset
t_catalog_start = time.time()
target_catalog = f"{catalog}.{GOLD}.product_search_catalog"
logger.info(f"Writing Gold Product Search Catalog to {target_catalog}...")
gold_catalog_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_catalog)

catalog_written = gold_catalog_df.count()
log_dq_report(
    spark=spark, catalog=catalog, ops_schema=OPERATIONS, run_id=run_id,
    table_name="product_search_catalog", stage="gold", records_read=products_df.count(),
    records_written=catalog_written, duplicates=0, invalid_records=0, status="SUCCESS"
)

# Query dataset
target_query = f"{catalog}.{GOLD}.query"
logger.info(f"Writing Gold query evaluation reference to {target_query}...")
gold_queries_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_query)

# Labels evaluation ground truth dataset
target_label = f"{catalog}.{GOLD}.label"
logger.info(f"Writing Gold evaluation relevance labels to {target_label}...")
gold_labels_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_label)
# COMMAND ----------
logger.success("Gold Feature Engineering pipeline completed successfully for all datasets!")
