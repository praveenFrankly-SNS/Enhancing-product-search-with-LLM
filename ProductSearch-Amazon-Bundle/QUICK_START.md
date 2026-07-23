# Quick Start Guide - Fixing Silent Failures

## Problem Summary
Your Product Search pipeline is failing silently. Many operations return error dictionaries instead of raising exceptions, making it hard to identify what's wrong.

## Quick Diagnostic (5 minutes)

### Step 1: Run Diagnostic Script
In a Databricks notebook, run:
```python
%run "./DIAGNOSTIC_SCRIPT"
```

This will:
- ✅ Check environment setup
- ✅ Verify library imports
- ✅ Check Vector Search SDK availability
- ✅ Validate data structures
- ✅ Check search capabilities
- ✅ Generate comprehensive report

## Common Issues & Quick Fixes

### Issue 1: Vector Search SDK Not Available
**Error**: `ModuleNotFoundError: No module named 'databricks.vector_search'`

**Quick Fix** (Run in notebook):
```python
%pip install databricks-vector-search
dbutils.library.restartPython()
```

**Verify**:
```python
from databricks.vector_search.client import VectorSearchClient
print("✅ Vector Search SDK installed successfully")
```

---

### Issue 2: Vector Search Operations Failing Silently
**Symptom**: Pipeline says "succeeded" but no index created

**Root Cause**: Error dictionaries returned instead of raised

**Quick Fix**: Update `notebooks/06_vector_search_index.py`
```python
# Add after result is returned
if result.get("status") == "error":
    raise RuntimeError(f"Vector index operation failed: {result['error']}")

# Add for status checking
print(f"✅ Vector Search Operation: {result['status'].upper()}")
print(f"   Index: {result['index_name']}")
print(f"   Endpoint: {result['endpoint_name']}")
```

---

### Issue 3: Search Returns Empty Results Silently
**Symptom**: Search runs but returns 0 results without error

**Quick Fix**: Update `notebooks/08_semantic_search_pipeline.py`
```python
# Add data validation
if len(results) == 0:
    print("⚠️  WARNING: Search returned no results!")
    print("   Checking data availability...")
    
    # Verify table exists
    table_count = spark.table(f"`{catalog}`.gold.amazon_product_catalog").count()
    print(f"   Products in catalog: {table_count}")
    
    if table_count == 0:
        raise ValueError("No products in gold table")

# Validate result structure
for result in results:
    assert "product_id" in result, "Missing product_id"
    assert "product_name" in result, "Missing product_name"
```

---

### Issue 4: Pipeline Task Fails But Looks Like Success
**Symptom**: E2E pipeline shows green but downstream tasks fail

**Root Cause**: Intermediate tasks return errors in dictionaries

**Quick Fix**: Wrap operations in error checking
```python
def safe_operation(func, *args, **kwargs):
    """Wrap operations to fail loudly"""
    try:
        result = func(*args, **kwargs)
        
        # Check if result is error dictionary
        if isinstance(result, dict):
            if result.get("status") == "error":
                raise RuntimeError(f"Operation failed: {result.get('error')}")
        
        return result
    except Exception as e:
        print(f"❌ Operation failed: {str(e)}")
        raise

# Usage
result = safe_operation(create_or_sync_amazon_vector_index, ...)
```

---

## Step-by-Step Fix Process

### Step 1: Run Diagnostics (5 min)
```python
%run "./DIAGNOSTIC_SCRIPT"
```

Expected output:
- Environment: ✅ OK
- Libraries: ✅ OK  
- Vector Search SDK: ❌ Not installed OR ⚠️ Issues
- Spark: ✅ OK
- Data structures: ✅ OK
- Search functions: ✅ Available

### Step 2: Fix Identified Issues (5-15 min)
Based on diagnostic results, fix in order:

1. **If Vector Search SDK missing**:
   ```python
   %pip install databricks-vector-search
   dbutils.library.restartPython()
   ```

2. **If data structures missing**:
   ```python
   # Run notebook 01_setup_platform.py
   %run "./notebooks/01_setup_platform"
   ```

3. **If search functions fail**:
   - Check Python path: `sys.path`
   - Verify `src/` folder structure
   - Run tests: `%run "./tests/unit/test_ingestion_framework"`

### Step 3: Run Pipeline with Validation (10 min)
```python
# Run the full pipeline with error checking enabled
%run "./notebooks/00_run_amazon_pipeline"
```

Monitor for:
- ✅ Each step completes or raises explicit error
- ✅ No "operation completed successfully" with error status
- ✅ All downstream tasks receive valid data

### Step 4: Verify Results (5 min)
```python
# Check vector index
from src.search.vector_index import get_index_stats
stats = get_index_stats(catalog="product_search_dev")
print(stats)

# Test search
from src.search.search_pipeline import execute_sql_keyword_search
results = execute_sql_keyword_search("USB cable", "product_search_dev", num_results=5)
print(f"Found {len(results)} results")
for r in results:
    print(f"  - {r.get('product_name')}")
```

---

## Files Modified/Created

| File | Purpose | Status |
|------|---------|--------|
| `INTEGRATION_PLAN.md` | Complete integration guide | 📄 NEW |
| `DIAGNOSTIC_SCRIPT.py` | Automated diagnostics | 📄 NEW |
| `QUICK_START.md` | This file | 📄 NEW |
| `src/search/vector_index.py` | Vector index manager | ✅ FIXED |
| `src/search/search_pipeline.py` | Search execution | ✅ FIXED |
| `notebooks/06_vector_search_index.py` | Index setup notebook | ⏳ NEEDS ERROR CHECKS |
| `notebooks/08_semantic_search_pipeline.py` | Search notebook | ⏳ NEEDS VALIDATION |

---

## Testing Checklist

- [ ] Run `DIAGNOSTIC_SCRIPT.py` - shows no critical errors
- [ ] Install Vector Search SDK if needed
- [ ] Run `00_run_amazon_pipeline` - no silent failures
- [ ] Check `vector_search_index` notebook - explicit error messages
- [ ] Test search functions - return valid results or clear errors
- [ ] Verify fallback to SQL search - works when Vector Search unavailable
- [ ] Run full E2E pipeline - all tasks complete or fail explicitly

---

## Success Criteria

✅ **All tests pass when:**
1. Diagnostic shows all ✅ or ⚠️ (no ❌)
2. Pipeline runs end-to-end without silent failures
3. Search returns results or explicit error messages
4. Vector index is created/synced successfully
5. Fallback search works if Vector Search unavailable
6. All error messages are clear and actionable

---

## Need Help?

### Check These Files First
1. `INTEGRATION_PLAN.md` - Full architecture and integration guide
2. `DIAGNOSTIC_SCRIPT.py` - Auto-diagnose issues
3. Vector Search notebook output - Look for error dictionaries

### Common Solutions

| Problem | Solution |
|---------|----------|
| SDK not installed | `%pip install databricks-vector-search` |
| Data not found | Run `01_setup_platform` then `02_ingest_amazon_csv` |
| Search fails silently | Check vector_index status with diagnostic |
| Results empty | Verify data in `gold.amazon_product_catalog` |
| Endpoint not found | Check if `shared_vs_endpoint` exists in Databricks |

---

## Next Steps After Fixing

1. ✅ Run end-to-end pipeline successfully
2. ✅ Integrate with Product Recommendation bundle (optional)
3. ✅ Set up monitoring and evaluation
4. ✅ Deploy search service
5. ✅ A/B test search vs. recommendations

