import requests
import json
import urllib.parse

# --- Configuration ---
BASE_URL = "http://localhost:8080"
# BASE_URL = "https://ahp.nuts.services" # Uncomment for cloud testing

def get_json_or_exit(response, step_name):
    """Helper function to decode JSON or print error and exit."""
    try:
        return response.json()
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {step_name}. Status code: {response.status_code}")
        print(f"Response text: {response.text}")
        exit()

# --- Main Test Flow ---
if __name__ == "__main__":
    try:
        # 1. Initialize the client (handles auth and session start)
        client = AHPClient(base_url=BASE_URL, token="f00bar")

        # 2. Generate and auto-save a new agent
        print("\n--- Generating and auto-saving a new agent ---")
        generate_result = client.call_tool("generate_agent") # save=True by default
        agent_data = generate_result.get("result", {})
        print(json.dumps(generate_result, indent=2))

        if not agent_data or agent_data.get("save_error"):
            print("\nError: Failed to generate or save agent.")
            exit()
            
        agent_name = agent_data.get("name")
        if not agent_name:
            print("\nError: Generated agent has no name.")
            exit()

        # 3. Embody the newly created agent (no save step needed)
        print(f"\n--- Embodying the new agent '{agent_name}' ---")
        embody_result = client.call_tool("embody_agent", agent_name=agent_name)
        print(json.dumps(embody_result, indent=2))

        # 4. Verification
        if embody_result.get("result", {}).get("success"):
            print(f"\nSUCCESS: Agent '{agent_name}' was generated, auto-saved, and embodied correctly.")
            print("\n--- Embodiment System Prompt ---")
            print(embody_result["result"]["prompt"])
        else:
            print(f"\nFAILURE: Could not embody the auto-saved agent '{agent_name}'.")

    except (ValueError, ConnectionError, requests.exceptions.RequestException) as e:
        print(f"\nAn error occurred: {e}")

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
