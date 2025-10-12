# Reddit Sentiment Brand Analysis

A professional-grade brand sentiment analysis system that replicates and enhances the N8N workflow for comprehensive brand intelligence from Reddit discussions.

## 🏗️ Architecture

This system follows Google's engineering best practices with:
- **Microservices architecture** with clear separation of concerns
- **Comprehensive testing** with unit, integration, and E2E tests
- **Production-ready** logging, monitoring, and error handling
- **Scalable deployment** with Docker and Kubernetes support
- **Security-first** approach with proper secret management

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository>
cd reddit_sentiment_analyzer

# Install dependencies
make install

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Run tests
make test

# Start development server
make dev
```

## 📁 Project Structure

```
reddit_sentiment_analyzer/
├── src/                          # Source code
│   ├── core/                     # Core business logic
│   ├── services/                 # External service integrations
│   ├── data/                     # Data models and processing
│   ├── api/                      # API endpoints
│   └── utils/                    # Utility functions
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── config/                       # Configuration files
├── deployment/                   # Deployment configurations
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── monitoring/                   # Monitoring and observability
└── logs/                         # Application logs
```

## 🔧 Configuration

The system uses a hierarchical configuration approach:
- Environment variables for secrets
- YAML files for application settings
- Pydantic models for validation

## 🧪 Testing

Comprehensive test coverage with:
- Unit tests for individual components
- Integration tests for service interactions
- E2E tests for complete workflows
- Performance and load testing

## 📊 Monitoring

Built-in observability with:
- Structured logging with correlation IDs
- Metrics collection (Prometheus)
- Distributed tracing
- Health checks and alerts

## 🚀 Deployment

Production-ready deployment options:
- Docker containers
- Kubernetes manifests
- CI/CD pipelines
- Infrastructure as Code

## 📈 Performance

Optimized for scale:
- Async/await patterns
- Connection pooling
- Caching strategies
- Rate limiting and backoff

## 🔒 Security

Security-first design:
- Secret management
- Input validation
- Rate limiting
- Audit logging

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guide](docs/contributing.md)

## 🤝 Contributing

Please read our [Contributing Guide](docs/contributing.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.