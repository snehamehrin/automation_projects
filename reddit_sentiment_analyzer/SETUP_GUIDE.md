# Quick Setup Guide

This guide will help you set up the Reddit Sentiment Analyzer with Supabase in just a few steps.

## 1. Environment Setup

### Create .env file
```bash
cp env.example .env
```

### Edit .env file with your credentials:
```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
APIFY_API_KEY=your_apify_api_key_here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_BRANDS_TABLE=brands
SUPABASE_RESULTS_TABLE=analysis_results

# Optional settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## 2. Install Dependencies

```bash
# Install Python dependencies
pip install -e .

# Or install specific requirements
pip install supabase openai httpx pydantic fastapi uvicorn
```

## 3. Set up Supabase Database

### Create Tables in Supabase

Go to your Supabase dashboard → SQL Editor and run:

```sql
-- Create brands table
CREATE TABLE brands (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    company_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create analysis_results table
CREATE TABLE analysis_results (
    id BIGSERIAL PRIMARY KEY,
    brand_name TEXT NOT NULL,
    brand_category TEXT,
    company_url TEXT,
    analysis_timestamp TIMESTAMP WITH TIME ZONE,
    total_posts INTEGER,
    key_insight TEXT,
    sentiment_summary JSONB,
    thematic_breakdown JSONB,
    customer_segments JSONB,
    strategic_recommendations JSONB,
    html_report TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert some sample brands
INSERT INTO brands (name, category, company_url) VALUES
('Nike', 'Sportswear', 'https://www.nike.com'),
('Apple', 'Technology', 'https://www.apple.com'),
('Tesla', 'Automotive', 'https://www.tesla.com');
```

## 4. Test the Setup

### Run the setup test:
```bash
python test_setup.py
```

This will test:
- ✅ Environment configuration
- ✅ Supabase connection
- ✅ Single brand input
- ✅ Database operations
- ✅ Analyzer initialization

### Run the analysis test:
```bash
python test_analysis.py
```

Choose option 1 for single brand analysis or option 2 for database analysis.

## 5. Usage Examples

### Single Brand Analysis
```python
import asyncio
from src.core.analyzer import RedditSentimentAnalyzer
from src.data.models import BrandData

async def analyze_brand():
    analyzer = RedditSentimentAnalyzer()
    await analyzer.initialize()
    
    brand = BrandData(
        name="Nike",
        category="Sportswear",
        company_url="https://www.nike.com"
    )
    
    result = await analyzer.analyze_brand(brand)
    print(f"Key Insight: {result.key_insight}")
    
    await analyzer.close()

asyncio.run(analyze_brand())
```

### Database Analysis
```python
import asyncio
from src.core.analyzer import RedditSentimentAnalyzer

async def analyze_from_db():
    analyzer = RedditSentimentAnalyzer()
    await analyzer.initialize()
    
    results = await analyzer.analyze_from_supabase()
    print(f"Analyzed {len(results)} brands")
    
    await analyzer.close()

asyncio.run(analyze_from_db())
```

## 6. API Usage (Optional)

### Start the API server:
```bash
uvicorn src.api.main:app --reload
```

### Access the API:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Example API calls:
```bash
# Single brand analysis
curl -X POST "http://localhost:8000/analyze/single" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nike",
    "category": "Sportswear",
    "company_url": "https://www.nike.com"
  }'

# Database analysis
curl -X POST "http://localhost:8000/analyze/supabase"
```

## Troubleshooting

### Common Issues:

1. **Missing API Keys**
   - Make sure all required API keys are set in .env file
   - Check that the keys are valid and have proper permissions

2. **Supabase Connection Issues**
   - Verify your Supabase URL and key are correct
   - Make sure the tables exist in your Supabase database
   - Check that your Supabase project is active

3. **Import Errors**
   - Make sure you're running from the project root directory
   - Install all dependencies: `pip install -e .`

4. **Analysis Failures**
   - Check your OpenAI API key and quota
   - Verify your Apify API key and credits
   - Check the logs for detailed error messages

### Getting Help:
- Check the logs for detailed error messages
- Run `python test_setup.py` to diagnose issues
- Make sure all environment variables are set correctly

## Next Steps

Once everything is working:

1. **Add more brands** to your Supabase `brands` table
2. **Run batch analysis** to process multiple brands
3. **Set up a frontend** (like Replit) to use the API
4. **Deploy to production** when ready

The system is now ready for Replit integration! 🚀