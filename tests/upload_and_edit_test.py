import requests
import json
import urllib.parse
import os

# --- Step 1: Create a local test file ---
local_file_name = "local_test_file.txt"
initial_content = "Line 1: This is the first line.\nLine 2: This is the second line.\nLine 3: This is the third line."
with open(local_file_name, "w") as f:
    f.write(initial_content)
print(f"Successfully created local file: {local_file_name}")

# --- Step 2: Get a new Bearer Token ---
auth_url = "http://localhost:8080/auth?token=f00bar"
auth_response = requests.get(auth_url)
auth_data = auth_response.json()
bearer_token = auth_data.get("bearer_token")
if not bearer_token:
    print("Failed to get bearer token.")
    exit()
print(f"Successfully obtained bearer token: {bearer_token}")

# --- Step 3: Start a Session ---
session_url = f"http://localhost:8080/session/start?bearer_token={bearer_token}"
session_response = requests.get(session_url)
session_data = session_response.json()
session_id = session_data.get("session_id")
if not session_id:
    print("Failed to start session.")
    exit()
print(f"Successfully started session: {session_id}")

# --- Step 4: Upload the local file to the session ---
save_url = "http://localhost:8080/save_memory"
with open(local_file_name, "r") as f:
    file_content_to_upload = f.read()

# The 'name' for save_memory will be the filename in the session storage
# We'll use the same base name but with a .json extension as that's what save_memory does.
session_file_name = f"{os.path.splitext(local_file_name)[0]}.json"

save_params = {
    "bearer_token": bearer_token,
    "session_id": session_id,
    "name": os.path.splitext(local_file_name)[0], # save_memory uses the name for the filename
    "data": file_content_to_upload
}
save_full_url = f"{save_url}?{urllib.parse.urlencode(save_params)}"
save_response = requests.get(save_full_url)
print("\nResult of uploading file:")
print(save_response.json())

# --- Step 5: Apply a Diff to the uploaded file ---
diff_text = """<<<<<<< SEARCH\nLine 2: This is the second line.\n=======  
Line 2: This is the modified line.\n>>>>>>> REPLACE"""

diff_url = "http://localhost:8080/apply_diff"
diff_params = {
    "bearer_token": bearer_token,
    "session_id": session_id,
    "file_path": session_file_name, # Use the .json filename
    "diff_text": diff_text
}
diff_full_url = f"{diff_url}?{urllib.parse.urlencode(diff_params)}"
diff_response = requests.get(diff_full_url)
print("\nResult of apply_diff:")
print(diff_response.json())

# --- Cleanup ---
os.remove(local_file_name)
print(f"\nCleaned up local file: {local_file_name}")
