#!/usr/bin/env python3
"""
Install required dependencies for the Reddit Sentiment Analyzer.

Run this script to install all required packages.
"""

import subprocess
import sys


def install_package(package):
    """Install a package using pip."""
    try:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False


def main():
    """Install all required dependencies."""
    print("🚀 Installing Reddit Sentiment Analyzer Dependencies")
    print("=" * 50)
    
    # Required packages
    packages = [
        "supabase",
        "python-dotenv",
        "openai",
        "httpx",
        "pydantic",
        "fastapi",
        "uvicorn",
        "structlog",
        "rich"
    ]
    
    success_count = 0
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Installation Results: {success_count}/{len(packages)} packages installed")
    
    if success_count == len(packages):
        print("🎉 All dependencies installed successfully!")
        print("\nNext steps:")
        print("1. Run: python simple_test.py")
        print("2. If that works, run: python test_analysis.py")
    else:
        print("⚠️  Some packages failed to install.")
        print("You may need to install them manually:")
        for package in packages:
            print(f"   pip install {package}")
    
    return success_count == len(packages)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
