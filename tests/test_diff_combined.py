import requests
import json
import urllib.parse

# --- Step 1: Get a new Bearer Token ---
auth_url = "http://localhost:8080/auth?token=f00bar"
auth_response = requests.get(auth_url)
auth_data = auth_response.json()
bearer_token = auth_data.get("bearer_token")

if not bearer_token:
    print("Failed to get bearer token.")
    exit()

print(f"Successfully obtained bearer token: {bearer_token}")

# --- Step 2: Start a Session ---
session_url = f"http://localhost:8080/session/start?bearer_token={bearer_token}"
session_response = requests.get(session_url)
session_data = session_response.json()
session_id = session_data.get("session_id")

if not session_id:
    print("Failed to start session.")
    exit()

print(f"Successfully started session: {session_id}")

# --- Step 3: Apply the Diff ---
diff_text = """<<<<<<< SEARCH
Line 2: This is the second line.
======= 
Line 2: This is the modified line.
>>>>>>> REPLACE"""

base_url = "http://localhost:8080/apply_diff"
file_path = "test_file_for_diff.txt" # Path is now relative to the session storage

params = {
    "bearer_token": bearer_token,
    "session_id": session_id,
    "file_path": file_path,
    "diff_text": diff_text
}

full_url = f"{base_url}?{urllib.parse.urlencode(params)}"
response = requests.get(full_url)

print("\nResult of apply_diff:")
print(response.json())