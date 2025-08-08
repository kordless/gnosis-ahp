import requests
import json
import urllib.parse
import argparse
from pathlib import Path

# --- Configuration ---
URL_MAP = {
    "local": "http://localhost:8080",
    "cloud": "https://ahp.nuts.services"
}
TOKEN_FILE = Path.home() / ".ahp_token"
SESSION_FILE = Path.home() / ".ahp_session"

class AHPClient:
    """
    A client for interacting with an AI Hypercall Protocol (AHP) server.
    Handles authentication and session management automatically.
    """
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.bearer_token = None
        self.session_id = None
        self._authenticate_and_start_session()

    def _get_json_or_raise(self, response, step_name):
        """Helper to decode JSON or raise a detailed exception."""
        try:
            response.raise_for_status()
            if response.status_code == 204:
                return {"success": True, "message": "Operation successful with no content."}
            return response.json()
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from {step_name}.")
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"Error: HTTP error during {step_name}.")
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Text: {e.response.text}")
            raise

    def _authenticate_and_start_session(self):
        """Gets a bearer token and starts a new session."""
        print("Authenticating...")
        auth_url = f"{self.base_url}/auth?token={self.token}"
        auth_response = requests.get(auth_url)
        auth_data = self._get_json_or_raise(auth_response, "authentication")
        self.bearer_token = auth_data.get("bearer_token")
        if not self.bearer_token:
            raise ValueError("Failed to get bearer token.")
        print("Authentication successful.")

        print("Starting session...")
        session_url = f"{self.base_url}/session/start?bearer_token={self.bearer_token}"
        session_response = requests.get(session_url)
        session_data = self._get_json_or_raise(session_response, "session start")
        self.session_id = session_data.get("session_id")
        if not self.session_id:
            raise ValueError("Failed to start session.")
        print(f"Session started successfully: {self.session_id}")

    def call_tool(self, tool_name: str, **params) -> dict:
        """Calls a tool on the AHP server."""
        if not self.bearer_token or not self.session_id:
            raise ConnectionError("Client is not authenticated or session is not started.")
        
        print(f"\nCalling tool '{tool_name}' with params: {params}")
        tool_url = f"{self.base_url}/{tool_name}"
        
        all_params = {
            "bearer_token": self.bearer_token,
            "session_id": self.session_id,
            **params
        }
        
        full_url = f"{tool_url}?{urllib.parse.urlencode(all_params)}"
        
        response = requests.get(full_url)
        return self._get_json_or_raise(response, f"tool call to '{tool_name}'")

# --- Main Test Flow ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A client for the AHP server.")
    parser.add_argument("--env", default="local", choices=["local", "cloud"], help="The environment to target.")
    parser.add_argument("--prompt", default="What is the capital of France?", help="The prompt to send to the Ollama model.")
    args = parser.parse_args()

    try:
        # 1. Initialize the client
        client = AHPClient(base_url=URL_MAP[args.env], token="linkedinPROMO1" if args.env == "cloud" else "f00bar")

        # 2. Test the talk_to_ollama tool
        model = "qwen2:7b"
        prompt = args.prompt
        print(f"\n--- Sending prompt to {model}: '{prompt}' ---")
        ollama_result = client.call_tool(
            "talk_to_ollama",
            model=model,
            prompt=prompt
        )
        print(json.dumps(ollama_result, indent=2))
        
        # 3. Verification
        if ollama_result.get("result", {}).get("success"):
            print(f"\nSUCCESS: The talk_to_ollama tool successfully received a response.")
            print(f"Response: {ollama_result['result']['response']}")
        else:
            print(f"\nFAILURE: The talk_to_ollama tool did not work as expected.")

    except (ValueError, ConnectionError, requests.exceptions.RequestException, AssertionError) as e:
        print(f"\nAn error occurred during the test: {e}")