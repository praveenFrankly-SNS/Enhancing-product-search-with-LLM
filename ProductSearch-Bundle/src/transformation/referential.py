# =====================================================================
# Product Search — Ingestion: Referential Integrity Validation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def validate_referential_integrity(
    tables_dict: Dict[str, DataFrame],
    run_id: str
) -> Tuple[Dict[str, DataFrame], List[Dict]]:
    """
    Validates PK-FK associations across all conformed tables.
    Returns (cleaned_tables_dict, list_of_violations).
    """
    violations = []
    cleaned_tables = dict(tables_dict)
    
    # 1. Label referential integrity (query_id exists in Query, product_id exists in Product)
    if "label" in cleaned_tables and "product" in cleaned_tables and "query" in cleaned_tables:
        label_df = cleaned_tables["label"]
        prod_keys = cleaned_tables["product"].select("product_id").distinct()
        query_keys = cleaned_tables["query"].select("query_id").distinct()
        
        # Check product_id
        orphan_prods = label_df.join(prod_keys, "product_id", "left_anti")
        orphan_prod_cnt = orphan_prods.count()
        if orphan_prod_cnt > 0:
            for row in orphan_prods.limit(100).collect():
                violations.append({
                    "rejection_id": str(uuid.uuid4()),
                    "run_id": run_id,
                    "run_date": datetime.now(timezone.utc).date(),
                    "source_table": "label",
                    "rule_name": "label_fk_product",
                    "violation_reason": f"product_id '{row['product_id']}' not found in product catalog",
                    "record_key": str(row["id"]),
                    "created_at": datetime.now(timezone.utc)
                })
                
        # Check query_id
        orphan_queries = label_df.join(query_keys, "query_id", "left_anti")
        orphan_query_cnt = orphan_queries.count()
        if orphan_query_cnt > 0:
            for row in orphan_queries.limit(100).collect():
                violations.append({
                    "rejection_id": str(uuid.uuid4()),
                    "run_id": run_id,
                    "run_date": datetime.now(timezone.utc).date(),
                    "source_table": "label",
                    "rule_name": "label_fk_query",
                    "violation_reason": f"query_id '{row['query_id']}' not found in query catalog",
                    "record_key": str(row["id"]),
                    "created_at": datetime.now(timezone.utc)
                })
                
        # Clean label table
        cleaned_tables["label"] = label_df.join(prod_keys, "product_id", "inner").join(query_keys, "query_id", "inner")

    # 2. Extension tables references to Product (product_master, product_pricing, product_attributes, product_review_summary)
    extensions = ["product_master", "product_pricing", "product_attributes", "product_review_summary"]
    if "product" in cleaned_tables:
        prod_keys = cleaned_tables["product"].select("product_id").distinct()
        for ext in extensions:
            if ext in cleaned_tables:
                ext_df = cleaned_tables[ext]
                orphans = ext_df.join(prod_keys, "product_id", "left_anti")
                orphan_cnt = orphans.count()
                
                # Determine identification columns
                key_col = "product_id" if ext in ["product_master", "product_review_summary"] else ("price_id" if ext == "product_pricing" else "attribute_id")
                
                if orphan_cnt > 0:
                    for row in orphans.limit(100).collect():
                        violations.append({
                            "rejection_id": str(uuid.uuid4()),
                            "run_id": run_id,
                            "run_date": datetime.now(timezone.utc).date(),
                            "source_table": ext,
                            "rule_name": f"{ext}_fk_product",
                            "violation_reason": f"product_id '{row['product_id']}' not found in product catalog",
                            "record_key": str(row[key_col]),
                            "created_at": datetime.now(timezone.utc)
                        })
                # Clean extension table
                cleaned_tables[ext] = ext_df.join(prod_keys, "product_id", "inner")
                
    # 3. Category parent-child hierarchy checks
    if "category" in cleaned_tables:
        cat_df = cleaned_tables["category"]
        parent_cats = cat_df.select(F.col("category_id").alias("parent_category_id")).distinct()
        
        # Check that parent_category_id resolves to an existing category
        orphans = cat_df.filter(F.col("parent_category_id").isNotNull()).join(parent_cats, "parent_category_id", "left_anti")
        orphan_cnt = orphans.count()
        if orphan_cnt > 0:
            for row in orphans.limit(100).collect():
                violations.append({
                    "rejection_id": str(uuid.uuid4()),
                    "run_id": run_id,
                    "run_date": datetime.now(timezone.utc).date(),
                    "source_table": "category",
                    "rule_name": "category_fk_parent",
                    "violation_reason": f"parent_category_id '{row['parent_category_id']}' not found in category table",
                    "record_key": str(row["category_id"]),
                    "created_at": datetime.now(timezone.utc)
                })
            
            # Nullify parent link if it is broken rather than dropping the category
            valid_cats = cat_df.select("category_id")
            cleaned_tables["category"] = cat_df.withColumn(
                "parent_category_id",
                F.when(F.col("parent_category_id").isin(valid_cats), F.col("parent_category_id")).otherwise(F.lit(None))
            )
            
    return cleaned_tables, violations
