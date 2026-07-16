**MEDALLION ARCHITECTURE**

**Data Source, Ingestion & Data Analytics — Bronze → Silver → Gold**

*Product Search with Large Language Models (LLMs) — Databricks Solution Accelerator Enhancement | SNS Square*


# **1. Data Source**

## **1.1 Enterprise Retail Database (Supabase PostgreSQL)**

All data for this accelerator — the WANDS benchmark tables and the enterprise extension tables — is consolidated into a single relational source system: an Enterprise Retail Database hosted on Supabase PostgreSQL. This mirrors how a real retailer's product data actually lives (a relational PIM/catalog database) rather than a folder of benchmark CSVs, and reuses the Supabase-as-external-source pattern already established across other accelerators in this program.


| Table | Layer | Description |
| --- | --- | --- |
| product | Core Benchmark (WANDS) | 42,994 candidate products — unmodified. |
| query | Core Benchmark (WANDS) | 480 real customer search queries — unmodified. |
| label | Core Benchmark (WANDS) | 233,448 human relevance judgments — unmodified. |
| product_master | Enterprise Extension | PIM attributes: SKU, brand, category, manufacturer, status, warranty. |
| product_pricing | Enterprise Extension | List/selling price, discount, currency, effective dates. |
| product_attributes | Enterprise Extension | Normalized attribute:value pairs (color, material, size, etc.). |
| product_review_summary | Enterprise Extension | Generated review synopsis and sentiment. |
| brand | Enterprise Extension | Brand reference data. |
| category | Enterprise Extension | Normalized category reference data. |

*Table 1.1 — Source table inventory, Enterprise Retail Database (Supabase PostgreSQL).*

## **1.2 Why a Unified Relational Source**

Enterprise-like architecture — a single relational catalog database is what an actual retailer's search system would ingest from, so the ingestion layer built here is representative of a production integration, not a benchmark-loading script.

JDBC ingestion — Databricks connects to Supabase over a standard JDBC connection, the same mechanism used for the source systems named in the target-state architecture (PIM/OMS).

Easy to extend — new enterprise tables (e.g. inventory, promotions) can be added to the same Postgres instance and picked up by the ingestion job without changing the pattern.

Reusable for future accelerators — this is the same Supabase-as-external-source approach already standardized across the accelerator program, keeping ingestion tooling consistent.


| DESIGN PRINCIPLE Moving WANDS from flat CSV into Postgres is a storage and ingestion change only. The product, query, and label tables are loaded into Supabase byte-for-byte from the published WANDS files — no field is added, removed, or rewritten in transit. Benchmark integrity is a Silver-layer concern (Section 3), not an artifact of where the data is stored. |
| --- |

# **2. Data Ingestion — Bronze Layer**

## **2.1 Ingestion Pattern**

A Databricks Workflows job connects to the Enterprise Retail Database over JDBC on a scheduled cadence and pulls each of the nine source tables into Unity Catalog as Bronze Delta tables. This replaces the current accelerator's one-time notebook download of WANDS CSVs from GitHub with an orchestrated, repeatable ingestion job — the same pattern used for the medallion pipelines across the rest of the program.

## **2.2 Bronze Layer Principles**

Land data exactly as received — no filtering, deduplication, or business-rule transformation happens in Bronze.

Only two additions are permitted at this stage: data-type conversion on ingestion, and metadata columns (ingestion_timestamp, source_system, batch_id) for lineage.

Change Data Feed is enabled on every Bronze table so downstream Silver/Gold layers can process incrementally as source data changes.

Unity Catalog governs every Bronze table with the same lineage, access control, and audit logging as the rest of the platform.

## **2.3 Bronze Table Mapping**


| Source Table (Postgres) | Bronze Table (Delta / Unity Catalog) |
| --- | --- |
| product | bronze_product |
| query | bronze_query |
| label | bronze_label |
| product_master | bronze_product_master |
| product_pricing | bronze_product_pricing |
| product_attributes | bronze_product_attributes |
| product_review_summary | bronze_product_review_summary |
| brand | bronze_brand |
| category | bronze_category |

*Table 2.3 — 1:1 mapping from source tables to Bronze Delta tables; no tables are merged or split at this stage.*

## **2.4 Ingestion Cadence & Known Limitation**

Initial load is a full JDBC extract of all nine tables. Refresh is a scheduled batch pull rather than true log-based CDC streaming — Supabase logical replication is a candidate upgrade if sub-batch freshness is required later, but is out of scope for this phase. This is called out explicitly here rather than implied, so the tech spec does not overstate ingestion freshness.

