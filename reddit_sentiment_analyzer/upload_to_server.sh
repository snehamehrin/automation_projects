#!/bin/bash
# Upload files to Hostinger server

echo "📤 Uploading files to Hostinger server"
echo "======================================"

# Your Hostinger server details
SERVER_USER="root"
SERVER_HOST="31.97.103.35"
SERVER_PATH="~/workspace/projects/reddit_sentiment_analyzer"

# Files to upload
FILES=(
    "process_all_urls.py"
    "test_process_one_url.py"
    "scrape_reddit_simple.py"
    "save_google_results_to_supabase.py"
    "check_reddit_table.py"
    "check_table_exists.py"
    "debug_scraper_data.py"
    "test_db_write_only.py"
    "check_processing_status.py"
    "simple_analysis_menu.py"
    "reddit_analyzer.py"
    "test_single_reddit_scrape.py"
    "requirements.txt"
    ".env"
)

echo "📁 Uploading files to $SERVER_USER@$SERVER_HOST:$SERVER_PATH"

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "📤 Uploading $file..."
        scp "$file" "$SERVER_USER@$SERVER_HOST:$SERVER_PATH/"
    else
        echo "⚠️  File $file not found, skipping..."
    fi
done

echo "✅ Upload complete!"
echo ""
echo "🔗 Connect to server with:"
echo "ssh $SERVER_USER@$SERVER_HOST"
echo ""
echo "📁 Then navigate to:"
echo "cd ~/reddit_sentiment_analyzer"
