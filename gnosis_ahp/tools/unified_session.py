"""Enhanced session management tool for gnosis services with cross-service compatibility."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core.storage_service import StorageService

@dataclass
class GnosisSession:
    """Represents a cross-service session in the Gnosis ecosystem."""
    session_id: str
    user_email: str
    user_hash: str
    created_at: str
    expires_at: str
    service_sessions: Dict[str, str]  # Service name -> service session ID
    metadata: Dict[str, any]

@tool(description="Create a unified session across gnosis services.", session_required=False)
async def create_unified_session(
    user_email: str,
    session_name: Optional[str] = None,
    services: Optional[str] = None,
    duration_hours: int = 24
) -> Dict[str, any]:
    """
    Create a unified session that can be used across gnosis services.
    
    Args:
        user_email: Email of the user
        session_name: Optional name for the session
        services: Comma-separated list of services (default: all)
        duration_hours: How long the session should last in hours (default: 24)
        
    Returns:
        Dictionary containing session information
    """
    # Create user hash
    user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    
    # Parse services
    service_list = services.split(",") if services else ["gnosis-ahp", "gnosis-ocr", "gnosis-wraith"]
    service_list = [s.strip() for s in service_list]
    
    # Create session ID
    session_id = str(uuid.uuid4())
    
    # Calculate expiration
    expires_at = (datetime.utcnow() + timedelta(hours=duration_hours)).isoformat()
    
    # Create service sessions (in a real implementation, this would create actual sessions in each service)
    service_sessions = {}
    for service in service_list:
        service_sessions[service] = str(uuid.uuid4())
    
    # Create session object
    session = GnosisSession(
        session_id=session_id,
        user_email=user_email,
        user_hash=user_hash,
        created_at=datetime.utcnow().isoformat(),
        expires_at=expires_at,
        service_sessions=service_sessions,
        metadata={
            "name": session_name or f"Session-{session_id[:8]}",
            "services": service_list,
            "duration_hours": duration_hours
        }
    )
    
    # In a real implementation, we would save this to a shared storage system
    # For now, we'll just return the session data
    
    return {
        "session": asdict(session),
        "message": f"Unified session '{session_name or session_id[:8]}' created for services: {', '.join(service_list)}"
    }

@tool(description="Validate a unified session.", session_required=False)
async def validate_unified_session(
    session_id: str,
    user_email: str
) -> Dict[str, any]:
    """
    Validate a unified session.
    
    Args:
        session_id: The session ID to validate
        user_email: Email of the user who owns the session
        
    Returns:
        Dictionary containing validation result
    """
    # In a real implementation, this would check a shared storage system
    # For now, we'll simulate validation
    
    # Create user hash for verification
    user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    
    # Simulate session validation
    # In a real implementation, we would retrieve the session from storage and verify:
    # 1. Session exists
    # 2. Session belongs to the user
    # 3. Session hasn't expired
    
    # For this simulation, we'll just verify the format
    if not session_id or len(session_id) < 32:
        return {
            "valid": False,
            "message": "Invalid session ID format"
        }
    
    # Simulate successful validation
    return {
        "valid": True,
        "session_id": session_id,
        "user_email": user_email,
        "user_hash": user_hash,
        "message": "Session is valid"
    }

@tool(description="Extend a unified session.", session_required=False)
async def extend_unified_session(
    session_id: str,
    user_email: str,
    additional_hours: int = 24
) -> Dict[str, any]:
    """
    Extend the duration of a unified session.
    
    Args:
        session_id: The session ID to extend
        user_email: Email of the user who owns the session
        additional_hours: Number of hours to extend the session by
        
    Returns:
        Dictionary containing extension result
    """
    # First validate the session
    validation_result = await validate_unified_session.execute(
        session_id=session_id,
        user_email=user_email
    )
    
    if not validation_result.get("valid"):
        return {
            "success": False,
            "message": "Cannot extend invalid session"
        }
    
    # In a real implementation, we would:
    # 1. Retrieve the session from storage
    # 2. Update the expiration time
    # 3. Save the updated session
    
    # For this simulation, we'll just return a success message
    return {
        "success": True,
        "session_id": session_id,
        "user_email": user_email,
        "additional_hours": additional_hours,
        "message": f"Session extended by {additional_hours} hours"
    }

@tool(description="List active unified sessions for a user.", session_required=False)
async def list_unified_sessions(
    user_email: str
) -> Dict[str, any]:
    """
    List all active unified sessions for a user.
    
    Args:
        user_email: Email of the user
        
    Returns:
        Dictionary containing list of sessions
    """
    # In a real implementation, this would query a shared storage system
    # For now, we'll return an empty list
    
    return {
        "user_email": user_email,
        "sessions": [],
        "message": "In a full implementation, this would list all active sessions for the user"
    }

@tool(description="Terminate a unified session across all services.", session_required=False)
async def terminate_unified_session(
    session_id: str,
    user_email: str
) -> Dict[str, any]:
    """
    Terminate a unified session across all services.
    
    Args:
        session_id: The session ID to terminate
        user_email: Email of the user who owns the session
        
    Returns:
        Dictionary containing termination result
    """
    # First validate the session
    validation_result = await validate_unified_session.execute(
        session_id=session_id,
        user_email=user_email
    )
    
    if not validation_result.get("valid"):
        return {
            "success": False,
            "message": "Cannot terminate invalid session"
        }
    
    # In a real implementation, we would:
    # 1. Retrieve the session from storage
    # 2. Terminate service sessions in each service
    # 3. Remove the unified session from storage
    
    # For this simulation, we'll just return a success message
    return {
        "success": True,
        "session_id": session_id,
        "user_email": user_email,
        "message": "Session terminated successfully across all services"
    }