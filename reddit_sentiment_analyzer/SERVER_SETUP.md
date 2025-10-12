# 🚀 Hostinger Server Setup Guide

## 📋 Prerequisites
- Hostinger VPS/Cloud hosting account
- SSH access to your server
- Your API keys (Supabase, Apify, OpenAI)

## 🔧 Step 1: Connect to Server
```bash
ssh your_username@your_hostinger_ip
```

## 📁 Step 2: Setup Project Directory
```bash
# Create project directory
mkdir -p ~/reddit_sentiment_analyzer
cd ~/reddit_sentiment_analyzer

# Install Python dependencies
pip3 install --user python-dotenv supabase httpx openai
```

## 📝 Step 3: Create Environment File
```bash
nano .env
```

Add your API keys:
```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Apify Configuration
APIFY_API_KEY=your_apify_api_key_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

## 📤 Step 4: Upload Files
From your local machine, run:
```bash
# Make upload script executable
chmod +x upload_to_server.sh

# Edit the script with your server details
nano upload_to_server.sh

# Upload files
./upload_to_server.sh
```

## 🧪 Step 5: Test on Server
```bash
# Connect to server
ssh your_username@your_hostinger_ip

# Navigate to project
cd ~/reddit_sentiment_analyzer

# Test database connection
python3 check_table_exists.py

# Test simple write
python3 test_db_write_only.py

# Run full test
python3 test_process_one_url.py
```

## 🚀 Step 6: Run Production Scripts
```bash
# Process all URLs from database
python3 scrape_reddit_simple.py

# Check processing status
python3 check_processing_status.py

# Run analysis menu
python3 simple_analysis_menu.py
```

## 📊 Performance Benefits
- ✅ **Faster execution** (server-grade hardware)
- ✅ **No local resource usage**
- ✅ **Can run in background**
- ✅ **Better network connectivity**

## 🔧 Troubleshooting
- **Permission issues**: Use `pip3 install --user` for packages
- **Python version**: Ensure Python 3.8+ is installed
- **Network issues**: Check firewall settings
- **API limits**: Monitor usage on server

## 📈 Monitoring
```bash
# Check running processes
ps aux | grep python

# Monitor system resources
htop

# Check logs
tail -f /var/log/syslog
```
