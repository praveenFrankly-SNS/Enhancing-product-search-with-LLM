# Databricks notebook source
# MAGIC %md
# MAGIC # ✅ Setup & Validation - Run This First!
# MAGIC Complete environment setup and validation before running the main pipeline.
# MAGIC This notebook ensures all prerequisites are met.

# COMMAND ----------
import sys
import traceback
from datetime import datetime

print(f"\n{'='*80}")
print(f"ENVIRONMENT SETUP & VALIDATION")
print(f"{'='*80}\n")

# Track validation results
validation_results = {
    "timestamp": datetime.now().isoformat(),
    "checks": []
}

def check(name, func):
    """Run a validation check"""
    try:
        result = func()
        validation_results["checks"].append({
            "name": name,
            "status": "✅ PASS",
            "details": result
        })
        print(f"✅ {name}: {result}")
        return True
    except Exception as e:
        validation_results["checks"].append({
            "name": name,
            "status": "❌ FAIL",
            "error": str(e)
        })
        print(f"❌ {name}: {str(e)}")
        return False

# ===== ENVIRONMENT CHECKS =====
print("1️⃣  ENVIRONMENT CHECKS")
print("-" * 80)

# Check Python
check("Python Version", lambda: f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Check Spark
def check_spark():
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.getOrCreate()
    return f"Spark {spark.version}"

check("Spark Session", check_spark)

# Check imports
def check_imports():
    try:
        import pandas
        import numpy
        return "All core libraries available"
    except:
        raise Exception("Missing core libraries")

check("Core Libraries", check_imports)

# ===== SDK CHECKS =====
print("\n2️⃣  SDK AVAILABILITY CHECKS")
print("-" * 80)

sdk_available = False
try:
    from databricks.vector_search.client import VectorSearchClient
    sdk_available = True
    check("Vector Search SDK", lambda: "Installed and importable")
except ImportError:
    check("Vector Search SDK", lambda: None)
    print("   ⚠️  Recommendation: %pip install databricks-vector-search")

# ===== DATABRICKS CONNECTIVITY =====
print("\n3️⃣  DATABRICKS CONNECTIVITY CHECKS")
print("-" * 80)

try:
    # Check catalog access
    catalogs = spark.sql("SHOW CATALOGS").collect()
    check("Catalog Access", lambda: f"{len(catalogs)} catalogs found")
    
    # Check product_search_dev catalog
    try:
        tables = spark.sql("SHOW SCHEMAS IN product_search_dev").collect()
        check("product_search_dev Catalog", lambda: f"{len(tables)} schemas found")
    except:
        check("product_search_dev Catalog", lambda: None)
        print("   ℹ️  Will be created by 01_setup_platform")
    
except Exception as e:
    check("Databricks Connectivity", lambda: None)
    print(f"   Error: {str(e)}")

# ===== VECTOR SEARCH ENDPOINT CHECK =====
print("\n4️⃣  VECTOR SEARCH ENDPOINT CHECK")
print("-" * 80)

if sdk_available:
    try:
        from databricks.vector_search.client import VectorSearchClient
        vsc = VectorSearchClient()
        endpoints = vsc.list_endpoints().get("endpoints", [])
        endpoint_names = [ep.get("name") for ep in endpoints]
        
        check("Vector Search Endpoints", lambda: f"{len(endpoints)} endpoint(s) found")
        
        if "shared_vs_endpoint" in endpoint_names:
            check("shared_vs_endpoint", lambda: "Found and ready")
        else:
            print(f"   ℹ️  Available endpoints: {', '.join(endpoint_names)}")
            print(f"   ℹ️  Will use 'shared_vs_endpoint' when available")
            check("shared_vs_endpoint", lambda: None)
    except Exception as e:
        print(f"   ⚠️  Could not check endpoints: {str(e)}")
else:
    print("   ⚠️  Vector Search SDK not available - skipping endpoint check")

# ===== DATA STRUCTURE CHECK =====
print("\n5️⃣  DATA STRUCTURE CHECK")
print("-" * 80)

try:
    # Check dataset folder
    import os
    dataset_path = "../dataset/V2/Amazon.csv"
    if os.path.exists(dataset_path):
        file_size = os.path.getsize(dataset_path)
        check("Dataset File", lambda: f"Found ({file_size/1024/1024:.1f} MB)")
    else:
        check("Dataset File", lambda: None)
        print(f"   Expected: {dataset_path}")
except Exception as e:
    print(f"   Error checking dataset: {str(e)}")

# ===== PYTHON PATH CHECK =====
print("\n6️⃣  PYTHON PATH CHECK")
print("-" * 80)

try:
    # Check if src folder is accessible
    import importlib.util
    spec = importlib.util.find_spec("src")
    if spec:
        check("Python Module Path", lambda: "src module found")
    else:
        print("   ℹ️  Attempting to add workspace to sys.path")
        check("Python Module Path", lambda: None)
except Exception as e:
    print(f"   Note: {str(e)}")

# ===== SUMMARY =====
print(f"\n{'='*80}")
print("VALIDATION SUMMARY")
print(f"{'='*80}\n")

passed = len([c for c in validation_results["checks"] if c["status"] == "✅ PASS"])
failed = len([c for c in validation_results["checks"] if c["status"] == "❌ FAIL"])
total = passed + failed

print(f"📊 Results:")
print(f"  - Total checks: {total}")
print(f"  - ✅ Passed: {passed}")
print(f"  - ❌ Failed: {failed}")
print(f"  - Success rate: {(passed/total*100):.0f}%")

if failed == 0:
    print(f"\n✅ ALL CHECKS PASSED - Ready to run pipeline!")
    print(f"\n🚀 Next steps:")
    print(f"   1. Run: %run ./00_run_amazon_pipeline")
    print(f"   2. This will execute the full end-to-end pipeline")
    print(f"   3. Check the output for any warnings or errors")
else:
    print(f"\n⚠️  SOME CHECKS FAILED - See recommendations below:")
    
    failed_checks = [c for c in validation_results["checks"] if c["status"] == "❌ FAIL"]
    for check_item in failed_checks:
        print(f"\n  • {check_item['name']}")
        if "error" in check_item:
            print(f"    Error: {check_item['error']}")
        print(f"    Recommendation: Investigate and fix before running pipeline")

print(f"\n{'='*80}\n")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Installation Guide (if needed)
# MAGIC 
# MAGIC If Vector Search SDK is not available, run this in a notebook cell:
# MAGIC ```python
# MAGIC %pip install databricks-vector-search
# MAGIC dbutils.library.restartPython()
# MAGIC ```
# MAGIC 
# MAGIC Then re-run this validation notebook.

# COMMAND ----------
# MAGIC %md
# MAGIC ## Quick Troubleshooting
# MAGIC 
# MAGIC ### SDK Installation Issues
# MAGIC - Ensure you're on Databricks Runtime 13.1 or later
# MAGIC - Use: `%pip install --upgrade databricks-vector-search`
# MAGIC 
# MAGIC ### Data Structure Issues
# MAGIC - Dataset should be at: `../dataset/V2/Amazon.csv`
# MAGIC - Size should be > 1 MB
# MAGIC 
# MAGIC ### Python Module Issues
# MAGIC - The `src/` folder should be in the workspace root
# MAGIC - Run from a notebook in the same workspace directory
