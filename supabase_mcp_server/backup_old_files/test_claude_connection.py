#!/usr/bin/env python3
"""
Test Claude Desktop MCP Connection
"""

import subprocess
import json
import time
import os

def test_mcp_connection():
    """Test if MCP server can be started and responds"""
    
    print("🧪 Testing MCP Server Connection")
    print("=" * 40)
    
    # Test 1: Check if server can start
    print("1️⃣ Testing server startup...")
    try:
        server_path = "/Users/snehamehrin/Desktop/automation_projects/supabase_mcp_server/server_http.py"
        
        # Start server process
        process = subprocess.Popen(
            ["python", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send a test request
        test_request = {"method": "tools/list", "params": {}}
        process.stdin.write(json.dumps(test_request) + "\n")
        process.stdin.flush()
        
        # Wait for response
        time.sleep(2)
        
        # Read response
        stdout, stderr = process.communicate(timeout=5)
        
        if stdout:
            try:
                response = json.loads(stdout.strip())
                if "tools" in response:
                    print("✅ Server responds correctly")
                    print(f"✅ Found {len(response['tools'])} tools")
                    for tool in response['tools']:
                        print(f"   - {tool['name']}: {tool['description']}")
                    return True
                else:
                    print("❌ Invalid response format")
                    return False
            except json.JSONDecodeError:
                print("❌ Invalid JSON response")
                print(f"Response: {stdout}")
                return False
        else:
            print("❌ No response from server")
            print(f"Stderr: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def check_claude_config():
    """Check Claude Desktop configuration"""
    
    print("\n2️⃣ Checking Claude Desktop config...")
    
    config_path = os.path.expanduser("~/Library/Application Support/Claude/config.json")
    
    if not os.path.exists(config_path):
        print("❌ Claude config file not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if "mcpServers" not in config:
            print("❌ No MCP servers configured")
            return False
        
        mcp_servers = config["mcpServers"]
        if "supabase-intelligence" not in mcp_servers:
            print("❌ Supabase MCP server not configured")
            return False
        
        server_config = mcp_servers["supabase-intelligence"]
        print("✅ MCP server configured")
        print(f"   Command: {server_config['command']}")
        print(f"   Args: {server_config['args']}")
        
        # Check if server file exists
        server_path = server_config['args'][0]
        if os.path.exists(server_path):
            print("✅ Server file exists")
        else:
            print(f"❌ Server file not found: {server_path}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Config check failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🚀 Claude Desktop MCP Connection Test")
    print("=" * 50)
    
    # Test 1: Check config
    config_ok = check_claude_config()
    
    # Test 2: Test server
    server_ok = test_mcp_connection()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Config: {'✅ OK' if config_ok else '❌ FAILED'}")
    print(f"   Server: {'✅ OK' if server_ok else '❌ FAILED'}")
    
    if config_ok and server_ok:
        print("\n🎉 MCP server is ready!")
        print("\nNext steps:")
        print("1. Restart Claude Desktop completely")
        print("2. Try asking: 'What tables do I have in my database?'")
        print("3. Look for MCP server indicators in Claude Desktop")
    else:
        print("\n⚠️  Issues found. Check the errors above.")
    
    return config_ok and server_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
