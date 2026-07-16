**DATASET DOCUMENTATION**

**Product Search with Large Language Models (LLMs)**

*Databricks Solution Accelerator — Enhancement Program | SNS Square*

# **1. Purpose**

This document defines the complete data model that underpins the enhanced Product Search with LLMs accelerator. It has two parts: the original Wayfair Annotation Dataset (WANDS), which supplies the search-relevance benchmark and remains unmodified, and a set of enterprise extension tables that enrich the same product catalog with the structured business attributes a production retail search system requires (price, brand, normalized specifications, and review sentiment).

The two parts are kept architecturally separate throughout this program. The benchmark is used exclusively to score and compare retrieval strategies (NDCG, MRR, Recall@k). The enterprise extension tables are used exclusively to demonstrate production-oriented capabilities — price-constrained filtering, brand/attribute-aware query understanding, and richer semantic search text — without altering the ground truth the benchmark depends on.


| DESIGN PRINCIPLE WANDS is preserved exactly as published. Nothing in the enterprise extension layer is written back into product_name, product_description, product_features, query, or label. All enrichment is joined on product_id from separate tables, and every enriched field carries a documented source (real / extracted / generated) so provenance is always traceable. |
| --- |

# **2. Core Benchmark Dataset — WANDS (Unmodified)**

WANDS (Wayfair Annotation Dataset) is a published, MIT-licensed search-relevance benchmark: 42,994 real Wayfair furniture and home-goods products, 480 real customer search queries, and 233,448 human-annotated query-product relevance judgments. It is the same dataset used by the underlying Databricks Solution Accelerator and is retained here as the evaluation ground truth.

## **2.1 Product**

One row per candidate product. This is the join key for every enterprise extension table below.


| Column | Type | Description |
| --- | --- | --- |
| product_id | String (PK) | Unique identifier for a candidate product. |
| product_name | String | Product title as listed in the Wayfair catalog. |
| product_class | String | Primary product category / type. |
| category_hierarchy | String | Parent category path, "/"-delimited. |
| product_description | String | Full free-text product description. |
| product_features | String | "|"-delimited attribute:value pairs scraped from the catalog — source for the Product Attributes extraction in Section 3.3. |
| rating_count | Integer | Number of ratings recorded for the product. |
| average_rating | Decimal | Mean customer rating (1–5 scale). |
| review_count | Integer | Number of written reviews recorded. |

*Table 2.1 — WANDS product.csv (9 columns, 42,994 rows).*

## **2.2 Query**


| Column | Type | Description |
| --- | --- | --- |
| query_id | String (PK) | Unique identifier for a search query. |
| query | String | Raw customer search string, as typed. |
| query_class | String | Predicted primary product class associated with the query. |

*Table 2.2 — WANDS query.csv (3 columns, 480 rows).*

## **2.3 Label**


| Column | Type | Description |
| --- | --- | --- |
| id | String (PK) | Unique identifier for the annotation record. |
| query_id | String (FK) | References Query.query_id. |
| product_id | String (FK) | References Product.product_id. |
| label | String | Human relevance judgment: Exact, Partial, or Irrelevant. |

*Table 2.3 — WANDS label.csv (4 columns, 233,448 rows). This is the evaluation ground truth for every retrieval and reranking model in this program.*

# **3. Enterprise Extension Tables (Recommended)**

These six tables extend the WANDS product catalog with the structured attributes a production retail search system needs but WANDS does not include. Every table joins to WANDS solely on product_id and is populated using one of three provenance types, recorded per table (and per row, where a table mixes sources):

Real — taken directly from an existing WANDS field (no fabrication).

Extracted — parsed and normalized out of WANDS's existing product_features text using an LLM/rules pass; grounded in real catalog text.

Generated (synthetic) — produced independently of query.csv and label.csv, using category-conditioned, realistic value distributions rather than random values, and explicitly flagged as an enrichment estimate rather than a Wayfair-sourced fact.

No field from this section is ever appended to the text used for embedding or benchmark scoring in Section 2. It is surfaced only in the query-understanding, filtering, and showcase-catalog layers of the accelerator.

## **3.1 Product Master (PIM)**

Enterprise product-management attributes not present in WANDS. Provenance: Generated, except product_id (Real) and manufacturer where recoverable from product_features (Extracted).


| Column | Type | Description |
| --- | --- | --- |
| product_id | String (PK/FK) | References WANDS Product.product_id. |
| sku | String | Stock-keeping unit code. |
| brand_id | String (FK) | References Brand.brand_id. |
| category_id | String (FK) | References Category.category_id. |
| manufacturer | String | Manufacturer name. |
| product_status | String | Lifecycle status: Active, Discontinued, or Out of Stock. |
| launch_date | Date | Date the product was introduced to the catalog. |
| country_of_origin | String | Country where the product is manufactured. |
| warranty | String | Warranty terms and duration. |

