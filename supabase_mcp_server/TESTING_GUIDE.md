# Testing Guide for Dynamic Supabase MCP Server

## 🧪 Testing Options

### 1. **Unit Tests** (Recommended First)
Test individual components without external dependencies.

### 2. **Demo Mode** (Safe Testing)
Test with simulated data and mocked responses.

### 3. **Integration Tests** (Real Database)
Test with actual Supabase connection.

### 4. **Live MCP Server** (Full Testing)
Test the complete MCP server with Claude.

---

## 🚀 Quick Start Testing

### Step 1: Install Dependencies
```bash
cd supabase_mcp_server
pip install -r requirements.txt
```

### Step 2: Run Unit Tests
```bash
# Test individual components
python -m pytest tests/ -v

# Test with coverage
python -m pytest tests/ --cov=src/supabase_mcp --cov-report=html
```

### Step 3: Run Demo
```bash
# Test with simulated data
python examples/dynamic_discovery_demo.py
```

---

## 🔧 Detailed Testing Methods

### Method 1: Unit Tests (No Database Required)

**What it tests:**
- Individual tool functions
- Error handling
- Data formatting
- Mock responses

**Run:**
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_mcp_tools.py -v

# Specific test function
pytest tests/test_mcp_tools.py::TestDynamicSupabaseMCPTools::test_query_table_tool -v
```

**Expected output:**
```
tests/test_mcp_tools.py::TestDynamicSupabaseMCPTools::test_query_table_tool PASSED
tests/test_supabase_client.py::TestSupabaseClient::test_query_table PASSED
...
```

### Method 2: Demo Mode (Simulated Data)

**What it tests:**
- Tool integration
- Response formatting
- Error scenarios
- User experience

**Run:**
```bash
python examples/dynamic_discovery_demo.py
```

**Expected output:**
```
🚀 Dynamic Supabase MCP Server Demo
==================================================

1️⃣ Discovering available tables...
# Available Tables in Your Supabase Database
...

2️⃣ Analyzing table schema...
# Schema for table: reddit_posts
...
```

### Method 3: Integration Tests (Real Database)

**Prerequisites:**
- Supabase project set up
- Environment variables configured

**Setup:**
```bash
# Copy and configure environment
cp env.example .env
# Edit .env with your Supabase credentials
```

**Run:**
```bash
# Test with real database
python examples/basic_usage.py
```

**Expected output:**
```
Querying users table...
Found 5 users
Inserting new user...
Created user: {'id': 123, 'email': 'test@example.com'}
```

### Method 4: Live MCP Server Testing

**Prerequisites:**
- Claude Desktop installed
- Supabase credentials configured

**Setup:**
1. Configure Claude Desktop:
```json
{
  "mcpServers": {
    "supabase-intelligence": {
      "command": "python",
      "args": ["/path/to/supabase_mcp_server/server.py"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-anon-key"
      }
    }
  }
}
```

2. Restart Claude Desktop

**Test in Claude:**
- "What tables do I have in my database?"
- "Show me the structure of the reddit_posts table"
- "Find posts about Knix with high scores"

---

## 🐛 Troubleshooting Tests

### Common Issues

**1. "Module not found" errors**
```bash
# Solution: Install in development mode
pip install -e .
```

**2. "No module named 'mcp'"**
```bash
# Solution: Install MCP dependencies
pip install mcp>=1.0.0
```

**3. "Supabase connection failed"**
```bash
# Solution: Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

**4. "Permission denied" in tests**
```bash
# Solution: Use anon key, not service role
# Or check RLS policies in Supabase
```

### Debug Mode

**Enable debug logging:**
```bash
export LOG_LEVEL=DEBUG
python examples/dynamic_discovery_demo.py
```

**Verbose test output:**
```bash
pytest tests/ -v -s --tb=short
```

---

## 📊 Test Coverage

### What's Tested

✅ **Unit Tests:**
- Tool registration and routing
- Parameter validation
- Error handling
- Response formatting
- Mock database operations

✅ **Integration Tests:**
- Real Supabase connections
- Actual database queries
- Data insertion/updates
- Cross-table searches

✅ **Demo Tests:**
- End-to-end workflows
- User experience
- Error scenarios
- Performance

### What's Not Tested

❌ **Live Claude Integration:**
- Requires Claude Desktop setup
- Manual testing only
- User interaction flows

❌ **Performance Under Load:**
- Large dataset queries
- Concurrent requests
- Memory usage

---

## 🎯 Test Scenarios

### Scenario 1: Fresh Database
**Test:** Empty database with no tables
**Expected:** Helpful guidance and suggestions

### Scenario 2: Single Table
**Test:** Database with one table
**Expected:** Proper schema analysis and querying

### Scenario 3: Multiple Tables
**Test:** Database with multiple related tables
**Expected:** Cross-table search and discovery

### Scenario 4: Permission Issues
**Test:** Database with RLS policies
**Expected:** Graceful error handling

### Scenario 5: Network Issues
**Test:** Intermittent connectivity
**Expected:** Retry logic and error messages

---

## 🚀 Quick Test Commands

```bash
# Quick smoke test
python -c "from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools; print('✅ Import successful')"

# Test configuration
python -c "from src.supabase_mcp.config import get_settings; print('✅ Config loaded')"

# Test Supabase client
python -c "from src.supabase_mcp.supabase_client import SupabaseClient; print('✅ Client created')"

# Run all tests
make test

# Run with coverage
make test-cov

# Format and lint
make format
make lint
```

---

## 📝 Test Results Interpretation

### ✅ Success Indicators
- All tests pass
- Demo runs without errors
- Clear, formatted output
- Helpful error messages

### ⚠️ Warning Signs
- Tests pass but demo fails
- Inconsistent results
- Poor error messages
- Performance issues

### ❌ Failure Indicators
- Import errors
- Connection failures
- Malformed responses
- Crashes or hangs

---

## 🔄 Continuous Testing

### Development Workflow
1. **Write code** → **Run unit tests** → **Fix issues**
2. **Run demo** → **Test integration** → **Verify output**
3. **Test with Claude** → **User acceptance** → **Deploy**

### Automated Testing
```bash
# Add to your CI/CD pipeline
pip install -r requirements.txt
pytest tests/ --cov=src/supabase_mcp
python examples/dynamic_discovery_demo.py
```

This testing approach ensures your MCP server works correctly at every level, from individual components to full user interactions with Claude.
