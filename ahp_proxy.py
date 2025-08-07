import requests
import json
import urllib.parse

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
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
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

        # Step 2: Start Session
        print("Starting session...")
        session_url = f"{self.base_url}/session/start?bearer_token={self.bearer_token}"
        session_response = requests.get(session_url)
        session_data = self._get_json_or_raise(session_response, "session start")
        self.session_id = session_data.get("session_id")
        if not self.session_id:
            raise ValueError("Failed to start session.")
        print(f"Session started successfully: {self.session_id}")

    def call_tool(self, tool_name: str, **params) -> dict:
        """
        Calls a tool on the AHP server.

        Args:
            tool_name: The name of the tool to call.
            **params: The parameters to pass to the tool.

        Returns:
            The JSON response from the server as a dictionary.
        """
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

# --- Example Usage ---
if __name__ == "__main__":
    # Configuration
    AHP_BASE_URL = "http://localhost:8080"
    AHP_PRE_SHARED_TOKEN = "f00bar"
    
    INSIGHT = "The process of debugging is a spiral. You return to the same points with deeper understanding each time, and the final solution is often a simple truth discovered through complex trial and error."
    MEMORY_NAME = "debugging_insight"

    try:
        # 1. Initialize the client (handles auth and session start)
        client = AHPClient(base_url=AHP_BASE_URL, token=AHP_PRE_SHARED_TOKEN)

        # 2. Save the insightful memory
        save_result = client.call_tool(
            "save_memory", 
            name=MEMORY_NAME, 
            data=INSIGHT
        )
        print("\n--- Result from save_memory ---")
        print(json.dumps(save_result, indent=2))

        # 3. Load the memory back to verify it was saved
        load_result = client.call_tool("get_memory", name=MEMORY_NAME)
        print(f"\n--- Verifying by loading '{MEMORY_NAME}' ---")
        print(json.dumps(load_result, indent=2))
        
        if load_result.get("result", {}).get("data") == INSIGHT:
            print("\nSUCCESS: The insight was saved and verified correctly.")
        else:
            print("\nFAILURE: The insight was not saved correctly.")

    except (ValueError, ConnectionError, requests.exceptions.RequestException) as e:
        print(f"\nAn error occurred: {e}")