# **3. Data Analytics — Cleaning & Preprocessing (Silver Layer)**


| GUIDING PRINCIPLE WANDS is a real, human-annotated benchmark. Silver-layer cleaning standardizes and validates structure — it never fabricates, infers, or rewrites the substance of product text, ratings, or queries. Anything that would change what the benchmark measures is deferred to Gold as a clearly-labeled derived feature, never applied in place. |
| --- |

## **3.1 Core Benchmark Cleaning Rules**

### **Product**

Remove duplicate product_id / duplicate product records.

Missing-value handling is rule-based per column, not a blanket fill — see Table 3.1.

Standardize category_hierarchy into explicit category levels (Level 1 / Level 2 / Level 3) for filtering, without altering the original hierarchy string.

Normalize product text (decode HTML entities, collapse whitespace, normalize punctuation/Unicode) into a separate normalized field — the original text is preserved alongside it.

Parse the pipe-delimited product_features string into structured attribute:value rows.

Validate rating bounds: 0 ≤ average_rating ≤ 5; rating_count ≥ 0; review_count ≥ 0.

Remove invalid records: empty product name, invalid/duplicate primary keys, corrupted descriptions.


| Column | Rule | Reason |
| --- | --- | --- |
| product_name | Drop row if NULL | Mandatory for search and display. |
| product_description | Keep NULL, or fall back to product_name if empty | Description may legitimately be absent. |
| product_features | Replace NULL with empty string | Optional field. |
| rating_count | Fill with 0 | No ratings yet is a valid state. |
| average_rating | Keep NULL when rating_count = 0 | Unknown rating is not the same as a zero rating. |
| review_count | Fill with 0 | No reviews yet is a valid state. |
| category_hierarchy | Drop or map to “Unknown” | Mandatory for filtering and navigation. |
| product_class | Map to “Unknown” if NULL | Preserve the product rather than discarding it. |

*Table 3.1 — Missing-value rules, Product. Fabricated values (e.g. defaulting average_rating to 5) are explicitly rejected in favor of a truthful NULL.*

### **Query**

Remove duplicate query_id records.

Normalize the query string (whitespace, casing) into a separate normalized_query field; the original raw query is preserved unchanged for evaluation.

### **Label**

Remove duplicate (query_id, product_id) combinations.

Validate referential integrity: every query_id exists in Query, every product_id exists in Product; drop orphan labels.

Validate label is one of Exact, Partial, or Irrelevant; reject any other value rather than coercing it.

## **3.2 Enterprise Extension Cleaning Rules**


| Table | Cleaning Rules |
| --- | --- |
| product_master | Dedup on product_id; validate product_id exists in Product; standardize product_status to a fixed value set (Active / Discontinued / Out of Stock). |
| product_pricing | Dedup on (product_id, effective_from); validate selling_price ≤ list_price; validate currency is a recognized ISO code; validate date ranges are non-overlapping per product. |
| product_attributes | Dedup on (product_id, attribute_name); normalize attribute_name to a controlled vocabulary (Color, Material, Size, Weight, Capacity, Dimensions). |
| product_review_summary | Dedup on product_id; validate sentiment_score is within its defined range; validate product_id exists in Product. |
| brand | Dedup on brand_id; drop records with a blank brand_name. |
| category | Dedup on category_id; validate parent_category_id, where present, resolves to an existing category (no broken hierarchy links). |

*Table 3.2 — Silver cleaning rules, enterprise extension tables. All six validate referential integrity back to Product via product_id.*

## **3.3 What This Layer Does Not Do**

Does not generate fake reviews, product descriptions, ratings, or search queries.

Does not rewrite or paraphrase WANDS product descriptions or query text.

Does not fill unknown ratings with an assumed value — an unrated product stays unrated.

Anything that looks like enrichment beyond structural cleaning — a combined search string, an attribute rollup, a review synopsis — is a derived Gold-layer feature, produced alongside the original fields rather than in place of them. That boundary is what Section 4 covers.

## **3.4 Silver Pipeline**

**▸  ****Bronze Product / Query / Label / Enterprise Tables (9 tables, raw)**

**▸  ****Remove Duplicates**

**▸  ****Handle Missing Values (rule-based, per Table 3.1)**

**▸  ****Standardize Categories & Normalize Text**

**▸  ****Parse Product Features into Structured Attributes**

**▸  ****Validate Ratings, Prices, and Enterprise-Table Value Ranges**

**▸  ****Validate Referential Integrity (Label → Query/Product; Extensions → Product)**

