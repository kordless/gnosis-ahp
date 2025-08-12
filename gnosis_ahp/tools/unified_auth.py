"""Tool for unified authentication across gnosis services with extended session management."""

import hashlib
import hmac
import base64
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict

from gnosis_ahp.tools.base import tool

# Logger setup
logger = logging.getLogger(__name__)

# Default token lifespan (can be overridden by environment variable)
DEFAULT_TOKEN_LIFESPAN_HOURS = 24

@dataclass
class UnifiedSession:
    """Represents a unified session across gnosis services."""
    session_id: str
    user_email: str
    user_hash: str
    created_at: str
    expires_at: str
    services: Dict[str, bool]  # Which services this session is valid for

@tool(description="Generate a unified authentication token for gnosis services.")
async def generate_unified_token(
    user_email: str,
    secret_key: str,
    services: Optional[str] = None,
    lifespan_hours: Optional[int] = None
) -> Dict[str, str]:
    """
    Generate a unified authentication token that works across gnosis services.
    
    Args:
        user_email: Email of the user
        secret_key: Secret key for token generation
        services: Comma-separated list of services this token is valid for (default: all)
        lifespan_hours: How long the token should be valid in hours (default: 24)
        
    Returns:
        Dictionary containing the token and its metadata
    """
    if not secret_key:
        raise ValueError("Secret key cannot be empty for token generation.")
    
    # Default to 24 hours if not specified
    if lifespan_hours is None:
        lifespan_hours = DEFAULT_TOKEN_LIFESPAN_HOURS
    
    # Create user hash for partitioning
    user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    
    # Parse services
    service_list = services.split(",") if services else ["gnosis-ahp", "gnosis-ocr", "gnosis-wraith"]
    service_dict = {service.strip(): True for service in service_list}
    
    # Create session
    session_id = hashlib.sha256(f"{user_email}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    
    # Calculate expiration
    expiration_time = datetime.now(timezone.utc) + timedelta(hours=lifespan_hours)
    
    # Create payload
    payload = {
        "session_id": session_id,
        "user_email": user_email,
        "user_hash": user_hash,
        "exp": expiration_time.isoformat(),
        "services": service_dict
    }
    
    # Encode payload
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode('utf-8')
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).rstrip(b'=').decode('utf-8')
    
    # Create signature
    signature_generator = hmac.new(secret_key.encode('utf-8'), encoded_payload.encode('utf-8'), hashlib.sha256)
    signature = signature_generator.digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b'=').decode('utf-8')
    
    # Create token
    token = f"{encoded_payload}.{encoded_signature}"
    
    return {
        "token": token,
        "session_id": session_id,
        "user_email": user_email,
        "user_hash": user_hash,
        "expires_at": expiration_time.isoformat(),
        "services": service_dict,
        "lifespan_hours": lifespan_hours
    }

@tool(description="Validate a unified authentication token.")
async def validate_unified_token(
    token: str,
    secret_key: str,
    required_service: Optional[str] = None
) -> Dict[str, any]:
    """
    Validate a unified authentication token.
    
    Args:
        token: The token to validate
        secret_key: Secret key for token validation
        required_service: Service that this token must be valid for
        
    Returns:
        Dictionary containing validation result and session information
    """
    logger.info("--- Starting Unified Token Validation ---")
    
    if not secret_key:
        logger.error("Validation failed: Secret key is missing.")
        raise ValueError("Secret key cannot be empty for token validation.")
    
    if not token:
        logger.warning("Validation failed: Missing token.")
        raise ValueError("Missing token.")
    
    logger.info(f"Received token: {token}")
    parts = token.split('.')
    if len(parts) != 2:
        logger.warning(f"Validation failed: Invalid token format. Expected 2 parts, got {len(parts)}.")
        raise ValueError("Invalid token format.")
    
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
            raise ValueError("Invalid token signature.")
            
    except (TypeError, base64.binascii.Error) as e:
        logger.error(f"Validation failed: Error decoding signature. Details: {e}")
        raise ValueError("Invalid signature encoding.")
    
    # Decode the payload and check for expiration
    try:
        payload_bytes = base64.urlsafe_b64decode(encoded_payload + '==')
        payload = json.loads(payload_bytes.decode('utf-8'))
        logger.info(f"Decoded Payload: {payload}")
        
        # Check expiration
        expiration_time = datetime.fromisoformat(payload["exp"])
        current_time = datetime.now(timezone.utc)
        
        logger.info(f"Token expiration time: {expiration_time.isoformat()}")
        logger.info(f"Current UTC time:      {current_time.isoformat()}")
        
        is_expired = expiration_time < current_time
        logger.info(f"Expiration check result: {'Expired' if is_expired else 'Not Expired'}")
        
        if is_expired:
            raise ValueError("Token has expired.")
            
        # Check service access if required
        if required_service:
            services = payload.get("services", {})
            if required_service not in services or not services[required_service]:
                raise ValueError(f"Token not valid for service: {required_service}")
        
        # Create session object
        session = UnifiedSession(
            session_id=payload["session_id"],
            user_email=payload["user_email"],
            user_hash=payload["user_hash"],
            created_at=payload.get("created_at", "unknown"),
            expires_at=payload["exp"],
            services=payload.get("services", {})
        )
        
        logger.info("--- Token Validation Successful ---")
        return {
            "valid": True,
            "session": asdict(session),
            "message": "Token is valid"
        }
        
    except (TypeError, base64.binascii.Error, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Validation failed: Error decoding or parsing payload. Details: {e}")
        raise ValueError(f"Invalid payload: {str(e)}")

@tool(description="Extend the lifespan of a unified authentication token.")
async def extend_token_lifespan(
    token: str,
    secret_key: str,
    additional_hours: int = 24
) -> Dict[str, str]:
    """
    Extend the lifespan of an existing unified authentication token.
    
    Args:
        token: The token to extend
        secret_key: Secret key for token validation and regeneration
        additional_hours: Number of hours to extend the token by
        
    Returns:
        Dictionary containing the new token and its metadata
    """
    # First validate the existing token
    validation_result = await validate_unified_token.execute(token=token, secret_key=secret_key)
    
    if not validation_result.get("valid"):
        raise ValueError("Cannot extend invalid token")
    
    session_data = validation_result["session"]
    
    # Calculate new expiration time
    new_expiration = datetime.fromisoformat(session_data["expires_at"]) + timedelta(hours=additional_hours)
    
    # Update payload with new expiration
    payload = {
        "session_id": session_data["session_id"],
        "user_email": session_data["user_email"],
        "user_hash": session_data["user_hash"],
        "exp": new_expiration.isoformat(),
        "services": session_data["services"],
        "created_at": session_data["created_at"]
    }
    
    # Encode new payload
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode('utf-8')
    encoded_payload = base64.urlsafe_b64encode(payload_bytes).rstrip(b'=').decode('utf-8')
    
    # Create new signature
    signature_generator = hmac.new(secret_key.encode('utf-8'), encoded_payload.encode('utf-8'), hashlib.sha256)
    signature = signature_generator.digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b'=').decode('utf-8')
    
    # Create new token
    new_token = f"{encoded_payload}.{encoded_signature}"
    
    return {
        "token": new_token,
        "session_id": session_data["session_id"],
        "user_email": session_data["user_email"],
        "user_hash": session_data["user_hash"],
        "expires_at": new_expiration.isoformat(),
        "services": session_data["services"],
        "message": f"Token extended by {additional_hours} hours"
    }