## **3.2 Product Pricing**

Enables budget-constrained retrieval (e.g. “office chair under ₹15,000”), which WANDS cannot support on its own since it has no price field. Provenance: Generated — category-conditioned to realistic furniture/home-goods price bands, not random values.


| Column | Type | Description |
| --- | --- | --- |
| price_id | String (PK) | Unique identifier for a pricing record. |
| product_id | String (FK) | References WANDS Product.product_id. |
| currency | String | ISO currency code. |
| list_price | Decimal | Standard catalog price. |
| selling_price | Decimal | Current effective price after any discount. |
| discount_percentage | Decimal | Discount applied, if any. |
| effective_from | Date | Date this price record becomes active. |
| effective_to | Date | Date this price record expires; null for the current price. |

## **3.3 Product Attributes**

Normalized structured attributes (color, material, size, weight, capacity, dimensions). Provenance: Extracted from WANDS's existing product_features field where present; Generated only to backfill attributes missing from the source text, flagged per row.


| Column | Type | Description |
| --- | --- | --- |
| attribute_id | String (PK) | Unique identifier for the attribute record. |
| product_id | String (FK) | References WANDS Product.product_id. |
| attribute_name | String | Normalized attribute name, e.g. Color, Material, Size, Weight, Capacity, Dimensions. |
| attribute_value | String | Value for the attribute. |
| attribute_unit | String | Unit of measure where applicable (cm, kg, etc.). |

## **3.4 Product Review Summary (Generated)**

Adds richer semantic search text beyond the manufacturer description, mirroring the way real customer language (“great lumbar support,” “easy 20-minute assembly”) often differs from catalog copy. Provenance: Generated, with two safeguards: (1) generation has no visibility into query.csv or label.csv, preventing query vocabulary from leaking into product text and inflating benchmark scores; (2) generated sentiment is directed by the product's real average_rating and review_count so summaries stay consistent with the actual rating distribution rather than being arbitrary.


| Column | Type | Description |
| --- | --- | --- |
| review_summary_id | String (PK) | Unique identifier for the summary record. |
| product_id | String (FK) | References WANDS Product.product_id. |
| review_summary | String | Short generated synopsis of overall review content and sentiment. |
| positive_highlights | String | Generated summary of frequently mentioned positive points. |
| negative_highlights | String | Generated summary of frequently mentioned negative points. |
| sentiment_score | Decimal | Numeric sentiment score derived from generation. |

## **3.5 Brand**

Provenance: Extracted where a brand is recoverable from product_features; Generated placeholder otherwise.


| Column | Type | Description |
| --- | --- | --- |
| brand_id | String (PK) | Unique identifier for the brand. |
| brand_name | String | Brand display name. |
| brand_description | String | Short brand description. |
| brand_country | String | Country of brand origin. |

## **3.6 Category**

Provenance: Real — derived directly from WANDS's existing category_hierarchy field; not synthetic.


| Column | Type | Description |
| --- | --- | --- |
| category_id | String (PK) | Unique identifier for the category. |
| parent_category_id | String (FK) | Self-referencing link to the parent category; null for top-level categories. |
| category_name | String | Display name of the category. |
| category_description | String | Short description of the category. |

# **4. Final Schema Overview**

WANDS (core benchmark, unmodified):

Product — product_id, product_name, product_class, category_hierarchy, product_description, product_features, rating_count, average_rating, review_count

Query — query_id, query, query_class

Label — id, query_id, product_id, label

**Enterprise Extensions (joined on product_id):**

Product Master (PIM)

Product Pricing

Product Attributes

Product Review Summary

Brand

Category

This keeps WANDS unchanged while adding only the enterprise tables needed to support a production-oriented product search accelerator.

# **5. Data Provenance & Governance**

Two structural rules govern how the enterprise extension layer is used throughout the rest of this program, so that enrichment never compromises the integrity of the WANDS benchmark:

Evaluation Corpus vs. Showcase Catalog — All NDCG, MRR, and Recall@k scoring runs against the untouched WANDS Product / Query / Label tables only. Query understanding, price/attribute filtering, and any UI-facing demo run against the enriched Showcase Catalog (WANDS Product joined to the Enterprise Extensions). The two are never merged into a single scored pipeline.

Source tagging — Every enterprise-extension table (or row, for Product Attributes) carries a documented provenance value of Real, Extracted, or Generated, as specified in Section 3, so any field's origin can be traced at any point in the pipeline.

Together, these rules let the accelerator demonstrate production-realistic capabilities — budget filters, brand-aware queries, richer semantic text — while keeping the original, published WANDS benchmark fully intact and auditable.
