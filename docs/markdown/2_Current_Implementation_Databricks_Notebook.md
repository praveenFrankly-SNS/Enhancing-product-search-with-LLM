**CURRENT IMPLEMENTATION**

**Databricks Solution Accelerator: Product Search with LLMs**

*Source: databricks-industry-solutions/product-search (GitHub) & Databricks Solution Accelerator page*


# **1. Overview**

Databricks publishes a free, community-supported “Solution Accelerator” (not covered by an SLA) that demonstrates how to build semantic product search using large language models and embedding models on the Databricks Data Intelligence Platform. It uses the Wayfair Annotation Dataset (WANDS) — 42,000+ furniture/home-goods products, 480 real customer queries, and 233,000+ human-labeled query-product relevance pairs — as a ready-made, realistic benchmark for comparing search strategies.

The accelerator is delivered as a set of six sequentially-run Databricks notebooks (Python) in a single repository, intended to be cloned into a workspace via Databricks Repos and executed top-to-bottom on a GPU-enabled single-node cluster.

# **2. Reference Architecture**

WANDS Raw Data (CSV)
      ↓
Unity Catalog Delta Tables  (products / queries / labels)
      ↓
Databricks Vector Search Index  (BGE-large embeddings, Delta-Sync, CDC-driven)
      ↓
MLflow PyFunc Models  (Basic ANN | Hybrid | Hybrid+Reranker | Fine-Tuned)
      ↓
Model Serving REST Endpoints  (optional, CPU, scale-to-zero)

Enterprise-grade platform capabilities used throughout: Unity Catalog for governance and lineage over every table, volume, model, and index; Delta Lake with Change Data Feed so the vector index can incrementally sync as source data changes; MLflow for experiment tracking, model packaging, versioning, and the Unity Catalog Model Registry; and Databricks Vector Search as the managed vector database, avoiding any externally-hosted vector store.

# **3. Notebook-by-Notebook Breakdown**


| Notebook | Purpose | What It Does |
| --- | --- | --- |
| 00_Setup.py | Configuration & environment setup | Defines catalog/schema names, Unity Catalog Volume paths, endpoint/index names, and shared config dict consumed by every other notebook. |
| 01_Data_Prep.py | WANDS data ingestion & preparation | Downloads WANDS CSVs (products, queries, labels) from the Wayfair GitHub repo, writes them as Delta tables in Unity Catalog with Change Data Feed enabled, and derives numeric label_score values (Exact=1.0, Partial=0.75, Irrelevant=0.0) from text labels. |
| 02_Define_Basic_Search.py | Baseline semantic (ANN) vector search | Uses the pre-trained BAAI BGE-large-en-v1.5 embedding model (1024-dim) via a Databricks-hosted embedding endpoint; creates a Databricks Vector Search Delta-Sync index; wraps retrieval in an MLflow PyFunc model with retry logic; registers to Unity Catalog and optionally deploys to a Model Serving REST endpoint. |
| 03_Define_Hybrid_Search.py | Hybrid (vector + keyword/BM25) search | Reuses the same Vector Search index but issues queries with query_type='HYBRID', blending semantic similarity with BM25 keyword matching for a balance of conceptual and exact-term matching; packaged and registered the same way as basic search. |
| 04_Define_Hybrid_Search_and_Reranker.py | Hybrid search + cross-field reranking | Adds a columns_to_rerank parameter (product description) on top of hybrid search, invoking the Databricks Vector Search Reranker (private preview, requires workspace enrollment) as a second-stage relevance reordering step. |
| 05_Fine_Tune_Embedding_Model.py | Domain fine-tuned embedding model | Fine-tunes a smaller all-MiniLM-L12-v2 model (384-dim) on WANDS query-product-label triples using sentence-transformers' CosineSimilarityLoss for 1 epoch; benchmarks cosine-similarity and label correlation before/after tuning; builds a new self-managed Vector Search index from the tuned embeddings and registers a fine-tuned model. |


# **4. Search Strategies Demonstrated**

## **4.1 Basic (ANN) Semantic Search**

Product description (or name, if description is blank) is embedded with the pre-trained BAAI/bge-large-en-v1.5 model producing 1024-dimensional vectors. These are stored in a Databricks Vector Search Delta-Sync index. A user query is embedded on the fly and matched via approximate nearest-neighbor (ANN) similarity search. No fine-tuning is applied — this is an “off-the-shelf” baseline.

