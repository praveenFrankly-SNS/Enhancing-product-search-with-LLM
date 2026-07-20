# =====================================================================
# Product Search Amazon — Ingestion: CSV Reader & Path Resolver
# =====================================================================

import os
import glob
import pandas as pd
from typing import Optional
from pyspark.sql import SparkSession, DataFrame


def resolve_amazon_csv_path(dbutils=None, custom_csv_path: Optional[str] = None) -> str:
    """
    Dynamically locates Amazon.csv in Workspace, Volumes, or custom input path.
    """
    if custom_csv_path and os.path.exists(custom_csv_path):
        return custom_csv_path

    # Check notebook context if dbutils available
    if dbutils:
        try:
            ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
            nb_path = ctx.notebookPath().get()
            full_ws_path = nb_path if nb_path.startswith("/Workspace") else f"/Workspace{nb_path}"
            
            if "/notebooks" in full_ws_path:
                base_dir = full_ws_path.split("/notebooks")[0]
                candidate = f"{base_dir}/dataset/V2/Amazon.csv"
                if os.path.exists(candidate):
                    return candidate
        except Exception:
            pass

    # Workspace directory traversal search fallback
    matches = glob.glob("/Workspace/**/Amazon.csv", recursive=True)
    if matches:
        for m in matches:
            if os.path.exists(m) and os.path.getsize(m) > 1000:
                return m

    # Local filesystem or standard path fallback
    candidates = [
        "/Workspace/dataset/V2/Amazon.csv",
        "dataset/V2/Amazon.csv",
        "../../dataset/V2/Amazon.csv"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    return "/Workspace/dataset/V2/Amazon.csv"


def read_amazon_csv(spark: SparkSession, csv_path: str) -> DataFrame:
    """
    Reads Amazon CSV into a PySpark DataFrame with all columns initially as strings.
    Natively handles both /Workspace paths and DBFS paths.
    """
    if not os.path.exists(csv_path) and not csv_path.startswith("dbfs:") and not csv_path.startswith("/Volumes"):
        raise FileNotFoundError(f"Amazon CSV file not found at path: {csv_path}")

    if csv_path.startswith("/Workspace") or os.path.exists(csv_path):
        # Use pandas for direct workspace path read without DBFS protocol restrictions
        pdf = pd.read_csv(csv_path, dtype=str)
        df = spark.createDataFrame(pdf.fillna(""))
    else:
        # Standard Spark CSV reader for DBFS / Volumes
        df = spark.read.format("csv") \
            .option("header", "true") \
            .option("inferSchema", "false") \
            .load(csv_path)
        
        # Replace Nulls with empty string for raw consistency
        df = df.fillna("")

    return df
