"""
Core engine for file diffing, patching, and versioning, using StorageService.
"""
import re
import difflib
import time
from typing import Dict, Any, List
from datetime import datetime

from gnosis_ahp.core.storage_service import StorageService

async def get_file_versions(storage: StorageService, file_path: str, session_id: str) -> List[Dict[str, Any]]:
    """Gets information about all versions of a file from the storage service."""
    versions = []
    # Versions are stored relative to the session's root
    versions_dir = f".{file_path}_versions"
    
    try:
        version_files = await storage.list_files(prefix=versions_dir, session_hash=session_id)
    except FileNotFoundError:
        version_files = []

    for version_file in version_files:
        match = re.match(r"v(\d+)_(\d+)(\..*)?\.backup", version_file['name'])
        if match:
            version_number = int(match.group(1))
            timestamp = int(match.group(2))
            tag = match.group(3)[1:] if match.group(3) else None
            versions.append({
                "version": version_number,
                "timestamp": timestamp,
                "date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                "path": f"{versions_dir}/{version_file['name']}",
                "tag": tag
            })
    
    versions.sort(key=lambda x: x["version"], reverse=True)
    
    try:
        await storage.get_file(file_path, session_hash=session_id)
        versions.insert(0, {"version": "current", "path": file_path})
    except FileNotFoundError:
        pass

    return versions

async def get_next_version_number(storage: StorageService, file_path: str, session_id: str) -> int:
    """Gets the next version number for a file."""
    versions = await get_file_versions(storage, file_path, session_id)
    past_versions = [v for v in versions if v["version"] != "current"]
    if not past_versions:
        return 1
    return max(v["version"] for v in past_versions) + 1

async def create_file_backup(storage: StorageService, file_path: str, session_id: str, change_tag: str = None) -> Dict[str, Any]:
    """Creates a backup of the file in a versioned directory using the storage service."""
    versions_dir = f".{file_path}_versions"
    version_number = await get_next_version_number(storage, file_path, session_id)
    timestamp = int(time.time())
    
    if change_tag:
        safe_tag = re.sub(r'[^\w\-_]', '_', change_tag)
        tag_suffix = f".{safe_tag}"
    else:
        tag_suffix = ""
    
    backup_filename = f"v{version_number}_{timestamp}{tag_suffix}.backup"
    
    try:
        content = await storage.get_file(file_path, session_hash=session_id)
        await storage.save_file(content, f"{versions_dir}/{backup_filename}", session_hash=session_id)
        return {"version": version_number, "change_tag": change_tag}
    except FileNotFoundError:
        return None

async def restore_file_version(storage: StorageService, file_path: str, session_id: str, version_number: int) -> Dict[str, Any]:
    """Restores a specific version of a file."""
    versions = await get_file_versions(storage, file_path, session_id)
    target_version = next((v for v in versions if v["version"] == version_number), None)
    
    if not target_version:
        raise ValueError(f"Version {version_number} not found for {file_path}")
    
    await create_file_backup(storage, file_path, session_id, "pre_restore")
    
    version_content = await storage.get_file(target_version["path"], session_hash=session_id)
    await storage.save_file(version_content, file_path, session_hash=session_id)
    
    return {"success": True, "restored_version": version_number}

def find_fuzzy_match(search_text: str, content: str):
    search_lines = [line for line in search_text.split('\n') if line]
    content_lines = content.split('\n')
    
    best_ratio, best_match_start, best_match_end = 0, -1, -1
    for i in range(len(content_lines) - len(search_lines) + 1):
        chunk = content_lines[i:i+len(search_lines)]
        ratio = difflib.SequenceMatcher(None, search_lines, chunk).ratio()
        if ratio > best_ratio:
            best_ratio, best_match_start, best_match_end = ratio, i, i + len(search_lines)

    return '\n'.join(content_lines[best_match_start:best_match_end]) if best_ratio > 0.7 else None

async def file_diff_write(storage: StorageService, file_path: str, session_id: str, diff_text: str, change_tag: str = None) -> Dict[str, Any]:
    """Applies a diff to a file using the storage service."""
    try:
        original_content = (await storage.get_file(file_path, session_hash=session_id)).decode('utf-8')
    except FileNotFoundError:
        return {"success": False, "error": f"File not found at {file_path}"}

    await create_file_backup(storage, file_path, session_id, change_tag)
    
    match = re.search(r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE', diff_text, re.DOTALL)
    if not match:
        return {"success": False, "error": "Invalid diff format"}
        
    search_block, replace_block = match.groups()
    content_to_replace = find_fuzzy_match(search_block, original_content)
    
    if content_to_replace is None:
        return {"success": False, "error": "Could not find a confident match for the SEARCH block"}

    modified_content = original_content.replace(content_to_replace, replace_block)
    await storage.save_file(modified_content, file_path, session_hash=session_id)
    
    return {"success": True, "changes_applied": True}

async def file_diff_versions(storage: StorageService, file_path: str, session_id: str) -> Dict[str, Any]:
    """Lists all versions of a file using the storage service."""
    versions = await get_file_versions(storage, file_path, session_id)
    return {"success": True, "versions": versions}

async def file_diff_restore(storage: StorageService, file_path: str, session_id: str, version_number: int) -> Dict[str, Any]:
    """Restores a file to a specific version using the storage service."""
    try:
        return await restore_file_version(storage, file_path, session_id, version_number)
    except (ValueError, FileNotFoundError) as e:
        return {"success": False, "error": str(e)}
