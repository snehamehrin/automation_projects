#!/usr/bin/env python3
"""
Test Runner for Dynamic Supabase MCP Server
Runs all tests in the correct order
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🧪 {description}")
    print(f"Running: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ FAILED")
            if result.stderr:
                print("Error:", result.stderr)
            if result.stdout:
                print("Output:", result.stdout)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def main():
    """Run all tests in sequence"""
    print("🚀 Dynamic Supabase MCP Server - Test Suite")
    print("=" * 60)
    
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        # Core functionality tests (no external dependencies)
        ("python test_core.py", "Core functionality test"),
        
        # Simple demo (with mocked Supabase)
        ("python examples/simple_demo.py", "Simple demo test"),
        
        # Unit tests (core components only)
        ("python -m pytest tests/test_supabase_client.py -v", "Supabase client tests"),
    ]
    
    # Optional tests (require MCP package)
    optional_tests = [
        ("python test_quick.py", "Quick functionality test (requires MCP)"),
        ("python -m pytest tests/test_mcp_tools.py -v", "MCP tools tests (requires MCP)"),
        ("python -m pytest tests/integration/ -v", "Integration tests (requires MCP)"),
        ("python examples/dynamic_discovery_demo.py", "Dynamic discovery demo (requires MCP)"),
    ]
    
    passed = 0
    total = len(tests)
    
    # Run core tests
    for command, description in tests:
        success = run_command(command, description)
        if success:
            passed += 1
        else:
            print(f"\n⚠️  Test failed: {description}")
            print("   Continuing with remaining tests...")
    
    # Try optional tests (may fail if MCP not available)
    print(f"\n🔄 Trying optional tests (may fail if MCP package not available)...")
    optional_passed = 0
    for command, description in optional_tests:
        success = run_command(command, description)
        if success:
            optional_passed += 1
        else:
            print(f"   ⚠️  Optional test skipped: {description}")
    
    print("\n" + "=" * 60)
    print(f"📊 Core Test Results: {passed}/{total} tests passed")
    print(f"📊 Optional Test Results: {optional_passed}/{len(optional_tests)} tests passed")
    print(f"📊 Total: {passed + optional_passed}/{total + len(optional_tests)} tests passed")
    
    if passed == total:
        print("🎉 All core tests passed! Your MCP server foundation is solid!")
        print("\nNext steps:")
        print("1. Create .env file with your Supabase credentials")
        print("2. Test with real database: python examples/simple_demo.py")
        if optional_passed == len(optional_tests):
            print("3. Connect to Claude Desktop for full MCP testing")
        else:
            print("3. Install MCP package when available: pip install mcp")
            print("4. Then connect to Claude Desktop for full MCP testing")
    else:
        print("⚠️  Some core tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Check Python path and imports")
        print("- See MCP_INSTALLATION.md for MCP package status")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
