# dhatu-api-gateway

🚪 **Passerelle API unifiée pour l'écosystème dhātu**

## 🎯 Objectif

Centraliser tous les accès API de l'écosystème dhātu avec authentification, rate limiting, monitoring, et documentation automatique. Point d'entrée unique pour tous les clients.

## ✨ Fonctionnalités Core

- **Gateway unifié**: Single point of entry
- **Service discovery**: Auto-detection services dhātu
- **Load balancing**: Distribution intelligente charge
- **Circuit breaker**: Protection surcharge services
- **API versioning**: Gestion versions multiples
- **Documentation**: OpenAPI/Swagger auto-générée

## 🏗️ Architecture Microservices

```yaml
dhatu-api-gateway/
├── gateway/
│   ├── core/
│   │   ├── router.py            # Routage intelligent
│   │   ├── middleware.py        # Middleware stack
│   │   └── discovery.py         # Service discovery
│   ├── auth/
│   │   ├── jwt_handler.py       # JWT validation
│   │   ├── rbac.py              # Role-based access
│   │   └── api_keys.py          # API key management
│   ├── rate_limiting/
│   │   ├── algorithms.py        # Token bucket, sliding window
│   │   └── storage.py           # Redis-based storage
│   └── monitoring/
│       ├── metrics.py           # Prometheus metrics
│       ├── tracing.py           # Distributed tracing
│       └── health_checks.py     # Health monitoring
├── services/
│   ├── compression/             # Proxy compression API
│   ├── corpus/                  # Proxy corpus API
│   ├── analysis/                # Proxy analysis API
│   └── dashboard/               # Proxy dashboard API
├── docs/
│   ├── openapi/                 # OpenAPI specifications
│   └── examples/                # Usage examples
└── deployment/
    ├── docker/                  # Container configs
    └── k8s/                     # Kubernetes manifests
```

## 🚀 Stack Technologique

### Core Framework
- **FastAPI**: Async/await native, auto-documentation
- **Pydantic**: Validation données robuste
- **asyncio**: Concurrence haute performance
- **httpx**: Client HTTP async

### Infrastructure
- **Redis**: Cache + rate limiting + sessions
- **Consul**: Service discovery + configuration
- **Prometheus**: Métriques + monitoring
- **Jaeger**: Distributed tracing

## 🔐 Sécurité Intégrée

### Authentication
- **JWT**: Tokens stateless avec refresh
- **API Keys**: Accès service-to-service
- **OAuth2**: Intégration providers externes
- **mTLS**: Mutual TLS pour microservices

### Authorization
- **RBAC**: Rôles granulaires
- **Scopes**: Permissions API spécifiques
- **Rate limiting**: Protection DDoS
- **Input validation**: Sanitization automatique

## 📊 Monitoring & Observabilité

### Métriques
- **Request metrics**: Latence, throughput, erreurs
- **Service health**: Statut services backend
- **Resource usage**: CPU, mémoire, connexions
- **Business metrics**: Usage API par endpoint

### Tracing
- **Request tracing**: Suivi requêtes cross-service
- **Performance profiling**: Identification bottlenecks
- **Error tracking**: Agrégation erreurs
- **Dependency mapping**: Topologie services

## 🔄 API Endpoints Structure

### Core APIs
```yaml
# Compression Service
/api/v1/compress
/api/v1/decompress
/api/v1/analyze

# Corpus Service  
/api/v1/corpus/collect
/api/v1/corpus/search
/api/v1/corpus/stats

# Analysis Service
/api/v1/patterns/detect
/api/v1/patterns/visualize
/api/v1/insights/generate

# System APIs
/api/v1/health
/api/v1/metrics
/api/v1/status
```

## 🚀 Roadmap v1.0

### Phase 1: Core Gateway (2 semaines)
- [ ] FastAPI setup + middleware stack
- [ ] Service proxy basique
- [ ] Authentication JWT
- [ ] Rate limiting Redis

### Phase 2: Advanced Features (2 semaines)
- [ ] Service discovery dynamique
- [ ] Load balancing algorithmique
- [ ] Circuit breaker pattern
- [ ] Health checks automatiques

### Phase 3: Observabilité (1 semaine)
- [ ] Prometheus metrics
- [ ] Jaeger tracing
- [ ] Dashboard monitoring
- [ ] Alerting rules

### Phase 4: Documentation (1 semaine)
- [ ] OpenAPI auto-generation
- [ ] Interactive docs Swagger
- [ ] Usage examples
- [ ] SDK client libraries

## 🔧 Configuration

### Environment Variables
```bash
# Gateway Config
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000
GATEWAY_WORKERS=4

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=secure_password

# Services
COMPRESSION_SERVICE_URL=http://compression:8001
CORPUS_SERVICE_URL=http://corpus:8002
ANALYSIS_SERVICE_URL=http://analysis:8003

# Security
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Monitoring
PROMETHEUS_ENABLED=true
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
```

## 📱 Client SDKs

### Python SDK
```python
from dhatu_client import DhatuAPI

client = DhatuAPI(
    base_url="https://api.dhatu.dev",
    api_key="your_api_key"
)

# Compression
result = await client.compress("text to compress")

# Corpus search
documents = await client.corpus.search("sanskrit linguistics")

# Pattern analysis
patterns = await client.analysis.detect_patterns(data)
```

### JavaScript SDK
```javascript
import { DhatuAPI } from '@dhatu/client';

const client = new DhatuAPI({
  baseURL: 'https://api.dhatu.dev',
  apiKey: 'your_api_key'
});

// Async/await support
const result = await client.compress('text to compress');
```

## 🔄 Load Balancing Strategies

- **Round Robin**: Distribution équitable
- **Weighted**: Selon capacité services
- **Least Connections**: Vers service moins chargé
- **Health-based**: Éviter services défaillants

## 📈 Scalabilité

- **Horizontal scaling**: Multiple gateway instances
- **Auto-scaling**: Kubernetes HPA
- **Connection pooling**: Réutilisation connexions
- **Async processing**: Non-blocking I/O

## 🛡️ Resilience Patterns

- **Circuit Breaker**: Protection cascade failures
- **Retry Logic**: Exponential backoff
- **Timeout Management**: Éviter hang requests
- **Graceful Degradation**: Fallback responses