**▸  ****Remove Invalid Records**


Output: nine Silver Delta tables — one per source table — cleaned and validated, with the original WANDS semantics fully intact.

# **4. Data Analytics — Feature Engineering (Gold Layer)**

Gold is where curated, derived features are built for the embedding and retrieval pipeline. Every Gold feature is additive: it sits alongside the cleaned Silver fields rather than replacing them, so the lineage back to the original WANDS record is never lost.

## **4.1 Gold Product Table — Primary Embedding Source**


| Feature | Used For |
| --- | --- |
| product_id | Lookup / join key |
| search_title | Cleaned product name |
| search_description | Cleaned description |
| search_features | Parsed product features |
| category_path | Normalized category hierarchy — embedding + filter |
| product_class | Filter |
| attribute_summary | Enterprise attributes rolled up into text — embedding |
| review_summary | Generated review synopsis — embedding |
| searchable_text ⭐ | Primary embedding input (see 4.2) |
| brand_name | Filter |
| selling_price | Filter |
| average_rating | Filter |
| review_count | Ranking metadata |

*Table 4.1 — Gold Product schema. Only searchable_text is sent to the embedding model; every other field remains structured metadata for filtering, ranking, and display.*

## **4.2 searchable_text — the Embedding Input**

A single canonical text field assembled from product name, description, category, and the enterprise attribute/review enrichment — one composed string per product, built once in Gold rather than assembled ad hoc at query time:

Product name + cleaned description

Category path (Furniture › Office Furniture › Office Chairs)

attribute_summary — e.g. “Material: Mesh, Color: Black, Height Adjustable, Lumbar Support”, rolled up from product_attributes

review_summary — e.g. “Customers praise comfort and lumbar support; easy assembly”, rolled up from product_review_summary

This keeps the embedding pipeline simple and consistent: read searchable_text, generate embeddings, write to the Vector Search index — with the source of every contributing sentence still traceable back through Gold to a specific Silver field.

## **4.3 Gold Query Table**


| Feature | Used For |
| --- | --- |
| query_id | Primary key |
| original_query | Original user query, preserved for evaluation |
| normalized_query | Cleaned query |
| query_class | Evaluation |
| query_embedding | Generated at search time — not pre-computed |

*Table 4.2 — Gold Query schema. Queries are dynamic and are not embedded during preprocessing; embedding happens at query time.*

## **4.4 Gold Label Table**


| Feature | Used For |
| --- | --- |
| query_id | FK to Query |
| product_id | FK to Product |
| label_score | Exact = 1.0, Partial = 0.75, Irrelevant = 0.0 — used for NDCG / MRR / Recall@k |

*Table 4.3 — Gold Label schema. No feature engineering beyond the documented numeric mapping; this remains the evaluation ground truth.*

## **4.5 Enterprise Table Contributions to Gold**


| Source Table | Gold Contribution |
| --- | --- |
| product_pricing | selling_price + price_bucket — metadata filter only, no embedding. |
| product_attributes | Rolled up into attribute_summary, which is appended into searchable_text. |
| product_review_summary | Rolled up into review_summary, which is appended into searchable_text. |
| brand | brand_name — metadata filter only, no embedding. |
| category | Already merged into category_path; no separate embedding. |

## **4.6 What Flows Where**

**▸  ****Gold Product Catalog**

**▸  ****search_title, search_description, attribute_summary, review_summary, category_path → composed into searchable_text**

**▸  ****searchable_text ⭐ → Embedding Model → product_embedding → Vector Search Index**

**▸  ****product_class, brand_name, selling_price, average_rating → remain structured metadata for filter pushdown and result display**

# **5. End-to-End Pipeline Summary**

**▸  ****Data Source — Enterprise Retail Database (Supabase PostgreSQL), 9 tables**

**▸  ****Bronze — JDBC ingestion, raw + metadata columns, CDF enabled**

**▸  ****Silver — dedup, rule-based cleaning, standardization, referential integrity**

**▸  ****Gold — feature engineering, searchable_text assembled, metadata separated**

**▸  ****Embedding Generation — searchable_text → product_embedding**

**▸  ****Vector Search — hybrid dense + BM25 retrieval**

**▸  ****Reranking / LLM Query Understanding**

**▸  ****Results**


This keeps the pipeline's responsibilities cleanly separated: Bronze proves nothing was lost on ingestion, Silver proves the benchmark stays truthful, and Gold proves every embedding input is traceable back to a real or clearly-labeled enrichment field.
