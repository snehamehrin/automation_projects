#!/bin/bash
# Deployment script for Hostinger server

echo "🚀 Deploying Reddit Sentiment Analyzer to Hostinger Server"
echo "============================================================"

# Create project directory
echo "📁 Creating project directory..."
mkdir -p ~/reddit_sentiment_analyzer
cd ~/reddit_sentiment_analyzer

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install --user python-dotenv supabase httpx openai

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

echo "✅ Deployment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your actual API keys"
echo "2. Upload your Python scripts to this directory"
echo "3. Run your scripts with: python3 script_name.py"
echo ""
echo "📁 Current directory: $(pwd)"