## **4.2 Hybrid Search (Vector + BM25)**

The same index is queried with query_type='HYBRID', which blends embedding-based semantic similarity with traditional BM25 keyword scoring in a single call — improving handling of exact product names, model numbers, and specific terms that pure embeddings can under-weight.

## **4.3 Hybrid Search + Reranker**

Adds a second-stage reranking pass (a private-preview Databricks Vector Search feature as of June 2025, requiring workspace enrollment) that reorders the hybrid result set using the product description text (columns_to_rerank) for finer-grained relevance scoring — at extra computational cost per query.

## **4.4 Fine-Tuned Embedding Model**

A smaller, faster all-MiniLM-L12-v2 model (384-dim) is fine-tuned directly on WANDS (query, product_text, label_score) triples using sentence-transformers with CosineSimilarityLoss for a single epoch (batch size 16, 100 warm-up steps). The notebook explicitly benchmarks average cosine similarity and correlation with human relevance labels before vs. after tuning to quantify the lift, then builds a new self-managed vector index from the tuned embeddings.

# **5. Deployment & MLOps Pattern**

Every search variant is wrapped in a custom mlflow.pyfunc.PythonModel (VectorSearchWrapper / FineTunedVectorSearchWrapper) exposing a standard predict(query) interface, with tenacity-based retry logic (3 attempts, exponential backoff) around the Vector Search calls.

Models are logged with mlflow.pyfunc.log_model(), registered to the Unity Catalog Model Registry, tagged with metadata (dataset, search type, source table, embedding endpoint), and given a rolling @newest alias.

Model Serving deployment (CPU, workload size Small, scale_to_zero_enabled) is explicitly marked optional in every notebook (“can take >20 minutes”) and is not required to complete the accelerator — it is a nice-to-have illustration of a REST endpoint, not a required production step.

Fine-tuned models are additionally persisted as raw files to a Unity Catalog Volume (SentenceTransformer.save()) alongside the MLflow registration, so the encoder can be reloaded independently for query-time embedding.

# **6. Recommended Compute**


| Cloud | Node Type | GPU | Runtime |
| --- | --- | --- | --- |
| AWS | g5.4xlarge | NVIDIA A10G | 16.4 LTS ML+ |
| Azure | Standard_NC6s_v3 | NVIDIA V100 | 16.4 LTS ML+ |
| GCP | n1-standard-4 | NVIDIA T4 | 16.4 LTS ML+ |


Configuration: single-node cluster, 0 workers. Cost of running the accelerator is explicitly the user's own responsibility.

# **7. Dataset Reference**

WANDS (Wayfair Annotation Dataset) — MIT license — 42,000+ products, 480 queries, 233,000+ relevance-labeled query-product pairs, sourced directly from the wayfair/WANDS GitHub repository.

sentence-transformers (Apache 2.0) — used for embedding generation and fine-tuning.

# **8. Known Limitations of the Current Implementation**

No formal SLA or production support — explicitly “AS-IS,” exploratory-only, with no Databricks support tickets accepted.

Manual, notebook-driven execution — no orchestrated pipeline (e.g. Databricks Workflows/Jobs), no CI/CD, no scheduled re-indexing or re-training.

Single, static dataset (WANDS / Wayfair furniture) — not connected to a live, changing production catalog or a real query log.

Reranker depends on a private-preview feature requiring manual workspace enrollment — not generally available.

Fine-tuning is a single-epoch, single-run demonstration — no hyperparameter search, no train/validation/test split discipline, no held-out offline evaluation harness (e.g. NDCG/MRR) beyond cosine-similarity correlation.

No query understanding layer — no query rewriting, spell correction, intent classification, or LLM-based query expansion.

No feedback loop — clickstream/conversion signals are not captured or fed back into ranking or retraining.

No monitoring, alerting, or drift detection on relevance quality, latency, or embedding/index freshness once (optionally) deployed.

Model Serving deployment is optional and CPU-only/Small in every notebook — not sized or load-tested for production traffic.

No A/B testing or experimentation framework to compare search strategies with real users.

Security/governance shown is baseline Unity Catalog + notebook auto-auth — no explicit discussion of service-principal-based production authentication, rate limiting, or multi-tenant isolation.
