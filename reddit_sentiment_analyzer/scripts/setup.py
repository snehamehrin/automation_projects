#!/usr/bin/env python3
"""
Setup script for the Reddit Sentiment Analyzer.

This script helps set up the development environment and initializes
the application with proper configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_requirements():
    """Check if required tools are installed."""
    print("🔍 Checking requirements...")
    
    requirements = {
        "python": "python3 --version",
        "pip": "pip --version",
        "git": "git --version"
    }
    
    missing = []
    for tool, command in requirements.items():
        if not run_command(command, f"Checking {tool}"):
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing requirements: {', '.join(missing)}")
        print("Please install the missing tools and try again.")
        return False
    
    print("✅ All requirements satisfied")
    return True


def setup_environment():
    """Set up the environment file."""
    print("🔧 Setting up environment...")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your API keys and configuration")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ No env.example file found")
        return False
    
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    # Install in development mode
    if not run_command("pip install -e .[dev]", "Installing development dependencies"):
        return False
    
    # Install pre-commit hooks
    if not run_command("pre-commit install", "Installing pre-commit hooks"):
        print("⚠️  Pre-commit installation failed, continuing...")
    
    return True


def setup_database():
    """Set up the database."""
    print("🗄️  Setting up database...")
    
    # Check if database URL is configured
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "DATABASE_URL" in content and "postgresql://" in content:
                print("✅ Database URL configured")
                return True
    
    print("⚠️  Database not configured. Please set DATABASE_URL in .env file")
    return False


def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    
    if not run_command("pytest tests/ -v", "Running test suite"):
        print("⚠️  Some tests failed, but setup can continue")
        return False
    
    print("✅ All tests passed")
    return True


def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        "logs",
        "uploads",
        "temp",
        "config",
        "data/raw",
        "data/processed"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")
    return True


def main():
    """Main setup function."""
    print("🚀 Setting up Reddit Sentiment Analyzer")
    print("=" * 50)
    
    steps = [
        ("Checking requirements", check_requirements),
        ("Creating directories", create_directories),
        ("Setting up environment", setup_environment),
        ("Installing dependencies", install_dependencies),
        ("Setting up database", setup_database),
        ("Running tests", run_tests)
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}")
        if not step_func():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 50)
    
    if failed_steps:
        print(f"⚠️  Setup completed with warnings:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease address the warnings above before running the application.")
    else:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys")
        print("2. Run 'make dev' to start the development server")
        print("3. Visit http://localhost:8000/docs for API documentation")
    
    return len(failed_steps) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
