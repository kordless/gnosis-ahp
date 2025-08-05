import os
import secrets
from datetime import datetime, timedelta
from typing import Dict

from gnosis_ahp.core.errors import invalid_bearer_token_exception

# In-memory store for tokens. In a real application, use a database.
# Format: {token: {"expires": expiration_datetime, "agent_id": agent_id}}
active_tokens: Dict[str, Dict] = {}

# Token configuration
TOKEN_LIFESPAN_MINUTES = int(os.getenv("TOKEN_LIFESPAN_MINUTES", 60))

def generate_token(agent_id: str = "default_agent") -> str:
    """Generates a secure token, stores it, and returns it."""
    token = secrets.token_hex(32)
    expires = datetime.utcnow() + timedelta(minutes=TOKEN_LIFESPAN_MINUTES)
    active_tokens[token] = {"expires": expires, "agent_id": agent_id}
    return token

def validate_token_from_query(token: str) -> Dict:
    """
    Validates a bearer token passed as a query parameter.
    Raises AHPException on failure.
    """
    if not token or token not in active_tokens:
        raise invalid_bearer_token_exception("Invalid or missing bearer_token.")
    
    token_data = active_tokens[token]
    if token_data["expires"] < datetime.utcnow():
        # Clean up expired token
        del active_tokens[token]
        raise invalid_bearer_token_exception("Bearer token has expired.")
        
    return {"agent_id": token_data["agent_id"]}