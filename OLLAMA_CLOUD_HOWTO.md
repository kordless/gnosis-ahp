# How to Connect to Ollama in the Cloud - A Guide for Gemini

## The Problem
You're having trouble connecting to Ollama in the cloud. Let me explain how the other services do it successfully and what might be going wrong.

## How gnosis-ocr Successfully Connects to Ollama

### 1. URL Configuration
```python
# In gnosis-ocr/app/config.py
ollama_api_url: str = Field(default="http://localhost:11434/api/generate", env="OLLAMA_API_URL")

# For cloud deployment, this is set via environment variable to:
# OLLAMA_API_URL=http://ollama.nuts.services:11434/api/generate
```

### 2. Making Requests (from gnosis-ocr/app/jobs.py)
```python
with requests.post(
    settings.ollama_api_url,  # This becomes http://ollama.nuts.services:11434/api/generate
    json={
        "model": model_name,
        "prompt": prompt,
        "images": [image_base64],  # Optional, for OCR
        "stream": True,
        "options": options
    },
    timeout=timeout,
    stream=True
) as response:
    response.raise_for_status()
    # Process streaming response...
```

## How gnosis-ahp Successfully Connects to Ollama

### 1. URL Configuration (from gnosis_ahp/tools/ollama_client.py)
```python
AHP_ENVIRONMENT = os.getenv("AHP_ENVIRONMENT", "local")
OLLAMA_BASE_URL = "http://host.docker.internal:11434" if AHP_ENVIRONMENT == "local" else os.getenv("OLLAMA_BASE_URL", "http://ollama.nuts.services:11434")
```

### 2. Making Requests
```python
# For listing models
api_url = f"{OLLAMA_BASE_URL}/api/tags"

# For generating text
api_url = f"{OLLAMA_BASE_URL}/api/generate"
payload = {
    "model": model,
    "prompt": prompt,
    "stream": False
}
```

## Common Mistakes and Solutions

### 1. Wrong URL Format
❌ **Wrong:**
- `http://ollama.nuts.services/api/generate` (missing port)
- `http://ollama.nuts.services:11434/generate` (missing /api prefix)
- `https://ollama.nuts.services:11434/api/generate` (Ollama typically uses HTTP, not HTTPS)

✅ **Correct:**
- `http://ollama.nuts.services:11434/api/generate`

### 2. Docker Networking Issues
When running in Docker:
- **Local development**: Use `http://host.docker.internal:11434`
- **Cloud/production**: Use `http://ollama.nuts.services:11434`

### 3. Missing or Wrong Headers
```python
# You typically only need:
headers = {"Content-Type": "application/json"}

# No authentication headers are needed for the nuts.services Ollama instance
```

### 4. Incorrect Request Format
The Ollama API expects specific JSON structure:

```python
# For text generation
{
    "model": "llama3",  # or any available model
    "prompt": "Your prompt here",
    "stream": true,  # or false
    "options": {
        "temperature": 0.7,
        "num_predict": 1000
    }
}

# For image-based requests (OCR)
{
    "model": "llava",  # or vision-capable model
    "prompt": "Describe this image",
    "images": ["base64_encoded_image_data"],
    "stream": false
}
```

### 5. Timeout Issues
Cloud requests might take longer:
```python
# Use appropriate timeouts
timeout = 120  # seconds, adjust based on your needs
```

## Debugging Steps

1. **Test connectivity first:**
   ```bash
   # From your container/environment
   curl http://ollama.nuts.services:11434/api/tags
   ```

2. **Check environment variables:**
   ```python
   import os
   print(f"OLLAMA_URL: {os.getenv('OLLAMA_URL', 'not set')}")
   print(f"OLLAMA_BASE_URL: {os.getenv('OLLAMA_BASE_URL', 'not set')}")
   ```

3. **Try a simple test:**
   ```python
   import requests
   
   url = "http://ollama.nuts.services:11434/api/tags"
   try:
       response = requests.get(url, timeout=10)
       print(f"Status: {response.status_code}")
       print(f"Models: {response.json()}")
   except Exception as e:
       print(f"Error: {e}")
   ```

## Complete Working Example

Here's a minimal working example that should work in the cloud:

```python
import requests
import json

# Configuration
OLLAMA_BASE_URL = "http://ollama.nuts.services:11434"

def test_ollama_connection():
    """Test if we can connect to Ollama"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        response.raise_for_status()
        models = response.json().get("models", [])
        print(f"✅ Connected! Found {len(models)} models")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def generate_text(prompt, model="llama3"):
    """Generate text using Ollama"""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Error generating text: {e}")
        return None

# Test it
if test_ollama_connection():
    result = generate_text("Hello, Ollama!")
    print(f"Response: {result}")
```

## Key Takeaways

1. **Always use the full URL with port**: `http://ollama.nuts.services:11434`
2. **Check your environment variables** - make sure they're being read correctly
3. **Use the correct API endpoints**: `/api/tags`, `/api/generate`, etc.
4. **Handle timeouts appropriately** - cloud requests may take longer
5. **No authentication needed** for the nuts.services instance
6. **Use HTTP, not HTTPS** for the Ollama service

## If It's Still Not Working

Check these common issues:
- Firewall/network restrictions blocking outbound connections to port 11434
- DNS resolution issues (try using IP address if available)
- Container networking configuration (if running in Docker)
- Proxy settings that might be interfering

Remember: Both gnosis-ocr and gnosis-ahp successfully connect to the same Ollama instance at `ollama.nuts.services:11434`, so if they can do it, you can too!
