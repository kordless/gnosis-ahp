"""
Core engine for file diffing, patching, and versioning.
A simplified and cleaned-up version of the original file_diff_editor.py,
containing only the essential functions for the AHP file_editor tool.
"""
import os
import re
import shutil
import difflib
import pathlib
import time
from typing import Dict, Any, List
from datetime import datetime

def ensure_version_dir(file_path: str) -> str:
    """Ensures that a versions directory exists for the given file."""
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    versions_dir = os.path.join(directory, f".{filename}_versions")
    os.makedirs(versions_dir, exist_ok=True)
    return versions_dir

def get_file_versions(file_path: str) -> List[Dict[str, Any]]:
    """Gets information about all versions of a file."""
    versions = []
    if not os.path.exists(file_path):
        return versions
    
    versions_dir = ensure_version_dir(file_path)
    if not os.path.exists(versions_dir):
        return versions

    version_files = [f for f in os.listdir(versions_dir) if os.path.isfile(os.path.join(versions_dir, f))]
    for version_file in version_files:
        match = re.match(r"v(\d+)_(\d+)(\..*)?\.backup", version_file)
        if match:
            version_number = int(match.group(1))
            timestamp = int(match.group(2))
            tag = match.group(3)[1:] if match.group(3) else None
            version_path = os.path.join(versions_dir, version_file)
            stats = os.stat(version_path)
            versions.append({
                "version": version_number,
                "timestamp": timestamp,
                "date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                "path": version_path,
                "tag": tag
            })
    
    versions.sort(key=lambda x: x["version"], reverse=True)
    stats = os.stat(file_path)
    versions.insert(0, {
        "version": "current",
        "timestamp": int(stats.st_mtime),
        "date": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "path": file_path
    })
    return versions

def get_next_version_number(file_path: str) -> int:
    """Gets the next version number for a file."""
    versions = get_file_versions(file_path)
    past_versions = [v for v in versions if v["version"] != "current"]
    if not past_versions:
        return 1
    return max(v["version"] for v in past_versions) + 1

def create_file_backup(file_path: str, change_tag: str = None) -> Dict[str, Any]:
    """Creates a backup of the file in a versioned directory."""
    versions_dir = ensure_version_dir(file_path)
    version_number = get_next_version_number(file_path)
    timestamp = int(time.time())
    
    if change_tag:
        safe_tag = re.sub(r'[^\w\-_]', '_', change_tag)
        backup_filename = f"v{version_number}_{timestamp}.{safe_tag}.backup"
    else:
        backup_filename = f"v{version_number}_{timestamp}.backup"
    
    backup_path = os.path.join(versions_dir, backup_filename)
    shutil.copy2(file_path, backup_path)
    return {"version": version_number, "path": backup_path, "change_tag": change_tag}

def restore_file_version(file_path: str, version_number: int) -> Dict[str, Any]:
    """Restores a specific version of a file."""
    versions = get_file_versions(file_path)
    target_version = next((v for v in versions if v["version"] == version_number), None)
    
    if not target_version:
        raise ValueError(f"Version {version_number} not found for {file_path}")
    
    create_file_backup(file_path, "pre_restore")
    shutil.copy2(target_version["path"], file_path)
    return {"success": True, "restored_version": version_number}

def find_fuzzy_match(search_text: str, content: str):
    """Finds the best fuzzy match for a search block."""
    search_lines = [line for line in search_text.split('\n') if line]
    content_lines = content.split('\n')
    
    best_ratio = 0
    best_match_start = -1
    best_match_end = -1

    for i in range(len(content_lines) - len(search_lines) + 1):
        chunk = content_lines[i:i+len(search_lines)]
        matcher = difflib.SequenceMatcher(None, search_lines, chunk)
        ratio = matcher.ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match_start = i
            best_match_end = i + len(search_lines)

    if best_ratio > 0.7: # Confidence threshold
        return '\n'.join(content_lines[best_match_start:best_match_end])
    return None

async def file_diff_write(file_path: str, diff_text: str, change_tag: str = None) -> Dict[str, Any]:
    """Applies a diff to a file."""
    # In a containerized environment, the file path will be relative to the /app directory
    abs_file_path = os.path.join("/app", file_path)
    if not os.path.exists(abs_file_path):
        return {"success": False, "error": f"File not found at {abs_file_path}"}

    create_file_backup(abs_file_path, change_tag)
    
    original_content = pathlib.Path(abs_file_path).read_text(encoding="utf-8")
    
    # Simple SEARCH/REPLACE block parsing
    pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
    match = re.search(pattern, diff_text, re.DOTALL)
    
    if not match:
        return {"success": False, "error": "Invalid diff format"}
        
    search_block, replace_block = match.groups()
    
    # Use fuzzy matching to find the content to replace
    content_to_replace = find_fuzzy_match(search_block, original_content)
    
    if content_to_replace is None:
        return {"success": False, "error": "Could not find a confident match for the SEARCH block"}

    modified_content = original_content.replace(content_to_replace, replace_block)
    
    pathlib.Path(abs_file_path).write_text(modified_content, encoding="utf-8")
    
    return {"success": True, "changes_applied": True}

async def file_diff_versions(file_path: str) -> Dict[str, Any]:
    """Lists all versions of a file."""
    versions = get_file_versions(file_path)
    return {"success": True, "versions": versions}

async def file_diff_restore(file_path: str, version_number: int) -> Dict[str, Any]:
    """Restores a file to a specific version."""
    try:
        result = restore_file_version(file_path, version_number)
        return result
    except ValueError as e:
        return {"success": False, "error": str(e)}
