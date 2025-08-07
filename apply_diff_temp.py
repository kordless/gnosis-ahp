import requests
import urllib.parse

# The diff content to apply
diff_text = """<<<<<<< SEARCH
Line 2: This is the second line.
=======
Line 2: This is the modified line.
>>>>>>> REPLACE"""

# URL parameters
base_url = "http://localhost:8080/apply_diff"
bearer_token = "a6022dbb5db77ce967f2250389b992ea3ad6bd25d3a714f12477773e8e66310a"
# We need the absolute path to the file
file_path = "C:/Users/kord/Code/gnosis/gnosis-ahp/test_file_for_diff.txt"

params = {
    "bearer_token": bearer_token,
    "file_path": file_path,
    "diff_text": diff_text
}

# Construct the full URL and make the request
full_url = f"{base_url}?{urllib.parse.urlencode(params)}"
response = requests.get(full_url)

print(response.json())
