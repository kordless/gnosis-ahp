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

# --- Step 1: Get a new Bearer Token ---
print(f"Attempting to get bearer token from {BASE_URL}...")
auth_url = f"{BASE_URL}/auth?token=f00bar"
auth_response = requests.get(auth_url)
auth_data = get_json_or_exit(auth_response, "auth endpoint")
    
bearer_token = auth_data.get("bearer_token")
if not bearer_token:
    print("Failed to get bearer token.")
    exit()
print(f"Successfully obtained bearer token.")

# --- Step 2: Start a Session ---
print(f"\nAttempting to start session...")
session_url = f"{BASE_URL}/session/start?bearer_token={bearer_token}"
session_response = requests.get(session_url)
session_data = get_json_or_exit(session_response, "session start")

session_id = session_data.get("session_id")
if not session_id:
    print("Failed to start session.")
    exit()
print(f"Successfully started session: {session_id}")

# --- Step 3: Generate a new agent ---
print("\nAttempting to generate an agent...")
generate_url = f"{BASE_URL}/generate_agent"
generate_params = {
    "bearer_token": bearer_token,
    "session_id": session_id
}
generate_full_url = f"{generate_url}?{urllib.parse.urlencode(generate_params)}"
generate_response = requests.get(generate_full_url)
generate_data = get_json_or_exit(generate_response, "generate agent")
print("\nResult of generating agent:")
print(json.dumps(generate_data, indent=2))

agent_data = generate_data.get("result", {})
if not agent_data:
    print("Failed to get agent data from generation step.")
    exit()

agent_name = agent_data.get("name")
if not agent_name:
    print("Generated agent has no name.")
    exit()

# --- Step 4: Add a memory to the agent ---
print(f"\nAdding memory to '{agent_name}'...")
memory_to_add = "Remembers the scent of rain on dry earth."
if "memories" not in agent_data:
    agent_data["memories"] = []
agent_data["memories"].append(memory_to_add)
print("Memory added successfully.")
print(json.dumps(agent_data, indent=2))

# --- Step 5: Save the modified agent ---
print(f"\nAttempting to save '{agent_name}'...")
save_url = f"{BASE_URL}/save_agent"
save_params = {
    "bearer_token": bearer_token,
    "session_id": session_id,
    "agent_name": agent_name,
    "agent_data": json.dumps(agent_data)
}
save_full_url = f"{save_url}?{urllib.parse.urlencode(save_params)}"
save_response = requests.get(save_full_url)
save_data = get_json_or_exit(save_response, "save agent")
print("\nResult of saving agent:")
print(json.dumps(save_data, indent=2))

# --- Step 6: Load the agent to verify the change ---
print(f"\nAttempting to load '{agent_name}' to verify memory...")
load_url = f"{BASE_URL}/load_agent"
load_params = {
    "bearer_token": bearer_token,
    "session_id": session_id,
    "agent_name": agent_name
}
load_full_url = f"{load_url}?{urllib.parse.urlencode(load_params)}"
load_response = requests.get(load_full_url)
load_data = get_json_or_exit(load_response, "load agent")
print("\nResult of loading agent:")
print(json.dumps(load_data, indent=2))

# --- Verification ---
loaded_memories = load_data.get("result", {}).get("data", {}).get("memories", [])
if memory_to_add in loaded_memories:
    print(f"\nSUCCESS: Memory was correctly saved and loaded for agent '{agent_name}'.")
else:
    print(f"\nFAILURE: Memory was not found after loading the agent.")
