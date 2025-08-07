"""
A comprehensive tool for managing files and directories within a user's session.
This tool uses the StorageService for all file operations to ensure security and session isolation.
"""

import os
import shutil
import glob
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core.storage_service import StorageService

# --- Helper Functions ---

async def _get_versions(storage: StorageService, path: str, session_id: str) -> List[Dict[str, Any]]:
    """Helper to list version history for a file."""
    versions = []
    versions_dir = f".{path}_versions"
    try:
        version_files = await storage.list_files(prefix=versions_dir, session_hash=session_id)
    except FileNotFoundError:
        version_files = []

    for version_file in version_files:
        match = re.match(r"v(\d+)_(\d+)(\..*)?\.backup", version_file['name'])
        if match:
            versions.append({
                "version": int(match.group(1)),
                "timestamp": int(match.group(2)),
                "date": datetime.fromtimestamp(int(match.group(2))).strftime("%Y-%m-%d %H:%M:%S"),
                "tag": match.group(3)[1:] if match.group(3) else None
            })
    versions.sort(key=lambda x: x["version"], reverse=True)
    return versions

async def _create_backup(storage: StorageService, path: str, session_id: str, tag: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Helper to create a versioned backup of a file."""
    versions = await _get_versions(storage, path, session_id)
    next_version = max(v["version"] for v in versions) + 1 if versions else 1
    
    versions_dir = f".{path}_versions"
    timestamp = int(time.time())
    tag_suffix = f".{tag}" if tag else ""
    backup_filename = f"v{next_version}_{timestamp}{tag_suffix}.backup"
    
    try:
        content = await storage.get_file(path, session_hash=session_id)
        await storage.save_file(content, f"{versions_dir}/{backup_filename}", session_hash=session_id)
        return {"version": next_version, "tag": tag}
    except FileNotFoundError:
        return None

# --- Main Tool ---

@tool(description="Manage files and directories. Supports: create, read, write, list, move, delete, search, copy, versions, restore.", session_required=True)
async def file_manager(
    action: str,
    path: str = None,
    dest: str = None,
    content: Optional[Any] = None,
    pattern: Optional[str] = None,
    show_hidden: bool = False,
    recursive: bool = False,
    max_depth: int = 2,
    create_backup: bool = True,
    version: Union[int, str, None] = None,
    encoding: str = "utf-8",
    session: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    A comprehensive tool for file and directory management within a secure session.
    """
    if not session:
        return {"success": False, "error": "A session is required for file operations."}
    
    storage: StorageService = session["storage"]
    session_id = session["id"]

    # --- Action Router ---
    try:
        action_lower = action.lower()
        if action_lower == "create":
            if not path: return {"success": False, "error": "'path' is required for create action."}
            if create_backup: await _create_backup(storage, path, session_id, "pre-create")
            content_bytes = content.encode(encoding) if isinstance(content, str) else b""
            await storage.save_file(content_bytes, path, session_hash=session_id)
            return {"success": True, "message": f"File '{path}' created."}

        elif action_lower == "read":
            if not path: return {"success": False, "error": "'path' is required for read action."}
            file_content = await storage.get_file(path, session_hash=session_id)
            return {"success": True, "content": file_content.decode(encoding)}

        elif action_lower == "write":
            if not path: return {"success": False, "error": "'path' is required for write action."}
            if create_backup: await _create_backup(storage, path, session_id, "pre-write")
            content_bytes = content.encode(encoding) if isinstance(content, str) else b""
            await storage.save_file(content_bytes, path, session_hash=session_id)
            return {"success": True, "message": f"Content written to '{path}'."}

        elif action_lower == "list":
            if not path: path = "" # List root by default
            files = await storage.list_files(prefix=path, session_hash=session_id)
            return {"success": True, "files": files}

        elif action_lower == "move":
            if not path or not dest: return {"success": False, "error": "'path' and 'dest' are required for move action."}
            await storage.move_file(source_path=path, dest_path=dest, session_hash=session_id)
            return {"success": True, "message": f"Moved '{path}' to '{dest}'."}

        elif action_lower == "delete":
            if not path: return {"success": False, "error": "'path' is required for delete action."}
            await storage.delete_file(path, session_hash=session_id)
            return {"success": True, "message": f"Deleted '{path}'."}

        elif action_lower == "search":
            if not pattern: return {"success": False, "error": "'pattern' is required for search action."}
            files = await storage.list_files(prefix=pattern, session_hash=session_id, recursive=True)
            return {"success": True, "matches": files}

        elif action_lower == "copy":
            if not path or not dest: return {"success": False, "error": "'path' and 'dest' are required for copy action."}
            original_content = await storage.get_file(path, session_hash=session_id)
            await storage.save_file(original_content, dest, session_hash=session_id)
            return {"success": True, "message": f"Copied '{path}' to '{dest}'."}

        elif action_lower == "versions":
            if not path: return {"success": False, "error": "'path' is required for versions action."}
            versions = _get_versions(storage, path, session_id)
            return {"success": True, "versions": versions}

        elif action_lower == "restore":
            if not path or version is None: return {"success": False, "error": "'path' and 'version' are required for restore action."}
            versions = _get_versions(storage, path, session_id)
            target_version = next((v for v in versions if v["version"] == int(version)), None)
            if not target_version: return {"success": False, "error": f"Version '{version}' not found."}
            
            if create_backup: await _create_backup(storage, path, session_id, "pre-restore")
            
            versions_dir = f".{path}_versions"
            tag_suffix = f".{target_version['tag']}" if target_version['tag'] else ""
            backup_filename = f"v{target_version['version']}_{target_version['timestamp']}{tag_suffix}.backup"
            
            version_content = await storage.get_file(f"{versions_dir}/{backup_filename}", session_hash=session_id)
            await storage.save_file(version_content, path, session_hash=session_id)
            return {"success": True, "message": f"Restored '{path}' to version {version}."}

        else:
            return {"success": False, "error": f"Invalid action '{action}'. Valid actions are: create, read, write, list, move, delete, search, copy, versions, restore."}

    except FileNotFoundError as e:
        return {"success": False, "error": f"File not found: {e}"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {e}"}
