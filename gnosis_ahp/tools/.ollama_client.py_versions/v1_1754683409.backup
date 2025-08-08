"""
AHP Tool for interacting with an Ollama server.
"""
import os
import httpx
import json
from typing import Dict, Any, Optional

from gnosis_ahp.tools.base import tool

# The base URL for the Ollama server is configurable via an environment variable.
AHP_ENVIRONMENT = os.getenv("AHP_ENVIRONMENT", "local")
OLLAMA_BASE_URL = "http://host.docker.internal:11434" if AHP_ENVIRONMENT == "local" else "http://ollama.nuts.services:11434"

@tool(description="Lists the available models from the Ollama server.")
async def list_ollama_models() -> Dict[str, Any]:
    """
    Retrieves a list of available models from the Ollama server.
    """
    api_url = f"{OLLAMA_BASE_URL}/api/tags"
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            models_data = response.json().get("models", [])
            model_names = [model["name"] for model in models_data]
            return {"success": True, "models": model_names}
    except httpx.RequestError as e:
        return {"success": False, "error": f"Could not connect to Ollama server at {OLLAMA_BASE_URL}. Details: {e}"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

@tool(description="Sends a prompt to a large language model running on an Ollama server.")
async def talk_to_ollama(prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Interacts with an Ollama model to get a response from a prompt.
    If no model is specified, it will use the first available model.

    Args:
        prompt: The text prompt to send to the model.
        model: Optional. The name of the model to use (e.g., 'llama3').
    """
    if not prompt:
        return {"success": False, "error": "The 'prompt' parameter is required."}

    if not model:
        print("No model specified, attempting to find a default model...")
        list_result = await list_ollama_models()
        if not list_result.get("success"):
            return list_result # Pass through the error
        
        available_models = list_result.get("models", [])
        if not available_models:
            return {"success": False, "error": "No models available on the Ollama server."}
        
        # Use the first model that is not 'nanonets'
        default_model = next((m for m in available_models if "nanonets" not in m), None)
        
        if not default_model:
            return {"success": False, "error": "No suitable default models found (other than 'nanonets')."}
            
        model = default_model
        print(f"Using default model: {model}")

    api_url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.post(api_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            return {
                "success": True,
                "model": model,
                "response": response_data.get("response", "").strip()
            }
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"API error: {e.response.status_code}", "details": e.response.text}
    except httpx.RequestError as e:
        return {"success": False, "error": f"Could not connect to Ollama server. Details: {e}"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}