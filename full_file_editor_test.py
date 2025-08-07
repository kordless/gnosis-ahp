import requests
import json
import urllib.parse

# --- Configuration ---
BASE_URL = "https://ahp.nuts.services"
# BASE_URL = "http://localhost:8080" # Uncomment for local testing

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
auth_url = f"{BASE_URL}/auth?token=wUT4h3FU3K"
# auth_url = f"{BASE_URL}/auth?token=f00bar"
auth_response = requests.get(auth_url)
auth_data = get_json_or_exit(auth_response, "auth endpoint")
    
bearer_token = auth_data.get("bearer_token")
if not bearer_token:
    print("Failed to get bearer token.")
    exit()
print(f"Successfully obtained bearer token: {bearer_token}")

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

# --- Step 3: Save the initial file content to the session ---
print("\nAttempting to save file...")
save_url = f"{BASE_URL}/save_memory"
file_content = "Line 1: This is the first line.\nLine 2: This is the second line.\nLine 3: This is the third line."
save_params = {
    "bearer_token": bearer_token,
    "session_id": session_id,
    "name": "test_file_for_diff", # This will be the filename
    "data": file_content
}
save_full_url = f"{save_url}?{urllib.parse.urlencode(save_params)}"
save_response = requests.get(save_full_url)
save_data = get_json_or_exit(save_response, "save memory")
print("\nResult of saving file:")
print(save_data)

# --- Step 4: Apply the Diff ---
print("\nAttempting to apply diff...")
diff_text = """<<<<<<< SEARCH
Line 2: This is the second line.
=======
Line 2: This is the modified line.
>>>>>>> REPLACE"""

diff_url = f"{BASE_URL}/apply_diff"
file_path = "test_file_for_diff.json" 

diff_params = {
    "bearer_token": bearer_token,
    "session_id": session_id,
    "file_path": file_path,
    "diff_text": diff_text
}
diff_full_url = f"{diff_url}?{urllib.parse.urlencode(diff_params)}"
diff_response = requests.get(diff_full_url)
diff_data = get_json_or_exit(diff_response, "apply diff")
print("\nResult of apply_diff:")
print(diff_data)