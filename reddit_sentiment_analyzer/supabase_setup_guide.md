# Supabase Setup Guide

## Understanding Your Supabase Credentials

You have a **PostgreSQL connection URI**:
```
postgresql://postgres:[YOUR-PASSWORD]@db.wbpupfkbjmncmjmhyfha.supabase.co:5432/postgres
```

But for the Reddit Sentiment Analyzer, we need the **Supabase API credentials**, not the database connection string.

## How to Get Your Supabase API Credentials

### Step 1: Go to Your Supabase Dashboard
1. Visit [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Select your project (the one with `wbpupfkbjmncmjmhyfha` in the URL)

### Step 2: Get API Credentials
1. Go to **Project Settings** (gear icon in left sidebar)
2. Click on **API** tab
3. You'll see these values:

```
Project URL: https://wbpupfkbjmncmjmhyfha.supabase.co
anon public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role secret key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 3: Configure Your .env File

Your `.env` file should look like this:

```bash
# Supabase Configuration
SUPABASE_URL=https://wbpupfkbjmncmjmhyfha.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # anon public key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # service_role secret key
SUPABASE_BRANDS_TABLE=brands
SUPABASE_RESULTS_TABLE=analysis_results

# Other required settings
OPENAI_API_KEY=your_openai_api_key_here
APIFY_API_KEY=your_apify_api_key_here
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## Quick Setup Script

Run this to set up your environment:

```bash
cd reddit_sentiment_analyzer
python setup_env.py
```

When prompted:
- **Supabase Project URL**: `https://wbpupfkbjmncmjmhyfha.supabase.co`
- **Supabase Anon Key**: Copy the "anon public key" from your dashboard
- **Supabase Service Role Key**: Copy the "service_role secret key" from your dashboard

## Database Tables Setup

After configuring the credentials, you need to create the tables in Supabase:

1. Go to **SQL Editor** in your Supabase dashboard
2. Run this SQL:

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

## Test Your Setup

After setting up the credentials and tables:

```bash
python test_setup.py
```

This will test:
- ✅ Environment configuration
- ✅ Supabase connection
- ✅ Database operations
- ✅ Analyzer initialization

## Important Notes

- **Database URI vs API Credentials**: The PostgreSQL URI you have is for direct database access, but we use the Supabase client library which needs the API credentials
- **Security**: The `anon public key` is safe to use in frontend code, but the `service_role secret key` should only be used in backend/server code
- **Tables**: Make sure to create the tables in Supabase before running the tests
