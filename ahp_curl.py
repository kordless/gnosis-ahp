import requests
import json
import subprocess
import sys
import os
from pathlib import Path
import argparse

# --- Configuration ---
TOKEN_FILE = Path.home() / ".ahp_token"
SESSION_FILE = Path.home() / ".ahp_session"

URL_MAP = {
    "local": "http://localhost:8080",
    "cloud": "https://ahp.nuts.services"
}

def save_token(token: str):
    """Saves the bearer token to a local file."""
    with open(TOKEN_FILE, "w") as f:
        f.write(token)
    print(f"Bearer token saved to {TOKEN_FILE}")

def load_token() -> str:
    """Loads the bearer token from a local file."""
    if not TOKEN_FILE.exists():
        print("Error: No bearer token found. Please run 'auth' first.")
        sys.exit(1)
    with open(TOKEN_FILE, "r") as f:
        return f.read().strip()

def save_session(session_id: str):
    """Saves the session ID to a local file."""
    with open(SESSION_FILE, "w") as f:
        f.write(session_id)
    print(f"Session ID saved to {SESSION_FILE}")

def load_session() -> str:
    """Loads the session ID from a local file."""
    if not SESSION_FILE.exists():
        print("Error: No session found. Please run 'auth' to start a new session.")
        sys.exit(1)
    with open(SESSION_FILE, "r") as f:
        return f.read().strip()

def main():
    """
    A Python wrapper for curl to interact with an AHP server.
    Handles authentication and token management automatically.
    """
    parser = argparse.ArgumentParser(description="A curl wrapper for the AHP.")
    parser.add_argument("command", help="The command to execute (e.g., 'auth', 'list_agents').")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the command.")
    parser.add_argument("--env", default="local", choices=["local", "cloud"], help="The environment to target.")
    
    args = parser.parse_args()
    
    base_url = URL_MAP[args.env]
    command = args.command
    
    if command == "auth":
        if not args.args:
            print("Usage: python ahp_curl.py auth <pre_shared_key>")
            sys.exit(1)
        pre_shared_key = args.args[0]
        
        print(f"Authenticating with {base_url}...")
        auth_url = f"{base_url}/auth?token={pre_shared_key}"
        try:
            response = requests.get(auth_url)
            response.raise_for_status()
            auth_data = response.json()
            bearer_token = auth_data.get("bearer_token")
            if not bearer_token:
                print("Error: Failed to get bearer token.")
                sys.exit(1)
            save_token(bearer_token)

            print("Starting new session...")
            session_url = f"{base_url}/session/start?bearer_token={bearer_token}"
            session_response = requests.get(session_url)
            session_response.raise_for_status()
            session_data = session_response.json()
            session_id = session_data.get("session_id")
            if not session_id:
                print("Error: Failed to start session.")
                sys.exit(1)
            save_session(session_id)

        except requests.exceptions.RequestException as e:
            print(f"Error during authentication: {e}")
            sys.exit(1)

    else:
        tool_name = command
        bearer_token = load_token()
        session_id = load_session()
        
        url = f"{base_url}/{tool_name}?bearer_token={bearer_token}&session_id={session_id}"
        if args.args:
            url += "&" + "&".join(args.args)
            
        print(f"Executing: curl {url}")
        subprocess.run(["curl", url])

if __name__ == "__main__":
    main()
