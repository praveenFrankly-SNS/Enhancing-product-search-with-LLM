**CORE PIPELINE DOCUMENTATION**

**Offline Indexing Pipeline & Online Semantic Search Pipeline**

*Product Search with Large Language Models (LLMs) — Databricks Solution Accelerator Enhancement | SNS Square*


# **1. Purpose & Design Principle**

Production semantic search systems separate two pipelines with fundamentally different jobs, cost profiles, and execution frequencies. This document defines both for the Product Search accelerator: the pipeline that builds and maintains the search index, and the pipeline that serves a customer's search request against it.


| DESIGN PRINCIPLE Product embeddings are expensive to compute and change infrequently; query embeddings are cheap and must be computed instantly. Separating the two pipelines means a customer search only ever pays the cost of one embedding — the query — against an index that was already built offline, rather than re-embedding the catalog on every request. |
| --- |

# **2. Pipeline 1 — Product Indexing Pipeline (Offline)**

Builds and refreshes the searchable index. It does not run per customer search.

## **2.1 Trigger Conditions**


| Trigger | Description |
| --- | --- |
| Initial deployment | First build of the Gold catalog, embeddings, and Vector Search index. |
| Scheduled refresh | Periodic Databricks Workflows run to pick up catalog and pricing changes. |
| Product added / updated | Change Data Feed on the Bronze/Silver tables signals which products need re-processing. |

## **2.2 Stage-by-Stage Flow**

**▸  ****Enterprise Retail Database (Supabase PostgreSQL) — WANDS core + 6 enterprise extension tables**

**▸  ****Bronze — raw JDBC ingestion, metadata columns, Change Data Feed enabled**

**▸  ****Silver — dedup, rule-based cleaning, standardization, referential integrity**

**▸  ****Gold — feature engineering; searchable_text assembled from product text + attribute_summary + review_summary; metadata fields (price, brand, category, rating) kept separate**

**▸  ****Embedding Generation — searchable_text → product_embedding, via the baseline BGE-large-en-v1.5 model and, once available, the fine-tuned MiniLM candidate**

**▸  ****Databricks Vector Search Index — Delta-Sync hybrid index (dense + BM25), CDC-driven so it stays in sync with Gold**

## **2.3 Outputs**

Gold Product Catalog — curated, filterable metadata plus the canonical searchable_text field.

Product Embedding Table — one embedding per product, versioned by model in MLflow.

Databricks Vector Search Index — the artifact Pipeline 2 queries at runtime; this is the sole handoff point between the two pipelines.

# **3. Pipeline 2 — Semantic Search Pipeline (Online)**

Serves a customer's search request in real time. It runs on every search and never touches Bronze, Silver, or Gold directly — it only reads the Vector Search index that Pipeline 1 already built.

## **3.1 Trigger**

Every customer search request, initiated the moment a query is submitted.

## **3.2 Stage-by-Stage Flow**

**▸  ****Customer Query**

**▸  ****Query Understanding — LLM-based intent detection and attribute extraction (brand, price ceiling, category) via Foundation Model APIs**

**▸  ****Query Rewrite / Expansion — optional spell-correction and reformulation**

**▸  ****Query Embedding — a single embedding generated at request time, using the same model that produced the product embeddings**

**▸  ****Databricks Vector Search — hybrid dense + BM25 retrieval against the pre-built index**

**▸  ****Metadata Filtering — category, price, brand, in-stock, pushed down against the Gold metadata fields**

**▸  ****Reranking — cross-encoder or Vector Search Reranker re-scores the top-K candidates**

**▸  ****LLM Response Generation — optional, for a conversational or summarized result presentation**

**▸  ****Final Product Results**

## **3.3 Latency Expectation**

The design intent, consistent with how comparable hybrid retrieval + reranking + optional LLM-response pipelines typically behave, is sub-second to low-single-digit-second response time depending on which optional stages (query rewrite, reranking, LLM response) are enabled for a given request. This is a design expectation to validate with load testing once a baseline is running — not a committed SLA — consistent with this program's practice of not asserting numeric performance targets ahead of a measured baseline. p95 latency is tracked as a named success metric once real measurements exist.

# **4. Why the Two Pipelines Are Kept Separate**

The WANDS product catalog underlying this accelerator has 42,994 products. Re-embedding the full catalog on every customer search does not scale:


| Approach | Work Done Per Search | Outcome |
| --- | --- | --- |
| Naive (no separation) | Re-embed all 42,994 products, then compare against the query | Search latency scales with catalog size — minutes per query, and cost grows linearly with every request. |
| Two-pipeline (adopted) | Embed only the incoming query; compare against a pre-built index | Search latency is independent of catalog size; indexing cost is paid once per product change, not once per search. |

This is also why Pipeline 1 is scheduled/event-triggered while Pipeline 2 is always-on and request-triggered: the two have different latency budgets, different cost profiles, and different failure-recovery needs, and coupling them would force the cheaper, latency-critical path to inherit the slower, expensive one's constraints.

# **5. Combined Reference Architecture**

The Vector Search Index is the single handoff artifact between the two pipelines — Pipeline 1's last output is Pipeline 2's first read.

## **Offline — Product Indexing Pipeline**

**PostgreSQL → Bronze → Silver → Gold → Embedding Generation → Vector Search Index**


## **Online — Semantic Search Pipeline**

**Customer Query → Query Understanding → Query Embedding → Vector Search → Hybrid Search → Metadata Filtering → Reranking → LLM Response → Results**


This mirrors how enterprise search platforms — including Databricks' own AI Search — are typically organized: one pipeline prepares and maintains the index, and a separate, independent pipeline serves low-latency requests against it.
