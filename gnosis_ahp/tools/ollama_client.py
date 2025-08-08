"""
AHP Tool for interacting with an Ollama server.
"""
import os
import httpx
import json
import logging
from typing import Dict, Any, Optional

from gnosis_ahp.tools.base import tool

logger = logging.getLogger(__name__)

# The base URL for the Ollama server is configurable via an environment variable.
AHP_ENVIRONMENT = os.getenv("AHP_ENVIRONMENT", "local")

# Get the base URL and strip any accidental quotes
base_url_env = os.getenv("OLLAMA_BASE_URL", "http://ollama.nuts.services:11434")
# Strip single and double quotes that might have been accidentally included
base_url_env = base_url_env.strip("'\"")

OLLAMA_BASE_URL = "http://host.docker.internal:11434" if AHP_ENVIRONMENT == "local" else "https://ollama.nuts.services"


# Log the configuration for debugging
logger.info(f"Ollama client configuration - AHP_ENVIRONMENT: {AHP_ENVIRONMENT}, OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")

@tool(description="Lists the available models from the Ollama server.")
async def list_ollama_models() -> Dict[str, Any]:
    """
    Retrieves a list of available models from the Ollama server.
    """
    api_url = f"{OLLAMA_BASE_URL}/api/tags"
    logger.info(f"Attempting to list models from: {api_url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(api_url)
            response.raise_for_status()
            models_data = response.json().get("models", [])
            model_names = [model["name"] for model in models_data]
            logger.info(f"Successfully retrieved {len(model_names)} models")
            return {"success": True, "models": model_names}
    except httpx.ConnectError as e:
        error_msg = f"Connection error to {OLLAMA_BASE_URL}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except httpx.TimeoutException as e:
        error_msg = f"Timeout connecting to {OLLAMA_BASE_URL}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"Request error to {OLLAMA_BASE_URL}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error connecting to {OLLAMA_BASE_URL}: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}

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
        logger.info("No model specified, attempting to find a default model...")
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
        logger.info(f"Using default model: {model}")

    api_url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    logger.info(f"Sending request to {api_url} with model: {model}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.post(api_url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            logger.info("Successfully received response from Ollama")
            return {
                "success": True,
                "model": model,
                "response": response_data.get("response", "").strip()
            }
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error {e.response.status_code} from Ollama API"
        logger.error(f"{error_msg}: {e.response.text}")
        return {"success": False, "error": error_msg, "details": e.response.text}
    except httpx.ConnectError as e:
        error_msg = f"Connection error to {OLLAMA_BASE_URL}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except httpx.TimeoutException as e:
        error_msg = f"Timeout connecting to {OLLAMA_BASE_URL}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"Request error to {OLLAMA_BASE_URL}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}
