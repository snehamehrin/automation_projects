import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "")

print(f"API Key: {api_key}")
print(f"Length: {len(api_key)}")
print(f"Starts with sk-: {api_key.startswith('sk-')}")
print(f"Contains spaces: {' ' in api_key}")
print(f"Contains newlines: {'\\n' in api_key}")

# Test if it's a valid format
if api_key.startswith('sk-') and len(api_key) > 50:
    print("✅ API key format looks correct")
else:
    print("❌ API key format looks incorrect")
