#!/usr/bin/env python3
"""
MCP Server Diagnostic Tool
Tests if your Supabase MCP server is properly configured
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def check_python():
    """Check Python installation"""
    print_section("1. Checking Python Installation")
    
    print(f"✅ Python version: {sys.version}")
    print(f"✅ Python executable: {sys.executable}")
    
    return sys.executable


def check_dependencies():
    """Check if required packages are installed"""
    print_section("2. Checking Dependencies")
    
    required_packages = ['supabase', 'pydantic', 'python-dotenv', 'httpx']
    missing = []
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            else:
                __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def check_env_file():
    """Check if .env file exists and is configured"""
    print_section("3. Checking Environment Configuration")
    
    env_path = Path(__file__).parent / '.env'
    
    if not env_path.exists():
        print("❌ .env file not found")
        print(f"Expected location: {env_path}")
        print("\nCreate a .env file with:")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_KEY=your-anon-key-here")
        return False
    
    print(f"✅ .env file found at: {env_path}")
    
    # Check if it has required variables
    with open(env_path) as f:
        content = f.read()
        
    has_url = 'SUPABASE_URL' in content
    has_key = 'SUPABASE_KEY' in content
    
    if has_url:
        print("✅ SUPABASE_URL is configured")
    else:
        print("❌ SUPABASE_URL is missing")
    
    if has_key:
        print("✅ SUPABASE_KEY is configured")
    else:
        print("❌ SUPABASE_KEY is missing")
    
    return has_url and has_key


def check_server_file():
    """Check if server.py exists"""
    print_section("4. Checking Server File")
    
    server_path = Path(__file__).parent / 'server.py'
    
    if not server_path.exists():
        print(f"❌ server.py not found at: {server_path}")
        return False, None
    
    print(f"✅ server.py found at: {server_path}")
    print(f"✅ Absolute path: {server_path.absolute()}")
    
    return True, str(server_path.absolute())


def check_imports():
    """Check if the server can import its modules"""
    print_section("5. Checking Module Imports")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.supabase_mcp.config import get_settings
        print("✅ Can import config module")
    except Exception as e:
        print(f"❌ Cannot import config: {e}")
        return False
    
    try:
        from src.supabase_mcp.supabase_client import SupabaseClient
        print("✅ Can import supabase_client module")
    except Exception as e:
        print(f"❌ Cannot import supabase_client: {e}")
        return False
    
    try:
        from src.supabase_mcp.mcp_tools import DynamicSupabaseMCPTools
        print("✅ Can import mcp_tools module")
    except Exception as e:
        print(f"⚠️  Cannot import mcp_tools (expected - MCP package not available): {e}")
        print("   This is normal since the MCP package isn't available yet")
    
    return True


def generate_config(python_exe, server_path):
    """Generate Claude Desktop config"""
    print_section("6. Generating Claude Desktop Config")
    
    config = {
        "mcpServers": {
            "supabase-intelligence": {
                "command": python_exe,
                "args": [str(Path(__file__).parent / 'server_https.py')],
                "env": {
                    "SUPABASE_URL": "https://your-project.supabase.co",
                    "SUPABASE_KEY": "your-anon-key-here"
                }
            }
        }
    }
    
    print("Copy this configuration to your Claude Desktop config file:")
    print("\n" + "="*60)
    print(json.dumps(config, indent=2))
    print("="*60)
    
    # Detect OS and show config location
    if sys.platform == 'darwin':
        config_path = "~/Library/Application Support/Claude/claude_desktop_config.json"
    elif sys.platform == 'win32':
        config_path = "%APPDATA%\\Claude\\claude_desktop_config.json"
    else:
        config_path = "~/.config/Claude/claude_desktop_config.json"
    
    print(f"\nConfig file location: {config_path}")
    
    return config


def test_server_startup():
    """Test if the server can start"""
    print_section("7. Testing Server Startup")
    
    print("Testing HTTPS server (will timeout after 5 seconds)...")
    print("This is normal - we just want to see if it starts without errors.")
    
    try:
        # Try to run the HTTPS server with a timeout
        result = subprocess.run(
            [sys.executable, 'server_https.py'],
            cwd=Path(__file__).parent,
            capture_output=True,
            timeout=5,
            text=True
        )
    except subprocess.TimeoutExpired:
        print("✅ HTTPS Server started successfully (timed out as expected)")
        return True
    except Exception as e:
        print(f"❌ HTTPS Server failed to start: {e}")
        return False
    
    if result.returncode != 0:
        print(f"❌ HTTPS Server exited with error:")
        print(result.stderr)
        return False
    
    return True


def main():
    """Run all diagnostic checks"""
    print("🚀 Supabase MCP Server Diagnostic Tool")
    print("This tool will help you troubleshoot your MCP server setup")
    
    # Run checks
    python_exe = check_python()
    deps_ok = check_dependencies()
    
    if not deps_ok:
        print("\n⚠️  Please install missing dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    env_ok = check_env_file()
    server_ok, server_path = check_server_file()
    imports_ok = check_imports()
    
    if not all([env_ok, server_ok]):
        print("\n❌ Some critical checks failed. Please fix the issues above.")
        sys.exit(1)
    
    # Generate config
    config = generate_config(python_exe, server_path)
    
    # Test server startup
    startup_ok = test_server_startup()
    
    # Final summary
    print_section("✅ Diagnostic Summary")
    
    if all([deps_ok, env_ok, server_ok, imports_ok, startup_ok]):
        print("🎉 All checks passed! Your MCP server is ready.")
        print("\nNext steps:")
        print("1. Copy the config above to your Claude Desktop config file")
        print("2. Update SUPABASE_URL and SUPABASE_KEY with your actual credentials")
        print("3. Restart Claude Desktop")
        print("4. Look for the 🔌 icon in Claude Desktop to see your connected MCP server")
    else:
        print("⚠️  Some checks failed. Review the errors above.")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
