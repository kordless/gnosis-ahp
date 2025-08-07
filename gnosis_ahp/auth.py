"""
Stateless, signed token authentication using HMAC.
This avoids the need for a shared token store in a multi-worker environment.
"""
import os
import hmac
import hashlib
import base64
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict

from gnosis_ahp.core.errors import invalid_bearer_token_exception

# --- Logger ---
logger = logging.getLogger(__name__)

# --- Configuration ---
TOKEN_LIFESPAN_MINUTES = int(os.getenv("TOKEN_LIFESPAN_MINUTES", 60))

def generate_token(agent_id: str, secret_key: str) -> str:
    """
    Generates a secure, stateless, signed token using a provided secret key.
    """
    if not secret_key:
        raise ValueError("Secret key cannot be empty for token generation.")

    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_LIFESPAN_MINUTES)
    payload = {
        "agent_id": agent_id,
        "exp": expiration_time.isoformat()
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode('utf-8')
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).rstrip(b'=').decode('utf-8')

    signature_generator = hmac.new(secret_key.encode('utf-8'), encoded_payload.encode('utf-8'), hashlib.sha256)
    signature = signature_generator.digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b'=').decode('utf-8')

    return f"{encoded_payload}.{encoded_signature}"

def validate_token_from_query(token: str, secret_key: str) -> Dict:
    """
    Validates a stateless bearer token from a query parameter using a provided secret key.
    """
    logger.info("--- Starting Token Validation ---")
    
    if not secret_key:
        logger.error("Validation failed: Secret key is missing.")
        raise ValueError("Secret key cannot be empty for token validation.")
    
    # Log a masked version of the secret key for security
    masked_key = secret_key[:8] + "..." if len(secret_key) > 8 else secret_key
    logger.info(f"Using secret key starting with: '{masked_key}'")

    if not token:
        logger.warning("Validation failed: Missing bearer_token.")
        raise invalid_bearer_token_exception("Missing bearer_token.")

    logger.info(f"Received token: {token}")
    parts = token.split('.')
    if len(parts) != 2:
        logger.warning(f"Validation failed: Invalid token format. Expected 2 parts, got {len(parts)}.")
        raise invalid_bearer_token_exception("Invalid token format.")
    
    encoded_payload, encoded_signature = parts
    logger.info(f"Encoded Payload: {encoded_payload}")
    logger.info(f"Encoded Signature: {encoded_signature}")

    # Verify the signature
    try:
        expected_signature_generator = hmac.new(secret_key.encode('utf-8'), encoded_payload.encode('utf-8'), hashlib.sha256)
        expected_signature = expected_signature_generator.digest()
        
        provided_signature = base64.urlsafe_b64decode(encoded_signature + '==')
        
        is_valid_signature = hmac.compare_digest(expected_signature, provided_signature)
        logger.info(f"Signature comparison result: {'Success' if is_valid_signature else 'Failure'}")

        if not is_valid_signature:
            raise invalid_bearer_token_exception("Invalid token signature.")
            
    except (TypeError, base64.binascii.Error) as e:
        logger.error(f"Validation failed: Error decoding signature. Details: {e}")
        raise invalid_bearer_token_exception("Invalid signature encoding.")

    # Decode the payload and check for expiration
    try:
        payload_bytes = base64.urlsafe_b64decode(encoded_payload + '==')
        payload = json.loads(payload_bytes.decode('utf-8'))
        logger.info(f"Decoded Payload: {payload}")
        
        expiration_time = datetime.fromisoformat(payload["exp"])
        current_time = datetime.now(timezone.utc)
        
        logger.info(f"Token expiration time: {expiration_time.isoformat()}")
        logger.info(f"Current UTC time:      {current_time.isoformat()}")
        
        is_expired = expiration_time < current_time
        logger.info(f"Expiration check result: {'Expired' if is_expired else 'Not Expired'}")

        if is_expired:
            raise invalid_bearer_token_exception("Bearer token has expired.")
            
    except (TypeError, base64.binascii.Error, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Validation failed: Error decoding or parsing payload. Details: {e}")
        raise invalid_bearer_token_exception("Invalid payload.")
        
    logger.info("--- Token Validation Successful ---")
    return {"agent_id": payload["agent_id"]}
