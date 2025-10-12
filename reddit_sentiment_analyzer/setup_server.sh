#!/bin/bash
# Setup script for Hostinger server (31.97.103.35)

echo "🚀 Setting up Reddit Sentiment Analyzer on Hostinger Server"
echo "============================================================"

# Navigate to workspace
cd ~/workspace/projects

# Create project directory
echo "📁 Creating project directory..."
mkdir -p reddit_sentiment_analyzer
cd reddit_sentiment_analyzer

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source ~/workspace/venv/bin/activate

# Install additional dependencies
echo "📦 Installing additional dependencies..."
pip install python-dotenv supabase httpx openai

# Create .env file template
echo "📝 Creating .env file template..."
cat > .env << 'EOF'
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Apify Configuration
APIFY_API_KEY=your_apify_api_key_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
EOF

echo "✅ Server setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your actual API keys: nano .env"
echo "2. Upload your Python scripts from local machine"
echo "3. Test with: python3 test_db_write_only.py"
echo ""
echo "📁 Current directory: $(pwd)"
echo "🐍 Virtual environment: $(which python)"
