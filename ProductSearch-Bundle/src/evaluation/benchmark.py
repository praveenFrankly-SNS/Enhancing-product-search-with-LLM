# =====================================================================
# Product Search — Evaluation: Benchmark Loader
# =====================================================================

from pyspark.sql import SparkSession

def load_benchmark_queries(spark: SparkSession, catalog: str, gold_schema: str) -> list:
    """
    Loads WANDS benchmark queries from the Gold query table.
    """
    df = spark.table(f"{catalog}.{gold_schema}.query")
    rows = df.collect()
    return [
        {
            "query_id": str(r["query_id"]),
            "original_query": str(r["original_query"]),
            "normalized_query": str(r["normalized_query"])
        }
        for r in rows
    ]

def load_relevance_labels(spark: SparkSession, catalog: str, gold_schema: str) -> dict:
    """
    Loads conformed relevance labels and scores from the Gold label table.
    Returns: {query_id: {product_id: label_score}}
    """
    df = spark.table(f"{catalog}.{gold_schema}.label")
    rows = df.collect()
    
    labels_map = {}
    for r in rows:
        qid = str(r["query_id"])
        pid = str(r["product_id"])
        score = float(r["label_score"])
        
        if qid not in labels_map:
            labels_map[qid] = {}
        labels_map[qid][pid] = score
        
    return labels_map

def load_product_names_map(spark: SparkSession, catalog: str, gold_schema: str) -> dict:
    """
    Loads product ID to name map from the Gold product search catalog.
    Returns: {product_id: product_name}
    """
    df = spark.table(f"{catalog}.{gold_schema}.product_search_catalog")
    rows = df.select("product_id", "product_name").collect()
    return {str(r["product_id"]): str(r["product_name"]) for r in rows}
