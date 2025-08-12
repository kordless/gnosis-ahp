"""Tool for cross-service file operations in the Gnosis ecosystem."""

import hashlib
import json
from typing import Dict, Optional, List, Union
from dataclasses import dataclass, asdict

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core.storage_service import StorageService

# File operation types
FILE_OPERATION_TYPES = [
    "copy",
    "move",
    "sync",
    "backup"
]

@dataclass
class FileOperation:
    """Represents a cross-service file operation."""
    operation_id: str
    operation_type: str
    source_service: str
    source_path: str
    destination_service: str
    destination_path: str
    user_email: str
    user_hash: str
    created_at: str
    status: str  # pending, in_progress, completed, failed
    metadata: Dict[str, any]

@tool(description="Copy a file between gnosis services.", session_required=True)
async def copy_file_between_services(
    session: Dict[str, any],
    source_service: str,
    source_path: str,
    destination_service: str,
    destination_path: str,
    user_email: Optional[str] = None
) -> Dict[str, any]:
    """
    Copy a file from one gnosis service to another.
    
    Args:
        session: Session context (automatically provided)
        source_service: Name of the source service (gnosis-ocr, gnosis-wraith, etc.)
        source_path: Path to the source file
        destination_service: Name of the destination service
        destination_path: Path where the file should be copied
        user_email: Email of the user (if not using session)
        
    Returns:
        Dictionary containing operation result
    """
    # Get user information
    if user_email is None and 'user_email' in session:
        user_email = session['user_email']
    
    if not user_email:
        return {
            "success": False,
            "message": "User email is required"
        }
    
    # Create user hash
    user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    
    # In a real implementation, this would:
    # 1. Connect to the source service's storage
    # 2. Retrieve the file
    # 3. Connect to the destination service's storage
    # 4. Save the file to the destination
    
    # For this simulation, we'll just create an operation record
    import uuid
    operation_id = str(uuid.uuid4())
    
    operation = FileOperation(
        operation_id=operation_id,
        operation_type="copy",
        source_service=source_service,
        source_path=source_path,
        destination_service=destination_service,
        destination_path=destination_path,
        user_email=user_email,
        user_hash=user_hash,
        created_at=session.get("created_at", ""),
        status="pending",
        metadata={
            "simulated": True,
            "message": "In a full implementation, this would copy the file between services"
        }
    )
    
    return {
        "success": True,
        "operation": asdict(operation),
        "message": f"File copy operation scheduled from {source_service}:{source_path} to {destination_service}:{destination_path}"
    }

@tool(description="Move a file between gnosis services.", session_required=True)
async def move_file_between_services(
    session: Dict[str, any],
    source_service: str,
    source_path: str,
    destination_service: str,
    destination_path: str,
    user_email: Optional[str] = None
) -> Dict[str, any]:
    """
    Move a file from one gnosis service to another (copy then delete).
    
    Args:
        session: Session context (automatically provided)
        source_service: Name of the source service
        source_path: Path to the source file
        destination_service: Name of the destination service
        destination_path: Path where the file should be moved
        user_email: Email of the user (if not using session)
        
    Returns:
        Dictionary containing operation result
    """
    # Get user information
    if user_email is None and 'user_email' in session:
        user_email = session['user_email']
    
    if not user_email:
        return {
            "success": False,
            "message": "User email is required"
        }
    
    # Create user hash
    user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    
    # In a real implementation, this would:
    # 1. Connect to the source service's storage
    # 2. Retrieve the file
    # 3. Connect to the destination service's storage
    # 4. Save the file to the destination
    # 5. Delete the file from the source
    
    # For this simulation, we'll just create an operation record
    import uuid
    operation_id = str(uuid.uuid4())
    
    operation = FileOperation(
        operation_id=operation_id,
        operation_type="move",
        source_service=source_service,
        source_path=source_path,
        destination_service=destination_service,
        destination_path=destination_path,
        user_email=user_email,
        user_hash=user_hash,
        created_at=session.get("created_at", ""),
        status="pending",
        metadata={
            "simulated": True,
            "message": "In a full implementation, this would move the file between services"
        }
    )
    
    return {
        "success": True,
        "operation": asdict(operation),
        "message": f"File move operation scheduled from {source_service}:{source_path} to {destination_service}:{destination_path}"
    }

