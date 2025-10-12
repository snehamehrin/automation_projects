#!/usr/bin/env python3
"""
Fix .env file issues
"""

import os
from pathlib import Path


def fix_env_file():
    """Fix .env file format and content."""
    print("🔧 Fixing .env file...")
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file doesn't exist. Creating one...")
        create_new_env_file()
        return
    
    # Read current content
    with open(env_path, 'r') as f:
        content = f.read()
    
    print("📄 Current .env file content:")
    print("-" * 40)
    print(content)
    print("-" * 40)
    
    # Check for common issues
    issues = []
    
    if "APIFY_TOKEN" not in content:
        issues.append("APIFY_TOKEN not found")
    
    if "=" not in content:
        issues.append("No key=value pairs found")
    
    # Check for quotes around values
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'APIFY_TOKEN' in line and '=' in line:
            key, value = line.split('=', 1)
            if value.startswith('"') and value.endswith('"'):
                issues.append(f"Line {i}: APIFY_TOKEN has quotes around value")
            if value.strip() == "":
                issues.append(f"Line {i}: APIFY_TOKEN has empty value")
    
    if issues:
        print(f"\n⚠️  Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        
        print(f"\n🔧 Let's fix this...")
        fix_env_content(content)
    else:
        print("\n✅ .env file looks correct!")
        print("   The issue might be with how it's being loaded.")


def create_new_env_file():
    """Create a new .env file."""
    print("📝 Creating new .env file...")
    
    # Get Apify token from user
    apify_token = input("Enter your Apify token: ").strip()
    
    if not apify_token:
        print("❌ No token provided!")
        return
    
    env_content = f"""# Supabase Configuration
SUPABASE_URL=https://wbpupfkbjmncmjmhyfha.supabase.co
SUPABASE_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here
SUPABASE_BRANDS_TABLE=prospects
SUPABASE_RESULTS_TABLE=analysis_results

# Apify Configuration
APIFY_TOKEN={apify_token}

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Logging Configuration
LOG_LEVEL=INFO
"""
    
    with open(".env", 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created!")
    print("   You can now run: python test_apify.py")


def fix_env_content(content):
    """Fix common .env file issues."""
    print("🔧 Fixing .env file content...")
    
    # Get Apify token from user
    apify_token = input("Enter your Apify token: ").strip()
    
    if not apify_token:
        print("❌ No token provided!")
        return
    
    # Fix the content
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if line.strip().startswith('APIFY_TOKEN'):
            # Replace with correct format
            fixed_lines.append(f"APIFY_TOKEN={apify_token}")
        else:
            fixed_lines.append(line)
    
    # Write fixed content
    with open(".env", 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("✅ .env file fixed!")
    print("   You can now run: python test_apify.py")


if __name__ == "__main__":
    fix_env_file()
