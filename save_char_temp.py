import requests
import json
import urllib.parse

# The character data from the previous step
character_data = {
  "id": "CHAR_3282",
  "name": "Rahel",
  "emotional_state": {
    "primary": "Surprise",
    "secondary": "Sadness"
  },
  "trait": "Clever",
  "quirk": "Always hums when thinking",
  "hexagram": {
    "current": "Ch'ien (The Creative, Heaven)",
    "meaning": "Strength, creativity, pure yang energy, leadership",
    "becoming": "Ta Yu (Possession in Great Measure)",
    "changing_lines": [4, 5]
  },
  "philosophy": "Embrace the creative power within to manifest great works.",
  "narrative": "Rahel lives in a state of constant wonder, easily amazed. In quiet moments, a profound melancholy reveals the depth of Rahel's character."
}

# URL parameters
base_url = "http://localhost:8080/save_character"
bearer_token = "8c1c9fc274753c1f466de17deecf3b7f00f3043c3f22a974af9f42ad8e44c845"
session_id = "9b281fa2-22cb-4ac1-af37-fe3edc5de0fa"

# The character data needs to be a JSON string
params = {
    "bearer_token": bearer_token,
    "session_id": session_id,
    "character": json.dumps(character_data)
}

# Construct the full URL and make the request
full_url = f"{base_url}?{urllib.parse.urlencode(params)}"
response = requests.get(full_url)

print(response.json())
