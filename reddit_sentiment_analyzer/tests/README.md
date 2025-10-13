# Test Suite for Brand Reddit Analysis Tool

This directory contains comprehensive tests for the Brand Reddit Analysis Tool.

## Test Structure

```
tests/
├── __init__.py                    # Test package initialization
├── conftest.py                    # Test configuration and fixtures
├── run_tests.py                   # Main test runner
├── test_individual_modules.py     # Individual module test scripts
├── requirements.txt               # Test dependencies
├── README.md                      # This file
├── unit/                          # Unit tests
│   ├── test_brand_selector.py     # Brand selector tests
│   ├── test_google_search.py      # Google search tests
│   ├── test_reddit_scraper.py     # Reddit scraper tests
│   ├── test_data_processor.py     # Data processor tests
│   ├── test_analysis.py           # Analysis module tests
│   └── test_database.py           # Database tests
└── integration/                   # Integration tests
    └── test_workflow.py           # End-to-end workflow tests
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
# From project root
python tests/run_tests.py

# Or using pytest directly
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
python tests/run_tests.py unit

# Integration tests only
python tests/run_tests.py integration

# Coverage report
python tests/run_tests.py coverage
```

### Run Individual Module Tests

```bash
# Test specific module
python tests/test_individual_modules.py brand_selector
python tests/test_individual_modules.py google_search
python tests/test_individual_modules.py reddit_scraper
python tests/test_individual_modules.py data_processor
python tests/test_individual_modules.py analysis
python tests/test_individual_modules.py database

# Test all modules
python tests/test_individual_modules.py
```

### Run Specific Test Files

```bash
# Test specific file
python tests/run_tests.py test_brand_selector

# Using pytest directly
pytest tests/unit/test_brand_selector.py -v
pytest tests/integration/test_workflow.py -v
```

## Test Types

### Unit Tests
- **Purpose**: Test individual modules in isolation
- **Location**: `tests/unit/`
- **Coverage**: Each module's functionality with mocked dependencies
- **Examples**: 
  - Brand selector prospect creation
  - Google search URL extraction
  - Reddit data transformation
  - Data filtering and cleaning
  - Analysis result parsing

### Integration Tests
- **Purpose**: Test complete workflows with multiple modules
- **Location**: `tests/integration/`
- **Coverage**: End-to-end scenarios with mocked external APIs
- **Examples**:
  - Complete brand analysis workflow
  - Error handling across modules
  - Data flow between components

### Individual Module Tests
- **Purpose**: Quick testing of individual modules with real-like scenarios
- **Location**: `tests/test_individual_modules.py`
- **Coverage**: Simplified tests for development and debugging
- **Examples**:
  - Module initialization
  - Basic functionality verification
  - Error condition testing

## Test Fixtures

The `conftest.py` file provides common test fixtures:

- `mock_prospect_data`: Sample prospect information
- `mock_reddit_urls`: Sample Reddit URLs
- `mock_reddit_data`: Sample Reddit posts/comments
- `mock_google_search_results`: Sample Google search results
- `mock_analysis_result`: Sample analysis output
- `mock_database`: Mocked database operations
- `mock_apify_response`: Mocked Apify API response
- `mock_openai_response`: Mocked OpenAI API response

## Mocking Strategy

Tests use comprehensive mocking to isolate units:

- **External APIs**: Apify, OpenAI, Supabase
- **User Input**: Rich prompts and confirmations
- **HTTP Requests**: httpx client responses
- **Database Operations**: Supabase client calls
- **File System**: Environment variables and settings

## Coverage

Run tests with coverage to see code coverage:

```bash
python tests/run_tests.py coverage
```

This generates:
- Terminal coverage report
- HTML coverage report in `htmlcov/index.html`

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- No external API calls (all mocked)
- No database connections (all mocked)
- Deterministic results
- Fast execution
- Clear pass/fail indicators

## Adding New Tests

### Unit Test
1. Create test file in `tests/unit/`
2. Follow naming convention: `test_<module_name>.py`
3. Use existing fixtures from `conftest.py`
4. Mock external dependencies
5. Test both success and error cases

### Integration Test
1. Add to `tests/integration/test_workflow.py`
2. Test complete user scenarios
3. Mock all external dependencies
4. Verify data flow between modules

### Individual Module Test
1. Add function to `tests/test_individual_modules.py`
2. Follow naming convention: `test_<module_name>()`
3. Use simple mocking for quick verification
4. Add to `run_all_module_tests()` if needed

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock all external dependencies
3. **Assertions**: Use specific assertions, not just `assert True`
4. **Error Testing**: Test both success and failure scenarios
5. **Async Testing**: Use `@pytest.mark.asyncio` for async functions
6. **Fixtures**: Reuse common test data via fixtures
7. **Naming**: Use descriptive test names
8. **Documentation**: Document complex test scenarios

