"""
AHP Tools for advanced file editing, versioning, and diff application.
This tool wraps the powerful engine from diff_engine.py and uses the StorageService.
"""
import json
from typing import Dict, Any

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core import diff_engine
from gnosis_ahp.core.storage_service import StorageService

@tool(description="Apply a diff to a file to edit its content. Creates a versioned backup.", session_required=True)
async def apply_diff(file_path: str, diff_text: str, change_tag: str = None, session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Applies a diff to the specified file within the current session.
    Handles both raw text files and .json files created by save_memory.
    """
    if not session:
        return {"success": False, "error": "A session is required for file operations."}
    
    storage: StorageService = session["storage"]
    session_id = session["id"]

    # Check if the file is a JSON file from save_memory
    if file_path.endswith('.json'):
        try:
            # Read the JSON file
            json_content_bytes = await storage.get_file(file_path, session_hash=session_id)
            json_content = json.loads(json_content_bytes.decode('utf-8'))
            
            # Extract the raw data
            original_text = json_content.get("data")
            if original_text is None:
                return {"success": False, "error": "JSON file does not contain a 'data' field."}

            # Apply the diff to the raw data
            # Note: This is a simplified diff application for this specific case.
            # We'll use the core diff_engine's fuzzy matching on the extracted text.
            import re
            match = re.search(r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE', diff_text, re.DOTALL)
            if not match:
                return {"success": False, "error": "Invalid diff format"}
            
            search_block, replace_block = match.groups()
            content_to_replace = diff_engine.find_fuzzy_match(search_block, original_text)
            
            if content_to_replace is None:
                return {"success": False, "error": "Could not find a confident match for the SEARCH block in the file's data."}

            modified_text = original_text.replace(content_to_replace, replace_block)
            
            # Update the JSON structure and save it back
            json_content["data"] = modified_text
            new_json_bytes = json.dumps(json_content, indent=2).encode('utf-8')
            
            await diff_engine.create_file_backup(storage, file_path, session_id, change_tag)
            await storage.save_file(new_json_bytes, file_path, session_hash=session_id)
            
            return {"success": True, "changes_applied": True}

        except FileNotFoundError:
            return {"success": False, "error": f"File not found at {file_path}"}
        except (json.JSONDecodeError, KeyError) as e:
            return {"success": False, "error": f"Error processing JSON file: {e}"}

    else:
        # Handle raw text files using the diff_engine
        return await diff_engine.file_diff_write(
            storage=storage,
            file_path=file_path,
            diff_text=diff_text,
            change_tag=change_tag,
            session_id=session_id
        )


@tool(description="List all saved versions of a file.", session_required=True)
async def get_versions(file_path: str, session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Retrieves the version history for a specific file within the current session.
    """
    if not session:
        return {"success": False, "error": "A session is required for file operations."}
        
    storage: StorageService = session["storage"]
    
    return await diff_engine.file_diff_versions(
        storage=storage,
        file_path=file_path,
        session_id=session["id"]
    )

@tool(description="Restore a file to a specific version.", session_required=True)
async def restore_version(file_path: str, version_number: int, session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Reverts a file to a previously saved version within the current session.
    """
    if not session:
        return {"success": False, "error": "A session is required for file operations."}
        
    storage: StorageService = session["storage"]
    
    return await diff_engine.file_diff_restore(
        storage=storage,
        file_path=file_path,
        version_number=version_number,
        session_id=session["id"]
    )