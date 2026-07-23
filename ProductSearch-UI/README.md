# Enterprise Search Application Architecture

## Overview
This is the Enterprise Search Application that consumes the AI Platform built in ProductSearch-Bundle. It demonstrates enterprise-grade patterns for semantic search, including API design, caching, performance optimization, and security.

## Architecture

```
Customer Browser
       │
       ▼
React + TypeScript UI
       │
    HTTPS / JWT
       │
       ▼
FastAPI Backend Gateway
       │
┌──────┴──────────────┐
▼                     ▼
Search Service    Cache Service
       │                │
       └────────┬───────┘
                ▼
    Databricks Service Layer
                │
    ┌───────────┼────────────┐
    ▼           ▼            ▼
Vector Search  SQL WH   Model Serving
    │
    ▼
Unity Catalog Layer
```

## Performance Goals
- **Target Search Latency**: < 2-3 seconds for typical queries
- **Concurrent Users**: Support multiple simultaneous searches
- **Cache Hit Rate**: > 70% for popular queries
- **API Response Time**: < 500ms (excluding Vector Search)

## Components

### 1. Frontend (React + TypeScript)
- Modern, responsive UI
- Customer Portal: Search, Results, Product Details
- Admin Portal: Monitoring, Analytics, System Health

### 2. Backend API (FastAPI)
- API Gateway with authentication & rate limiting
- Search Service with query normalization
- Cache Service with multi-level caching
- Databricks integration layer
- Health & monitoring endpoints

### 3. Key Features
- **Semantic Search**: Powered by Databricks Vector Search
- **Query Optimization**: Normalization, caching, parallel execution
- **Security**: JWT authentication, input validation, rate limiting
- **Monitoring**: Request tracking, latency metrics, error rates
- **Pagination**: Efficient result streaming
- **Lazy Loading**: Optimized resource loading

## Directory Structure

```
ProductSearch-UI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── search.py
│   │   │   │   ├── products.py
│   │   │   │   ├── health.py
│   │   │   │   └── analytics.py
│   │   │   └── middleware/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── services/
│   │   │   ├── search_service.py
│   │   │   ├── cache_service.py
│   │   │   ├── databricks_service.py
│   │   │   └── product_service.py
│   │   ├── models/
│   │   └── utils/
│   ├── tests/
│   ├── requirements.txt
│   └── main.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── customer/
│   │   │   │   ├── SearchBar.tsx
│   │   │   │   ├── SearchResults.tsx
│   │   │   │   ├── ProductCard.tsx
│   │   │   │   ├── ProductDetails.tsx
│   │   │   │   ├── Filters.tsx
│   │   │   │   └── Pagination.tsx
│   │   │   ├── admin/
│   │   │   │   ├── MonitoringDashboard.tsx
│   │   │   │   ├── AnalyticsDashboard.tsx
│   │   │   │   └── SystemHealth.tsx
│   │   │   └── common/
│   │   │       ├── Loading.tsx
│   │   │       ├── ErrorMessage.tsx
│   │   │       └── EmptyState.tsx
│   │   ├── pages/
│   │   │   ├── customer/
│   │   │   │   ├── HomePage.tsx
│   │   │   │   ├── SearchPage.tsx
│   │   │   │   └── ProductPage.tsx
│   │   │   └── admin/
│   │   │       └── DashboardPage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── hooks/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
│
├── docs/
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT.md
│   ├── PERFORMANCE_OPTIMIZATION.md
│   └── SECURITY.md
│
└── docker/
    ├── backend.Dockerfile
    └── frontend.Dockerfile
```

## Search Flow

```
User Query
    ↓
Validate Input
    ↓
Normalize Query (lowercase, trim, etc.)
    ↓
Check Cache
    ↓
[Cache Hit] → Return Cached Results
    ↓
[Cache Miss] → Vector Search
    ↓
Parallel Execution:
  - Fetch Product Details
  - Fetch Metadata
  - Log Analytics
    ↓
Format Response
    ↓
Update Cache
    ↓
Return to User
```

## API Response Format

```json
{
  "query": "office chair",
  "processing_time_ms": 742,
  "total_results": 18,
  "page": 1,
  "page_size": 20,
  "results": [
    {
      "product_id": "prod_001",
      "product_name": "Ergonomic Office Chair",
      "description": "...",
      "price": 299.99,
      "similarity_score": 0.94,
      "image_url": "...",
      "category": "Furniture"
    }
  ],
  "metadata": {
    "cached": false,
    "vector_search_time_ms": 520,
    "product_fetch_time_ms": 180
  }
}
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Databricks workspace with Vector Search enabled
- Access to ProductSearch-Bundle platform

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Configure your Databricks credentials in .env
python -m uvicorn main:app --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (.env)
```
DATABRICKS_HOST=your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token
VECTOR_SEARCH_ENDPOINT=your-endpoint
SQL_WAREHOUSE_ID=your-warehouse-id
CACHE_TTL=3600
RATE_LIMIT_PER_MINUTE=100
JWT_SECRET=your-secret
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

## Monitoring Metrics

The application tracks:
- **Search Latency**: Time from query to response
- **Cache Hit Rate**: Percentage of cached responses
- **API Latency**: Backend processing time
- **Error Rate**: Failed requests per minute
- **Active Users**: Concurrent search sessions
- **Top Queries**: Most searched terms

## Security Features

1. **Authentication**: JWT-based authentication
2. **Authorization**: Role-based access control
3. **Input Validation**: Query sanitization and length limits
4. **Rate Limiting**: Prevent abuse
5. **Request Size Limits**: Protect against large payloads
6. **CORS Configuration**: Controlled cross-origin access
7. **HTTPS Only**: Encrypted communication

## Performance Optimizations

1. **Query Normalization**: Reduce duplicate cache entries
2. **Multi-level Caching**: In-memory and distributed cache
3. **Parallel Execution**: Concurrent backend operations
4. **Lazy Loading**: Progressive image loading
5. **Pagination**: Efficient result streaming
6. **Field Selection**: Retrieve only required data
7. **Connection Pooling**: Reuse Databricks connections

## Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test
```

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment instructions.

## License

Part of the Databricks Product Search Solution Accelerator
