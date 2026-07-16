# Enterprise Extensions Data Quality Improvements

## Problem Analysis

After reviewing the generated enterprise extension data, we identified three critical quality issues that would negatively impact semantic search and LLM-based retrieval:

### 1. **Repetitive Review Summaries** ❌
**Before:**
```
Product A (rating 4.5): "Highly rated by customers who praise its exceptional quality and durability..."
Product B (rating 4.5): "Highly rated by customers who praise its exceptional quality and durability..."
Product C (rating 4.5): "Highly rated by customers who praise its exceptional quality and durability..."
```

**Problem:** Nearly identical template text for products with similar ratings adds no semantic diversity to embeddings.

### 2. **Low-Quality Keywords** ❌
**Before:**
```
"and, bed frame, bedroom, bedroom furniture, beds, slow slow cookers, home home improvement"
```

**Problems:**
- Contains stopwords: "and", "by", "for", "all"
- Duplicated terms: "slow slow cookers", "home home improvement"
- Hierarchy repetition: entire category path included
- Low signal-to-noise ratio

### 3. **Missing Rich Searchable Content** ❌
**Before:** No consolidated field combining product name, description, category, and attributes for embedding generation.

---

## Solution: Improved Data Generation

### ✅ 1. Simplified Review Summary Table
**Changed from:** Template-based summaries with repetitive prose  
**Changed to:** Clean numeric metadata only

**New Schema:**
```csv
review_summary_id, product_id, average_rating, rating_count, sentiment_score
```

**Benefits:**
- No synthetic text pollution
- Preserves actual rating data
- Can be used for metadata filtering
- No embedding quality degradation

---

### ✅ 2. High-Quality Keywords
**Improvements:**
- **Stopword removal**: Filters out "and", "or", "the", "a", "by", "for", etc.
- **Deduplication**: Prevents repeated terms
- **Leaf category only**: Uses most specific category level instead of full hierarchy
- **Focused synonyms**: Only adds meaningful product-specific alternatives

**After:**
```
"beds, bedstead, frame, mattress base, platform, twin"
"cookers, crockpot, electric cooker, multi cooker, slow"
"bathroom, bathroom sink, powder room, sink cabinet, vanities"
```

**Code changes:**
```python
STOPWORDS = {
    "and", "or", "the", "a", "an", "by", "for", "with", "to", "of", "in", "on", "at", 
    "from", "browse", "all", "shop"
}

# Only use leaf category instead of full path
if cat_parts:
    leaf_category = cat_parts[-1]  # e.g., "Twin Beds" instead of "Furniture / Bedroom / Beds / Twin Beds"
```

---

### ✅ 3. Rich Searchable Text Field (NEW)
**Added to:** `product_master.csv`

**Purpose:** Deterministically combines real product information for high-quality embeddings

**Formula:**
```
Product Name | Product Class | Leaf Category | Description (truncated) | Top 5 Attributes
```

**Example Output:**
```
"solid wood platform bed | Beds | Twin Beds | good, deep sleep can be quite 
difficult to have in this busy age. fortunately, there's an antidote to such 
a problem: a nice, quality bed frame like the acacia kaylin. solidly constructed 
from | Width: 64.7 in, Height: 25.35 in, Weight: 500 lbs, Length: 77.9 in"
```

**Benefits:**
- **High diversity**: Each product generates unique text from its actual attributes
- **No hallucination**: Uses only real data from source files
- **Rich semantic content**: Combines multiple information sources
- **Embedding-ready**: Can be directly used for vector generation

---

## Table Usage Recommendations

