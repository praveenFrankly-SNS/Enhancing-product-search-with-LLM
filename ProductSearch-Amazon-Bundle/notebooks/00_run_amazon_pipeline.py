# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 Master Amazon Pipeline Orchestrator
# MAGIC **Purpose**: Run the complete Amazon Product Search end-to-end pipeline with error tracking and validation.

# COMMAND ----------
import traceback
from datetime import datetime

# Pipeline execution tracker
pipeline_status = {
    "start_time": datetime.now().isoformat(),
    "steps": [],
    "failed_steps": [],
    "warnings": []
}

def run_step(step_num, step_name, notebook_path):
    """Run a pipeline step with error tracking"""
    print(f"\n{'='*80}")
    print(f"Step {step_num}: {step_name}")
    print(f"{'='*80}")
    
    try:
        dbutils.notebook.run(notebook_path, timeout_seconds=3600)
        
        pipeline_status["steps"].append({
            "num": step_num,
            "name": step_name,
            "status": "✅ SUCCESS",
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"✅ Step {step_num} completed successfully")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Step {step_num} FAILED: {error_msg}")
        print(f"Traceback:\n{traceback.format_exc()}")
        
        pipeline_status["steps"].append({
            "num": step_num,
            "name": step_name,
            "status": "❌ FAILED",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        })
        
        pipeline_status["failed_steps"].append({
            "num": step_num,
            "name": step_name,
            "error": error_msg
        })
        
        return False

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 0: Validate Environment
# COMMAND ----------
run_step(0, "Validate Environment", "./00_validate_environment")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 1: Setup Unity Catalog Platform & Schemas
# COMMAND ----------
run_step(1, "Setup Platform", "./01_setup_platform")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 2: Ingest Raw Amazon CSV (Bronze)
# COMMAND ----------
run_step(2, "Ingest Amazon CSV", "./02_ingest_amazon_csv")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 3: Bronze to Silver Medallion Transformation
# COMMAND ----------
run_step(3, "Bronze to Silver", "./03_bronze_to_silver")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 4: Gold Feature Engineering (Catalog & Search Document)
# COMMAND ----------
run_step(4, "Feature Engineering", "./04_feature_engineering")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 5: Verify Embeddings Document Readiness
# COMMAND ----------
run_step(5, "Generate Embeddings", "./05_generate_embeddings")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 6: Create & Sync Delta Vector Search Index
# COMMAND ----------
run_step(6, "Vector Search Index", "./06_vector_search_index")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 7: Query Understanding & Term Expansion
# COMMAND ----------
run_step(7, "Query Understanding", "./07_query_understanding")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 8: Execute Hybrid & Semantic Search Pipeline
# COMMAND ----------
run_step(8, "Semantic Search", "./08_semantic_search_pipeline")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 9: Search Relevance Evaluation & MLflow Logging
# COMMAND ----------
run_step(9, "Search Evaluation", "./09_search_evaluation")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 10: System Observability & Health Check
# COMMAND ----------
run_step(10, "Monitoring Healthcheck", "./10_monitoring_healthcheck")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 11: Governance & Security Validation
# COMMAND ----------
run_step(11, "Governance Validation", "./11_governance_validation")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 12: Pipeline Completion Report
# COMMAND ----------
print(f"\n{'='*80}")
print(f"PIPELINE EXECUTION REPORT")
print(f"{'='*80}\n")

# Count successes and failures
successful = len([s for s in pipeline_status["steps"] if "SUCCESS" in s["status"]])
failed = len(pipeline_status["failed_steps"])
total = successful + failed

print(f"📊 Summary:")
print(f"  - Total steps: {total}")
print(f"  - ✅ Successful: {successful}")
print(f"  - ❌ Failed: {failed}")
print(f"  - Success rate: {(successful/total*100):.1f}%" if total > 0 else "  - No steps executed")

print(f"\n📋 Step-by-Step Status:")
for step in pipeline_status["steps"]:
    print(f"  Step {step['num']}: {step['name']:30} → {step['status']}")

if pipeline_status["failed_steps"]:
    print(f"\n❌ Failed Steps (Detailed):")
    for step in pipeline_status["failed_steps"]:
        print(f"\n  Step {step['num']}: {step['name']}")
        print(f"  Error: {step['error'][:100]}...")
else:
    print(f"\n✅ All steps completed successfully!")

print(f"\n{'='*80}")

# Final status
if failed == 0:
    print("✅ PIPELINE EXECUTION SUCCESSFUL")
    print(f"\nNext steps:")
    print(f"  1. Review search results in Step 8")
    print(f"  2. Check evaluation metrics in Step 9")
    print(f"  3. Verify monitoring health in Step 10")
    print(f"  4. Deploy search service for production use")
else:
    print(f"❌ PIPELINE EXECUTION FAILED - {failed} step(s) failed")
    print(f"\nActions to take:")
    print(f"  1. Review error messages above")
    print(f"  2. Fix identified issues")
    print(f"  3. Re-run the pipeline")
    print(f"  4. Check DIAGNOSTIC_SCRIPT.py for additional insights")

print(f"\n{'='*80}\n")