@tool(description="Synchronize files between gnosis services.", session_required=True)
async def sync_files_between_services(
    session: Dict[str, any],
    source_service: str,
    source_path: str,
    destination_service: str,
    destination_path: str,
    user_email: Optional[str] = None
) -> Dict[str, any]:
    """
    Synchronize files between gnosis services (copy newer files).
    
    Args:
        session: Session context (automatically provided)
        source_service: Name of the source service
        source_path: Path to the source directory
        destination_service: Name of the destination service
        destination_path: Path where files should be synchronized
        user_email: Email of the user (if not using session)
        
    Returns:
        Dictionary containing operation result
    """
    # Get user information
    if user_email is None and 'user_email' in session:
        user_email = session['user_email']
    
    if not user_email:
        return {
            "success": False,
            "message": "User email is required"
        }
    
    # Create user hash
    user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    
    # In a real implementation, this would:
    # 1. Connect to both service's storage
    # 2. Compare file timestamps
    # 3. Copy newer files from source to destination
    
    # For this simulation, we'll just create an operation record
    import uuid
    operation_id = str(uuid.uuid4())
    
    operation = FileOperation(
        operation_id=operation_id,
        operation_type="sync",
        source_service=source_service,
        source_path=source_path,
        destination_service=destination_service,
        destination_path=destination_path,
        user_email=user_email,
        user_hash=user_hash,
        created_at=session.get("created_at", ""),
        status="pending",
        metadata={
            "simulated": True,
            "message": "In a full implementation, this would synchronize files between services"
        }
    )
    
    return {
        "success": True,
        "operation": asdict(operation),
        "message": f"File synchronization operation scheduled from {source_service}:{source_path} to {destination_service}:{destination_path}"
    }

@tool(description="Backup files from a gnosis service.", session_required=True)
async def backup_service_files(
    session: Dict[str, any],
    service: str,
    source_path: str,
    backup_service: str = "gnosis-backup",
    backup_path: Optional[str] = None,
    user_email: Optional[str] = None
) -> Dict[str, any]:
    """
    Backup files from a gnosis service to a backup service.
    
    Args:
        session: Session context (automatically provided)
        service: Name of the service to backup
        source_path: Path to the source directory
        backup_service: Name of the backup service (default: gnosis-backup)
        backup_path: Path where files should be backed up (default: same as source_path)
        user_email: Email of the user (if not using session)
        
    Returns:
        Dictionary containing operation result
    """
    # Get user information
    if user_email is None and 'user_email' in session:
        user_email = session['user_email']
    
    if not user_email:
        return {
            "success": False,
            "message": "User email is required"
        }
    
    # Create user hash
    user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:12]
    
    # Set backup path if not provided
    if backup_path is None:
        backup_path = source_path
    
    # In a real implementation, this would:
    # 1. Connect to the source service's storage
    # 2. Retrieve the files
    # 3. Connect to the backup service's storage
    # 4. Save the files to the backup location
    
    # For this simulation, we'll just create an operation record
    import uuid
    operation_id = str(uuid.uuid4())
    
    operation = FileOperation(
        operation_id=operation_id,
        operation_type="backup",
        source_service=service,
        source_path=source_path,
        destination_service=backup_service,
        destination_path=backup_path,
        user_email=user_email,
        user_hash=user_hash,
        created_at=session.get("created_at", ""),
        status="pending",
        metadata={
            "simulated": True,
            "message": "In a full implementation, this would backup files to the backup service"
        }
    )
    
    return {
        "success": True,
        "operation": asdict(operation),
        "message": f"File backup operation scheduled from {service}:{source_path} to {backup_service}:{backup_path}"
    }

@tool(description="List file operations for a user.", session_required=True)
async def list_file_operations(
    session: Dict[str, any],
    user_email: Optional[str] = None,
    operation_type: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, any]:
    """
    List file operations for a user.
    
    Args:
        session: Session context (automatically provided)
        user_email: Email of the user (if not using session)
        operation_type: Filter by operation type (copy, move, sync, backup)
        status: Filter by status (pending, in_progress, completed, failed)
        
    Returns:
        Dictionary containing list of operations
    """
    # Get user information
    if user_email is None and 'user_email' in session:
        user_email = session['user_email']
    
    if not user_email:
        return {
            "success": False,
            "message": "User email is required"
        }
    
    # In a real implementation, this would query a shared storage system
    # For now, we'll return an empty list
    
    filters = []
    if operation_type:
        filters.append(f"type: {operation_type}")
    if status:
        filters.append(f"status: {status}")
    
    filter_str = f" ({', '.join(filters)})" if filters else ""
    
    return {
        "user_email": user_email,
        "operations": [],
        "message": f"In a full implementation, this would list all file operations for the user{filter_str}"
    }