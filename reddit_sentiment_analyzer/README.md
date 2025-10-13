# Brand Reddit Analysis Tool

A modular Python application that replicates the n8n workflow for brand sentiment analysis from Reddit data.

## Features

- **Brand Selection**: Find existing prospects or create new ones
- **Google Search**: Discover Reddit URLs using `reddit:brandname` search
- **Reddit Scraping**: Extract posts and comments using Apify
- **Data Processing**: Clean, filter, and deduplicate Reddit data
- **AI Analysis**: Generate comprehensive brand intelligence reports using ChatGPT
- **Rich CLI**: Beautiful terminal interface with progress tracking

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp env.example .env
# Edit .env with your actual API keys
```

## Usage

Run the complete workflow:
```bash
python main.py
```

The tool will ask you to:
1. Choose between analyzing a single brand or all prospects
2. Enter brand name (if single brand selected)
3. Confirm prospect details or create new prospect
4. Automatically process through the entire pipeline

## Module Structure

- `main.py` - Main workflow orchestrator
- `config/settings.py` - Configuration management
- `database/db.py` - Supabase database operations
- `modules/brand_selector.py` - Brand/prospect management
- `modules/google_search.py` - Reddit URL discovery
- `modules/reddit_scraper.py` - Reddit data extraction
- `modules/data_processor.py` - Data cleaning and filtering
- `modules/analysis.py` - ChatGPT analysis generation
- `utils/logger.py` - Logging configuration

## Testing Individual Modules

```python
# test_brand_selector.py
import asyncio
from modules.brand_selector import BrandSelector

async def test():
    selector = BrandSelector()
    prospect = await selector.get_or_create_prospect("Seed Health")
    print(prospect)

asyncio.run(test())
```

## Database Tables

The tool works with these Supabase tables:
- `prospects` - Brand/prospect information
- `brand_google_reddit` - Reddit URLs found via Google search
- `brand_reddit_posts_comments` - Scraped Reddit data
- `reddit_brand_analysis_results` - AI analysis results

## Configuration

Edit `.env` to configure:
- `MAX_REDDIT_URLS` - Maximum Reddit URLs to search (default: 10)
- `MAX_POSTS_PER_URL` - Maximum posts per Reddit URL (default: 20)
- `MAX_COMMENTS_PER_POST` - Maximum comments per post (default: 20)

