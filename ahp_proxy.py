import requests
import json
import urllib.parse

# --- Configuration ---
BASE_URL = "http://localhost:8080"
AHP_PRE_SHARED_TOKEN = "f00bar"

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
    try:
        # 1. Initialize the client
        client = AHPClient(base_url=BASE_URL, token=AHP_PRE_SHARED_TOKEN)

        # 2. Test the cast_hexagram tool
        print(f"\n--- Casting the I Ching ---")
        casting_result = client.call_tool("cast_hexagram")
        print(json.dumps(casting_result, indent=2))
        
        if casting_result.get("result", {}).get("primary"):
            print("\nSUCCESS: The cast_hexagram tool successfully returned a reading.")
        else:
            print("\nFAILURE: There was an issue with the cast_hexagram tool.")

    except (ValueError, ConnectionError, requests.exceptions.RequestException, AssertionError) as e:
        print(f"\nAn error occurred during the test: {e}")
