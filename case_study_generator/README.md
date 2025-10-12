# Case Study Generator

A production-grade case study generation system that leverages AI to automate research, synthesis, and documentation.

## Architecture

```
case_study_generator/
├── src/
│   ├── core/                 # Core business logic
│   │   ├── research.py      # Research orchestration
│   │   ├── synthesis.py     # Theme synthesis
│   │   └── generation.py    # Case study generation
│   ├── services/            # External service integrations
│   │   ├── gemini.py        # Google Gemini integration
│   │   ├── openai.py        # OpenAI integration
│   │   └── notion.py        # Notion integration
│   ├── models/              # Data models and schemas
│   │   ├── case_study.py    # Case study data model
│   │   └── config.py        # Configuration models
│   └── utils/               # Utility functions
│       ├── formatting.py    # Text formatting utilities
│       └── validation.py    # Input validation
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── e2e/               # End-to-end tests
├── config/                 # Configuration files
│   ├── templates/         # Case study templates
│   └── prompts/          # AI prompts
├── scripts/               # Utility scripts
├── docs/                  # Documentation
└── examples/             # Example usage
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run tests:
```bash
pytest tests/
```

## Development

### Code Style
- Follow Google Python Style Guide
- Use type hints
- Write docstrings for all public functions
- Maintain 100% test coverage

### Testing
```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src tests/
```

### Documentation
- API documentation: `docs/api.md`
- Architecture: `docs/architecture.md`
- Contributing: `docs/contributing.md`

## Usage

```python
from src.core.research import ResearchOrchestrator
from src.core.synthesis import SynthesisOrchestrator
from src.core.generation import CaseStudyGenerator

# Initialize orchestrators
research = ResearchOrchestrator()
synthesis = SynthesisOrchestrator()
generator = CaseStudyGenerator()

# Generate case study
case_study = generator.generate(
    topic="Your Topic",
    research_orchestrator=research,
    synthesis_orchestrator=synthesis
)
```

## Production Deployment

1. Build Docker image:
```bash
docker build -t case-study-generator .
```

2. Run container:
```bash
docker run -p 8000:8000 case-study-generator
```

## Monitoring

- Prometheus metrics available at `/metrics`
- Health check endpoint at `/health`
- Logging configured with structured logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests
4. Submit a pull request

## License

Apache 2.0 