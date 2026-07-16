# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Embedding Generation Pipeline (Placeholder)
# MAGIC **Responsibility**: Exposes a structured placeholder task where dense embeddings will be generated for the `searchable_text` attribute and index synchronization will occur.
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
from pathlib import Path
from pyspark.sql import SparkSession

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
from src.shared.constants import GOLD
from src.shared.logger import get_logger
# COMMAND ----------
# Initialize Spark
spark = SparkSession.builder.getOrCreate()
logger = get_logger("generate_embeddings")
# COMMAND ----------
# Setup widgets
dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment", "dev", "Environment (dev/staging/prod)")

config = get_config(dbutils)
catalog = config.catalog

logger.info(f"Checking access to Gold Product Search Catalog in catalog: {catalog}...")
# COMMAND ----------
# Read sample records
catalog_df = spark.table(f"{catalog}.{GOLD}.product_search_catalog")
records_count = catalog_df.count()
logger.info(f"Gold Product Search Catalog contains {records_count} rows ready for embedding.")

# Display a preview of the composed searchable_text
display(catalog_df.select("product_id", "product_name", "searchable_text").limit(5))
# COMMAND ----------
logger.success("Embedding Generation placeholder verified and completed successfully!")
