"""Tools for saving and retrieving memories."""

import json
from typing import Dict, Any

import json
from typing import Dict, Any

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core.storage_service import StorageService

@tool(description="Save a piece of data to a named memory within the current session.")
async def save_memory(name: str, data: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves a JSON string to a named file within the current session.

    Args:
        name: The name of the memory to save. This will be the filename.
        data: The JSON string data to save.
        session: The current session object, provided by the system.

    Returns:
        A confirmation dictionary.
    """
    if not all([name, data, session]):
        raise ValueError("'name', 'data', and 'session' are required.")

    storage: StorageService = session["storage"]
    session_id = session["id"]
    
    safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).rstrip()
    filename = f"{safe_name}.json"

    saved_path = await storage.save_file(content=data, filename=filename, session_hash=session_id)

    return {
        "success": True,
        "message": f"Memory '{name}' saved in session {session_id}.",
        "path": saved_path
    }

@tool(description="Retrieve a piece of data from a named memory within the current session.")
async def get_memory(name: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves data from a named file within the current session.

    Args:
        name: The name of the memory to retrieve.
        session: The current session object, provided by the system.

    Returns:
        The retrieved data.
    """
    if not all([name, session]):
        raise ValueError("'name' and 'session' are required.")

    storage: StorageService = session["storage"]
    session_id = session["id"]

    safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).rstrip()
    filename = f"{safe_name}.json"

    try:
        file_content = await storage.get_file(filename=filename, session_hash=session_id)
        return json.loads(file_content)
    except FileNotFoundError:
        raise ValueError(f"Memory '{name}' not found in session {session_id}.")
    except json.JSONDecodeError:
        raise ValueError(f"Could not decode JSON from memory '{name}'.")
