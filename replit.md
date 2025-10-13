# Reddit Sentiment Analyzer

A Python CLI application that analyzes brand sentiment from Reddit discussions using AI-powered insights.

## Overview

This tool automates brand sentiment analysis by:
1. Selecting brands/prospects from a Supabase database
2. Searching Google for Reddit discussions about the brand
3. Scraping Reddit posts and comments using Apify
4. Processing and cleaning the data
5. Generating AI-powered sentiment analysis using OpenAI

## Project Structure

```
reddit_sentiment_analyzer/
├── main.py                 # Main workflow orchestrator
├── config/
│   └── settings.py        # Configuration management
├── database/
│   └── db.py             # Supabase database operations
├── modules/
│   ├── brand_selector.py # Brand/prospect management
│   ├── google_search.py  # Reddit URL discovery
│   ├── reddit_scraper.py # Reddit data extraction
│   ├── data_processor.py # Data cleaning and filtering
│   └── analysis.py       # ChatGPT analysis generation
├── utils/
│   └── logger.py         # Logging configuration
└── tests/                # Unit and integration tests
```

## Recent Changes

- **2025-10-13**: Initial Replit setup
  - Installed Python 3.11 and dependencies (including Streamlit)
  - Created web UI for step-by-step pipeline execution
  - Fixed Apify API integration (updated to use tilde format: `apify~actor-name`)
  - Fixed API token authentication (changed from Bearer header to query parameter)
  - Fixed database schema alignment (replaced `status` with `processed` boolean)
  - Added automatic URL processing tracking
  - Configured environment variables for all API keys
  - Updated .gitignore to exclude Python virtual environments

## Configuration

### Required Environment Variables

The following secrets must be configured in Replit Secrets:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase API key
- `APIFY_API_KEY` - Your Apify API token
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional Settings

Edit these in `.env` if needed:
- `MAX_REDDIT_URLS=10` - Maximum Reddit URLs to search per brand
- `MAX_POSTS_PER_URL=20` - Maximum posts per Reddit URL
- `MAX_COMMENTS_PER_POST=20` - Maximum comments per post

## How to Use

The application provides both a web UI and CLI interface:

### Web UI (Recommended)
1. Click the **Run** button or use the workflow panel
2. The Streamlit web interface will open showing a step-by-step pipeline:
   - **Step 1: Brand Selection** - Load prospects or create new ones
   - **Step 2: Search Reddit URLs** - Find Reddit discussions about the brand
   - **Step 3: Scrape Posts & Comments** - Extract data from Reddit
   - **Step 4: Process Data** - Clean and filter the data
   - **Step 5: Run Analysis** - Generate AI-powered sentiment insights
3. Run steps individually or skip steps as needed

### CLI Interface (Alternative)
Run the CLI version with:
```bash
cd reddit_sentiment_analyzer && python main.py
```

## Database Tables

The application uses these Supabase tables:
- `prospects` - Brand/prospect information
- `brand_google_reddit` - Reddit URLs found via Google search
- `brand_reddit_posts_comments` - Scraped Reddit data
- `reddit_brand_analysis_results` - AI analysis results

## Testing

Run tests with:
```bash
cd reddit_sentiment_analyzer
python -m pytest tests/
```

## Architecture Notes

- **Async/await**: All I/O operations use async for better performance
- **Rich CLI**: Beautiful terminal interface with progress tracking
- **Error handling**: Graceful error handling with detailed logging
- **Modular design**: Each module is independently testable
- **Rate limiting**: Built-in support for API rate limits

## Data Persistence

All data is automatically saved to Supabase as you progress through the pipeline:

- **Reddit URLs**: Saved to `brand_google_reddit` (with `processed` flag)
- **Posts & Comments**: Saved to `brand_reddit_posts_comments`
- **Analysis Results**: Saved to `reddit_brand_analysis_results`

You can work on multiple brands and all data will be preserved in the database.

## User Preferences

- Web UI for step-by-step control
- Data persists across sessions in Supabase
- Can process multiple brands without data loss
