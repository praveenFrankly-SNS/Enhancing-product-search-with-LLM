# Enterprise Search Application Architecture

## Overview

This document describes the architecture of the Enterprise Search Application that consumes the AI Platform built in ProductSearch-Bundle.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Customer Browser                          │
│                    (React + TypeScript UI)                        │
└────────────────────────────┬──────────────────────────────────────┘
                             │ HTTPS / JWT
┌────────────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend Gateway                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Authentication & Authorization                          │   │
│  │ • Request Validation & Rate Limiting                      │   │
│  │ • Response Formatting & Error Handling                    │   │
│  │ • Logging & Monitoring                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬──────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼──────────┐ ┌─────▼──────┐  ┌────────▼──────────┐
│  Search Service   │ │   Cache    │  │  Health Service   │
│                   │ │  Service   │  │                   │
│ • Query           │ │            │  │ • System Health   │
│   Normalization   │ │ • Redis    │  │ • Metrics         │
│ • Vector Search   │ │ • TTL      │  │ • Analytics       │
│ • Result Merge    │ │ • Hit Rate │  │                   │
└────────┬──────────┘ └────────────┘  └───────────────────┘
         │
         │
┌────────▼──────────────────────────────────────────────────────────┐
│                    Databricks Service Layer                        │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ │
│  │ Vector Search    │ │  SQL Warehouse   │ │  Model Serving   │ │
│  │                  │ │                  │ │                  │ │
│  │ • Embeddings     │ │ • Product Data   │ │ • Inference      │ │
│  │ • Similarity     │ │ • Metadata       │ │                  │ │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘ │
└─────────────────────────────┬──────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                      Unity Catalog Layer                            │
│  • Data Governance  • Access Control  • Lineage Tracking           │
└─────────────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Layer 1: Frontend UI (React + TypeScript)

**Responsibilities:**
- Search interface and user interactions
- Product display and pagination
- Filter controls and sorting
- Loading states and animations
- Error handling and empty states
- Responsive design (mobile, tablet, desktop)

**Key Components:**
- `SearchBar` - Smart search with autocomplete
- `ProductCard` - Product display with similarity score
- `HomePage` - Landing page with popular searches
- `SearchPage` - Results page with pagination
- `Filters` - Category, price, brand filters

**Technologies:**
- React 18 with TypeScript
- React Router for navigation
- TanStack Query for data fetching
- Zustand for state management
- Tailwind CSS for styling
- Phosphor Icons for UI elements

### Layer 2: API Gateway (FastAPI)

**Responsibilities:**
- Request authentication and authorization
- Input validation and sanitization
- Rate limiting (100 requests/minute)
- Response formatting
- Error handling and logging
- CORS configuration
- Request/response compression

**Key Features:**
- JWT-based authentication
- Role-based access control
- Query length limits (200 chars max)
- Automatic API documentation (OpenAPI/Swagger)
- Structured logging with metadata
- Request timing middleware

**Endpoints:**
```
POST   /api/v1/search/              - Semantic product search
GET    /api/v1/search/              - Search with URL params
GET    /api/v1/search/suggestions   - Query autocomplete
GET    /api/v1/products/{id}        - Product details
GET    /api/v1/health/              - Basic health check
GET    /api/v1/health/detailed      - Service health status
GET    /api/v1/health/stats         - Analytics and metrics
```

### Layer 3: Search Service

**Responsibilities:**
- Query normalization and optimization
- Cache management
- Vector search orchestration
- Parallel data fetching
- Result enrichment
- Performance tracking

**Search Flow:**
```
User Query
    ↓
Validate & Sanitize (< 200 chars, no injection)
    ↓
Normalize (lowercase, trim, remove punctuation)
    ↓
Check Cache (Redis, 1 hour TTL)
    ↓
[Cache Hit] → Return Immediately (< 100ms)
    ↓
[Cache Miss] → Query Vector Search
    ↓
Parallel Execution:
  ├─ Fetch Product Details (SQL Warehouse)
  ├─ Fetch Metadata (ratings, reviews)
  └─ Log Analytics (query tracking)
    ↓
Merge & Enrich Results
    ↓
Update Cache
    ↓
Return Response (< 2-3 seconds target)
```

**Optimizations:**
1. **Query Normalization** - Reduces cache misses
2. **Multi-level Caching** - In-memory + Redis
3. **Parallel Execution** - Concurrent backend calls
4. **Pagination** - Progressive loading (20 results/page)
5. **Field Selection** - Fetch only required data
6. **Connection Pooling** - Reuse Databricks connections

### Layer 4: Cache Service (Redis)

**Responsibilities:**
- Search result caching
- Product detail caching
- Query suggestion caching
- Cache invalidation
- Hit rate tracking

**Cache Strategy:**
- **Search Results:** 1 hour TTL
- **Product Details:** 6 hours TTL
- **Suggestions:** 30 minutes TTL
- **LRU Eviction:** When memory limit reached

**Key Metrics:**
- Hit rate target: > 70%
- Memory usage monitoring
- Total keys tracking
- Eviction rate

### Layer 5: Databricks Integration

**Components:**

1. **Vector Search Service**
   - Embedding generation
   - Similarity search
   - Top-K retrieval
   - Metadata filtering

2. **SQL Warehouse**
   - Product master data
   - Pricing information
   - Product attributes
   - Review summaries

3. **Unity Catalog**
   - Data governance
   - Access control
   - Lineage tracking
   - Audit logging

## Performance Goals

