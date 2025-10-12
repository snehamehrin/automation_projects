# Architecture Overview

## System Architecture

The Reddit Sentiment Analyzer follows a microservices architecture with clear separation of concerns, designed for scalability, maintainability, and production deployment.

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Load Balancer │
│   (Optional)    │◄──►│   (FastAPI)     │◄──►│   (Nginx)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Core Analyzer  │
                       │   (Orchestrator)│
                       └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │   Google    │ │    Apify    │ │   OpenAI    │
        │   Sheets    │ │   Service   │ │   Service   │
        │   Service   │ │             │ │             │
        └─────────────┘ └─────────────┘ └─────────────┘
                │               │               │
                ▼               ▼               ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │ PostgreSQL  │ │   Redis     │ │   External  │
        │  Database   │ │   Cache     │ │    APIs     │
        └─────────────┘ └─────────────┘ └─────────────┘
```

## Core Components

### 1. API Layer (`src/api/`)
- **FastAPI Application**: RESTful API with automatic OpenAPI documentation
- **Middleware**: CORS, authentication, rate limiting, logging
- **Error Handling**: Centralized exception handling with structured responses
- **Health Checks**: Endpoint monitoring and service health reporting

### 2. Core Business Logic (`src/core/`)
- **RedditSentimentAnalyzer**: Main orchestrator that coordinates the entire workflow
- **Workflow Management**: Implements the N8N workflow logic in Python
- **Batch Processing**: Handles multiple brand analysis with concurrency control
- **Error Recovery**: Graceful handling of service failures and retries

### 3. Service Layer (`src/services/`)
- **GoogleSheetsService**: Handles Google Sheets API integration
- **ApifyService**: Manages web scraping through Apify's cloud infrastructure
- **OpenAIService**: Provides AI-powered sentiment analysis and report generation
- **Service Abstraction**: Clean interfaces for external service integration

### 4. Data Layer (`src/data/`)
- **Models**: Pydantic models for type safety and validation
- **Processors**: Data cleaning, filtering, and normalization pipeline
- **Database**: SQLAlchemy ORM with PostgreSQL for data persistence
- **Caching**: Redis for performance optimization

### 5. Configuration (`src/config/`)
- **Settings Management**: Hierarchical configuration with environment overrides
- **Validation**: Pydantic-based configuration validation
- **Security**: Secret management and environment-specific settings
- **Feature Flags**: Runtime configuration for feature toggles

## Data Flow

### Single Brand Analysis Flow

```
1. Brand Input → 2. Search Query Generation → 3. Google Search (Apify)
                                        ↓
8. HTML Report ← 7. AI Analysis (OpenAI) ← 6. Data Processing ← 5. Reddit Scraping (Apify)
                                        ↓
9. Result Storage → 10. Response
```

### Batch Analysis Flow

```
1. Brand List Input → 2. Concurrency Control → 3. Parallel Analysis
                                        ↓
4. Result Aggregation → 5. Error Handling → 6. Batch Response
```

## Technology Stack

### Backend
- **Python 3.11+**: Core programming language
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **AsyncIO**: Asynchronous programming support

### External Services
- **OpenAI GPT-4**: AI-powered sentiment analysis
- **Apify**: Web scraping infrastructure
- **Google Sheets API**: Data input/output management
- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage

### Infrastructure
- **Docker**: Containerization
- **Kubernetes**: Container orchestration
- **Nginx**: Reverse proxy and load balancing
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **ELK Stack**: Logging and monitoring

## Security Considerations

### Authentication & Authorization
- JWT-based authentication for API access
- Role-based access control (RBAC)
- API key management for external services
- Secure credential storage

### Data Protection
- Input validation and sanitization
- SQL injection prevention through ORM
- XSS protection in HTML reports
- Rate limiting to prevent abuse

### Infrastructure Security
- Container security scanning
- Network policies in Kubernetes
- TLS/SSL encryption for all communications
- Secrets management with Kubernetes secrets

## Scalability Design

### Horizontal Scaling
- Stateless service design
- Load balancer distribution
- Database connection pooling
- Redis clustering support

### Performance Optimization
- Async/await patterns throughout
- Connection pooling for external APIs
- Caching strategies for repeated requests
- Batch processing for multiple brands

### Monitoring & Observability
- Structured logging with correlation IDs
- Distributed tracing with OpenTelemetry
- Custom metrics for business logic
- Health checks and alerting

## Deployment Architecture

### Development Environment
```
Local Machine → Docker Compose → Services
```

### Production Environment
```
Internet → Load Balancer → Kubernetes Cluster → Services
```

### CI/CD Pipeline
```
Git Push → GitHub Actions → Build → Test → Deploy → Monitor
```

## Error Handling Strategy

### Service-Level Errors
- Graceful degradation when external services fail
- Retry mechanisms with exponential backoff
- Circuit breaker pattern for failing services
- Fallback responses for partial failures

### Application-Level Errors
- Structured error responses
- Comprehensive logging with context
- Error tracking and alerting
- User-friendly error messages

## Future Enhancements

### Planned Features
- Real-time WebSocket updates for long-running analyses
- Advanced caching with Redis Streams
- Machine learning model training pipeline
- Multi-language support for international brands
- Advanced analytics dashboard

### Scalability Improvements
- Event-driven architecture with message queues
- Microservices decomposition
- GraphQL API for flexible data querying
- Edge computing for global performance