| Table | Keep? | Use in Embedding? | Primary Use Case |
|-------|-------|-------------------|------------------|
| **Category** | ✅ Yes | ✅ Yes (via searchable_text) | Category hierarchy, navigation |
| **Product Attributes** | ✅ Yes | ✅ Yes (via searchable_text) | Structured filtering, display |
| **Product Master** | ✅ Yes | ✅ Yes (searchable_text field) | **PRIMARY EMBEDDING SOURCE** |
| **Product Pricing** | ✅ Yes | ❌ No | Metadata filter (price range, bucket) |
| **Brand** | ✅ Yes | ❌ No | Metadata filter (brand name) |
| **Product Keywords** | ⚠️ Optional | ⚠️ Optional | Synonym expansion, exact match |
| **Product Review Summary** | ✅ Yes | ❌ No | Metadata filter (rating, sentiment) |

---

## Recommended Embedding Strategy

### Gold Layer `searchable_products` Table
Combine core product data with enterprise extensions:

```sql
CREATE OR REPLACE TABLE gold.searchable_products AS
SELECT 
  p.product_id,
  p.product_name,
  p.product_class,
  p.product_description,
  c.category_name,
  b.brand_name,
  pm.searchable_text,  -- NEW: Rich semantic content
  pr.list_price,
  pr.selling_price,
  pr.price_bucket,
  rs.average_rating,
  rs.sentiment_score,
  pk.keywords  -- Optional: for synonym expansion
FROM product p
JOIN product_master pm ON p.product_id = pm.product_id
JOIN category c ON pm.category_id = c.category_id
JOIN brand b ON pm.brand_id = b.brand_id
JOIN product_pricing pr ON p.product_id = pr.product_id
JOIN product_review_summary rs ON p.product_id = rs.product_id
LEFT JOIN product_keywords pk ON p.product_id = pk.product_id
```

### Vector Generation
```python
# Primary embedding field
embedding_text = row["searchable_text"]

# Optional: Append keywords for synonym coverage
if include_keywords:
    embedding_text += f" | Keywords: {row['keywords']}"

vector = embedding_model.encode(embedding_text)
```

### Metadata Filtering
```python
filters = {
    "price_bucket": ["Budget", "Mid-range"],  # From product_pricing
    "brand_name": ["Wayfair", "Ikea"],        # From brand
    "category_name": "Bedroom Furniture",     # From category
    "min_rating": 4.0,                        # From product_review_summary
    "sentiment_score": {"$gte": 0.5}          # From product_review_summary
}
```

---

## Impact Summary

### Before
- 42,994 products with **repetitive review text**
- Keywords cluttered with **stopwords and duplicates**
- No **consolidated searchable field**

### After
- 42,994 products with **unique, rich searchable_text**
- Clean keywords: **signal-focused, no stopwords**
- Review data: **numeric metadata only (no template pollution)**

### Expected Retrieval Improvements
1. **Better semantic diversity** → Improved embedding separation
2. **Higher signal-to-noise** → More accurate similarity matching
3. **No synthetic repetition** → Reduced false positives
4. **Richer context per product** → Better LLM understanding

---

## Files Changed

1. **`generate_enterprise_extensions.py`**
   - Added `generate_searchable_text()` function
   - Refactored `generate_review_summary()` to return numeric data only
   - Improved `generate_keywords()` with stopword filtering and deduplication
   - Updated `product_master.csv` schema to include `searchable_text` column
   - Updated `product_review_summary.csv` schema (removed text columns)

---

## Next Steps

1. **Update Databricks notebooks** to read new `searchable_text` column
2. **Regenerate embeddings** using `searchable_text` as primary input
3. **Test retrieval quality** with diverse queries
4. **Consider reducing dataset size** to 1,000-5,000 products if needed (quality > quantity)
5. **Evaluate keyword usage** - may be optional given rich searchable_text

---

## Quality Validation

Run these checks on the new data:

```python
# Check searchable_text diversity
df['searchable_text'].nunique() / len(df)  # Should be ~1.0 (unique per product)

# Check keyword quality
df['keywords'].str.contains('and|the|for|with').sum()  # Should be 0

# Check review summary schema
df[['average_rating', 'rating_count', 'sentiment_score']].dtypes  # All numeric

# Sample searchable_text examples
df[['product_name', 'searchable_text']].sample(10)
```
