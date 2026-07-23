# Product Search Amazon Accelerator — Databricks Asset Bundle

Enterprise Databricks Accelerator for Amazon product catalog semantic search using Databricks Vector Search, Foundation Model Serving, and Medallion Architecture.

## Architecture

- **Bronze:** CSV ingestion (`Amazon.csv`) into `bronze.amazon_products_raw` with dynamic column resolution
- **Silver:** Dynamic column normalization, numeric field cleaning, search document synthesis, quality filtering, deduplication
- **Gold:** Feature engineering with price/rating tiers, change data feed enabled for Vector Search sync
- **Vector Search:** Synced Delta Vector Index with BGE-large-en embeddings on `shared_vs_endpoint`
- **Search:** Hybrid search (keyword + semantic) with query understanding, SQL fallback
- **Evaluation:** NDCG, Precision@k, Recall@k benchmarks logged to MLflow
- **Governance:** Unity Catalog enforcement, PII masking, audit logging, query validation

## Project Structure

```text
ProductSearch-Amazon-Bundle/
├── databricks.yml           # DAB bundle configuration
├── requirements.txt         # Python dependencies
├── config/                  # Pipeline, embedding, serving & evaluation YAML configs
│   ├── pipeline.yml         # Centralized pipeline configuration
│   ├── embedding.yml        # Embedding model configuration
│   ├── serving.yml          # Search serving configuration
│   ├── evaluation.yml       # Evaluation benchmark configuration
│   ├── dev.yml              # Dev environment overrides
│   ├── staging.yml          # Staging environment overrides
│   └── prod.yml             # Production environment overrides
├── notebooks/               # 00-12 Execution notebooks (numbered pipeline order)
│   ├── 00_validate_environment.py
│   ├── 00A_setup_and_validate.py
│   ├── 01_setup_platform.py
│   ├── 02_ingest_amazon_csv.py
│   ├── 03_bronze_to_silver.py
│   ├── 04_feature_engineering.py
│   ├── 05_generate_embeddings.py
│   ├── 06_vector_search_index.py
│   ├── 07_query_understanding.py
│   ├── 08_semantic_search_pipeline.py
│   ├── 09_search_evaluation.py
│   ├── 10_monitoring_healthcheck.py
│   ├── 11_governance_validation.py
│   └── 12_test_amazon_search.py
├── src/                     # Modular Python source code
│   ├── shared/              # Shared utilities (config, constants, logger, validation)
│   ├── ingestion/           # CSV reader with path resolution
│   ├── transformation/      # Dynamic schema resolution, deduplication, quality
│   ├── feature_engineering/ # Gold catalog feature builder
│   ├── search/              # Vector search, hybrid search, query understanding
│   ├── evaluation/          # NDCG, Precision@k, Recall@k metrics
│   ├── embeddings/          # Document preparation and embedding generation
│   ├── mlflow/              # Experiment tracking and metric logging
│   ├── monitoring/          # Pipeline event logging, alerts, health checks
│   ├── governance/          # Unity Catalog provisioning, PII masking, audit
│   └── utils/               # Spark, database, logging, validation helpers
├── resources/               # Job definitions, serving configs, dashboards
├── tests/                   # Unit tests for all pipeline modules
└── dataset/                 # Amazon CSV dataset
```

## Prerequisites

1. **Databricks Workspace** with Unity Catalog enabled
2. **Python 3.10+** on Databricks Runtime 15.4 LTS or later
3. **Databricks CLI v0.218+** installed and authenticated
4. **Vector Search Endpoint** (`shared_vs_endpoint` or custom) created in the workspace
5. **BGE-large-en Foundation Model** serving endpoint configured

## Quick Start

1. **Validate Bundle:**
   ```bash
   databricks bundle validate --target dev
   ```

2. **Deploy Bundle:**
   ```bash
   databricks bundle deploy --target dev
   ```

3. **Run Platform Setup (creates UC catalog & schemas):**
   ```bash
   databricks bundle run setup_platform_job --target dev
   ```

4. **Run Full Amazon Ingestion Pipeline:**
   ```bash
   databricks bundle run amazon_ingestion_job --target dev
   ```

5. **Run E2E Orchestration (all stages):**
   ```bash
   databricks bundle run e2e_orchestration_job --target dev
   ```

## Pipeline Stages

| Notebook | Stage | Description |
|----------|-------|-------------|
| `00_validate_environment` | Validation | Validates workspace setup, secret scopes, libraries |
| `01_setup_platform` | Provisioning | Creates UC catalog, bronze/silver/gold/operations schemas |
| `02_ingest_amazon_csv` | Bronze Ingestion | Reads Amazon.csv with dynamic column resolution into bronze table |
| `03_bronze_to_silver` | Silver Transformation | Column normalization, numeric cleaning, quality filtering, dedup |
| `04_feature_engineering` | Gold Features | Price tiers, rating buckets, search doc length, metadata |
| `05_generate_embeddings` | Embeddings | Validates search document readiness and embedding endpoint |
| `06_vector_search_index` | Vector Index | Creates/syncs Delta Vector Search index |
| `07_query_understanding` | Query Analysis | LLM-based query parsing and expansion |
| `08_semantic_search_pipeline` | Search | End-to-end semantic search pipeline execution |
| `09_search_evaluation` | Evaluation | Benchmark evaluation with MLflow logging |
| `10_monitoring_healthcheck` | Monitoring | Table health checks, data quality assessment |
| `11_governance_validation` | Governance | Query policy validation, secret scope audit |
| `12_test_amazon_search` | Testing | End-to-end search testing and verification |

## Configuration

All pipeline settings are in `config/pipeline.yml`. Environment-specific overrides are in `config/{env}.yml`.

Key configuration sections:
- **pipeline**: Medallion schema names, write mode, retry settings
- **ingestion**: CSV source path, table targets
- **mlflow**: Experiment tracking configuration
- **embedding**: Model name, endpoint, document field mappings
- **serving**: Vector search endpoint, hybrid search weights
- **evaluation**: Benchmark queries, metrics enabled
- **monitoring**: Alert thresholds for search latency, index sync
- **governance**: Secret scope, Unity Catalog enforcement

## Testing

```bash
# Run unit tests (requires pytest)
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_evaluation.py -v
```

## Monitoring & Observability

- Pipeline execution logs in `{catalog}.operations.pipeline_execution_log`
- Structured events in `{catalog}.operations.pipeline_events`
- Rejected records in `{catalog}.operations.rejected_records`
- Audit trail in `{catalog}.operations.audit_log`
- MLflow experiment at `/Shared/Amazon_Product_Search_ML`
- Search latency alerts configured via monitoring thresholds

## Governance

- Unity Catalog enforced for all data assets
- PII fields (user_id, user_name) masked with SHA-256 hashing
- Search query length and content policy validation
- Audit logging for all data access and pipeline operations
- Secret scope validation for credential management