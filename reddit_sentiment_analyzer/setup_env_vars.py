#!/usr/bin/env python3
"""
Setup environment variables for the Reddit Sentiment Analyzer.
"""

import os
from pathlib import Path


def create_env_file():
    """Create .env file with required variables."""
    env_path = Path(".env")
    
    if env_path.exists():
        print("📄 .env file already exists!")
        return
    
    print("🔧 Creating .env file...")
    
    env_content = """# Supabase Configuration
SUPABASE_URL=https://wbpupfkbjmncmjmhyfha.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here
SUPABASE_BRANDS_TABLE=prospects
SUPABASE_RESULTS_TABLE=analysis_results

# Apify Configuration
APIFY_TOKEN=your-apify-token-here

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Logging Configuration
LOG_LEVEL=INFO
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created!")
    print("\n📝 Please edit the .env file and add your actual API keys:")
    print("   1. APIFY_TOKEN - Get from https://console.apify.com/account/integrations")
    print("   2. OPENAI_API_KEY - Get from https://platform.openai.com/api-keys")
    print("   3. SUPABASE_KEY - Get from your Supabase project settings")


def check_env_vars():
    """Check if environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        "APIFY_TOKEN",
        "OPENAI_API_KEY", 
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your-{var.lower().replace('_', '-')}-here":
            print(f"   ✅ {var}: {value[:10]}...")
        else:
            print(f"   ❌ {var}: Not set or using placeholder")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing variables: {', '.join(missing_vars)}")
        print("   Please edit your .env file with actual values.")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True


if __name__ == "__main__":
    print("🚀 Environment Setup for Reddit Sentiment Analyzer")
    print("=" * 60)
    
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Check if variables are set
    check_env_vars()
    
    print("\n📋 Next steps:")
    print("   1. Edit the .env file with your actual API keys")
    print("   2. Run: python test_apify.py")
    print("   3. Run: python simple_analysis_menu.py")
