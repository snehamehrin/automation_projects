import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY", "")
print(f"API Key found: {api_key[:10]}..." if api_key else "No API key found")
print(f"API Key length: {len(api_key)}")

# Test OpenAI connection
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    # Test with a simple completion
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, this is a test."}],
        max_tokens=10
    )
    
    print("✅ OpenAI API key is working!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ OpenAI API key test failed: {str(e)}")
