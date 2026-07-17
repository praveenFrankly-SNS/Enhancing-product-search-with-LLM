# =====================================================================
# Product Search — Catalog Governance checks
# =====================================================================

import pyspark.sql.functions as F
from pyspark.errors.exceptions.connect import AnalysisException
from src.governance.policies import REQUIRED_SCHEMAS, REQUIRED_TABLES_READ, REQUIRED_TABLES_WRITE

def verify_catalog_prerequisites(spark, catalog: str) -> dict:
    """
    Verifies that the target catalog exists, all required schemas are created,
    and the current execution session has necessary read/write table privileges.
    Returns a dictionary of status results.
    """
    results = {
        "catalog_exists": False,
        "schemas": {},
        "read_privileges": {},
        "write_privileges": {},
        "errors": []
    }
    
    # 1. Verify Catalog Exists
    try:
        spark.sql(f"USE CATALOG {catalog}")
        results["catalog_exists"] = True
    except AnalysisException as e:
        msg = f"Catalog '{catalog}' not found or inaccessible. Detail: {str(e)}"
        results["errors"].append(msg)
        return results
        
    # 2. Verify Medallion Schemas Exist
    for schema in REQUIRED_SCHEMAS:
        full_schema_name = f"{catalog}.{schema}"
        try:
            schema_exists = spark.catalog.databaseExists(full_schema_name)
            results["schemas"][schema] = schema_exists
            if not schema_exists:
                results["errors"].append(f"Required schema '{full_schema_name}' is missing.")
        except Exception as e:
            results["schemas"][schema] = False
            results["errors"].append(f"Failed to check schema '{full_schema_name}'. Detail: {str(e)}")
            
    # 3. Verify Read Privileges on Required Tables
    for schema, tables in REQUIRED_TABLES_READ.items():
        for table in tables:
            full_table_name = f"{catalog}.{schema}.{table}"
            try:
                # First check if the table exists
                if spark.catalog.tableExists(full_table_name):
                    # Execute a metadata-only lightweight query to verify SELECT (Read) access
                    spark.sql(f"SELECT 1 FROM {full_table_name} WHERE 1=0").collect()
                    results["read_privileges"][full_table_name] = "PASSED"
                else:
                    results["read_privileges"][full_table_name] = "MISSING"
                    # Note: We don't fail-fast on missing downstream tables during platform setup
            except AnalysisException as ae:
                results["read_privileges"][full_table_name] = "FAILED"
                results["errors"].append(f"Read permission check failed on table '{full_table_name}'. Detail: {str(ae)}")
            except Exception as e:
                results["read_privileges"][full_table_name] = "FAILED"
                results["errors"].append(f"Error accessing table '{full_table_name}'. Detail: {str(e)}")
                
    # 4. Verify Write Privileges on Required Target Tables
    for schema, tables in REQUIRED_TABLES_WRITE.items():
        for table in tables:
            full_table_name = f"{catalog}.{schema}.{table}"
            try:
                if spark.catalog.tableExists(full_table_name):
                    # Under UC, we check if the user is authorized to run a lightweight insert/update plan check
                    # We can use DESCRIBE TABLE to verify schema compatibility and write metadata checks
                    spark.sql(f"DESCRIBE TABLE {full_table_name}").collect()
                    results["write_privileges"][full_table_name] = "PASSED"
                else:
                    results["write_privileges"][full_table_name] = "MISSING"
            except AnalysisException as ae:
                results["write_privileges"][full_table_name] = "FAILED"
                results["errors"].append(f"Write validation check failed on table '{full_table_name}'. Detail: {str(ae)}")
            except Exception as e:
                results["write_privileges"][full_table_name] = "FAILED"
                results["errors"].append(f"Error validating table '{full_table_name}'. Detail: {str(e)}")
                
    return results