| Metric | Target | Current |
|--------|--------|---------|
| Search Latency (cache hit) | < 100ms | ~80ms |
| Search Latency (cache miss) | < 2-3s | ~1.5s |
| Concurrent Users | 100+ | Tested: 50 |
| Cache Hit Rate | > 70% | ~75% |
| API Response Time | < 500ms | ~300ms |
| Uptime | > 99.5% | - |

## Security Architecture

### Authentication Flow
```
Client Request
    ↓
Extract JWT Token (from Authorization header)
    ↓
Verify Token Signature (secret key)
    ↓
Check Token Expiration (30 min default)
    ↓
Extract User Claims (user_id, role, permissions)
    ↓
Validate Permissions (role-based access)
    ↓
Allow Request
```

### Security Features
1. **JWT Authentication** - Token-based auth
2. **Input Validation** - Query sanitization
3. **Rate Limiting** - Prevent abuse (100/min)
4. **Request Size Limits** - Max payload size
5. **CORS Configuration** - Controlled origins
6. **HTTPS Only** - Encrypted communication
7. **SQL Injection Prevention** - Parameterized queries

### Query Sanitization
```python
# Remove dangerous characters
query = re.sub(r'[^\w\s\-]', '', query)

# Limit length
query = query[:200]

# Remove control characters
query = ''.join(c for c in query if c.isprintable())

# Normalize whitespace
query = ' '.join(query.split())
```

## Monitoring & Observability

### Application Metrics
- **Search Latency** - P50, P95, P99
- **Cache Hit Rate** - Percentage cached
- **API Latency** - Request processing time
- **Error Rate** - Failed requests per minute
- **Active Users** - Concurrent sessions
- **Request Rate** - Requests per second

### System Health Checks
```
Vector Search:      ✓ Healthy / ✗ Unhealthy
SQL Warehouse:      ✓ Running / ⚠ Starting / ✗ Stopped
Unity Catalog:      ✓ Accessible / ✗ Unreachable
Cache (Redis):      ✓ Connected / ✗ Disconnected
API Gateway:        ✓ Healthy
```

### Logging Structure
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "search_service",
  "event": "search_completed",
  "query": "gaming laptop",
  "results_count": 18,
  "processing_time_ms": 742,
  "cached": false,
  "user_id": "user_123"
}
```

## Data Flow Example

### Semantic Search Request

**1. Client Request:**
```http
POST /api/v1/search/
Content-Type: application/json

{
  "query": "lightweight laptop for students",
  "page": 1,
  "page_size": 20
}
```

**2. API Gateway:**
- Validates JWT token
- Checks rate limit (99/100 used)
- Sanitizes query
- Logs request

**3. Search Service:**
- Normalizes: "lightweight laptop for students"
- Checks cache: MISS
- Calls Vector Search with normalized query

**4. Databricks:**
- Generates embedding for query
- Performs similarity search
- Returns top 100 products with scores

**5. Search Service:**
- Filters by similarity > 0.5
- Paginates to page 1 (20 results)
- Fetches product details in parallel
- Enriches with pricing, ratings
- Updates cache
- Returns response

**6. Client Response:**
```json
{
  "query": "lightweight laptop for students",
  "total_results": 18,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "results": [...],
  "metadata": {
    "vector_search_time_ms": 520,
    "product_fetch_time_ms": 180,
    "processing_time_ms": 742,
    "cached": false
  }
}
```

## Scalability Considerations

### Horizontal Scaling
- **API Gateway:** Stateless, can run multiple instances
- **Search Service:** Stateless, horizontally scalable
- **Cache:** Redis cluster for distributed caching
- **Load Balancer:** Distribute requests across instances

### Vertical Scaling
- **Databricks:** Scale compute clusters
- **SQL Warehouse:** Increase warehouse size
- **Redis:** Increase memory allocation

### Optimization Strategies
1. **Connection Pooling** - Reuse database connections
2. **Lazy Loading** - Load images progressively
3. **Response Compression** - GZip responses
4. **CDN Integration** - Cache static assets
5. **Query Batching** - Batch similar queries

## Deployment Architecture

```
                    ┌─────────────┐
                    │   Route 53  │ (DNS)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │     ALB     │ (Load Balancer)
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       ┌──────▼──────┐          ┌──────▼──────┐
       │  ECS Task 1 │          │  ECS Task 2 │
       │             │          │             │
       │ • FastAPI   │          │ • FastAPI   │
       │ • Container │          │ • Container │
       └──────┬──────┘          └──────┬──────┘
              │                         │
              └────────────┬────────────┘
                           │
              ┌────────────▼─────────────┐
              │                          │
       ┌──────▼──────┐          ┌────────▼────────┐
       │   Redis     │          │   Databricks    │
       │  ElastiCache│          │    Workspace    │
       └─────────────┘          └─────────────────┘
```

## Future Enhancements

1. **Advanced Filtering**
   - Price range slider
   - Multi-select categories
   - Rating filter
   - Availability filter

2. **Personalization**
   - User preferences
   - Search history
   - Recommended products

3. **Analytics Dashboard**
   - Real-time metrics
   - Search trends
   - Performance monitoring
   - User behavior tracking

4. **A/B Testing**
   - Search algorithm variants
   - UI/UX experiments
   - Conversion optimization

5. **Mobile App**
   - React Native implementation
   - Offline support
   - Push notifications

## References

- [API Documentation](./API_DOCUMENTATION.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Performance Optimization](./PERFORMANCE_OPTIMIZATION.md)
- [Security Guide](./SECURITY.md)
