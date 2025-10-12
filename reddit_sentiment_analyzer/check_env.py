#!/usr/bin/env python3
"""
Check if .env file exists and what's in it
"""

import os
from pathlib import Path


def check_env_file():
    """Check .env file status."""
    print("🔍 Checking .env file...")
    
    env_path = Path(".env")
    
    if env_path.exists():
        print("✅ .env file exists!")
        
        # Read and display contents (masking sensitive values)
        with open(env_path, 'r') as f:
            content = f.read()
        
        print("\n📄 .env file contents:")
        print("-" * 30)
        
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if 'token' in key.lower() or 'key' in key.lower():
                        # Mask sensitive values
                        if value and len(value) > 10:
                            masked_value = value[:10] + "..." + value[-4:]
                        else:
                            masked_value = "***"
                        print(f"   {key}={masked_value}")
                    else:
                        print(f"   {line}")
                else:
                    print(f"   {line}")
        
        # Check if APIFY_TOKEN is set
        load_dotenv()
        apify_token = os.getenv("APIFY_TOKEN")
        
        if apify_token:
            print(f"\n✅ APIFY_TOKEN is loaded: {apify_token[:10]}...")
        else:
            print("\n❌ APIFY_TOKEN is not loaded from .env file")
            
    else:
        print("❌ .env file does not exist!")
        print("   You need to create a .env file with your API keys")


if __name__ == "__main__":
    # Import here to avoid issues if dotenv is not installed
    try:
        from dotenv import load_dotenv
        check_env_file()
    except ImportError:
        print("❌ python-dotenv not installed. Run: pip install python-dotenv")
