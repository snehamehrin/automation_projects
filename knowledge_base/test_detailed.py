import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "")

print("=== API Key Analysis ===")
print(f"Raw key: {repr(api_key)}")
print(f"Length: {len(api_key)}")
print(f"First 20 chars: {api_key[:20]}")
print(f"Last 20 chars: {api_key[-20:]}")
print(f"Contains spaces: {' ' in api_key}")
print(f"Contains tabs: {'\\t' in api_key}")
print(f"Contains newlines: {'\\n' in api_key}")
print(f"Contains carriage returns: {'\\r' in api_key}")

# Check if it's a valid OpenAI key format
if api_key.startswith('sk-'):
    print("✅ Starts with sk-")
    if len(api_key) < 100:
        print("✅ Length looks reasonable")
    else:
        print("⚠️  Length is unusually long")
else:
    print("❌ Does not start with sk-")

# Test with a simple request
print("\n=== Testing API Key ===")
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    # Test with a very simple request
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    
    print("✅ API key works!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ API key test failed: {str(e)}")
    
    # Try to get more details about the error
    if "401" in str(e):
        print("This is an authentication error. The API key is invalid.")
    elif "403" in str(e):
        print("This is a permission error. The API key might be valid but lacks permissions.")
    elif "429" in str(e):
        print("This is a rate limit error. The API key works but you've hit rate limits.")
    else:
        print("This is a different type of error.")
