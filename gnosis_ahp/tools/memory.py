"""Tools for saving and retrieving memories."""

import json
from typing import Dict, Any

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core.storage_service import StorageService

@tool(description="Save a piece of data to a named memory.")
async def save_memory(name: str, data: str, agent_id: str) -> Dict[str, Any]:
    """
    Saves a JSON string to a named file for a specific agent.

    Args:
        name: The name of the memory to save. This will be the filename.
        data: The JSON string data to save.
        agent_id: The ID of the agent saving the memory.

    Returns:
        A confirmation dictionary.
    """
    if not name or not data or not agent_id:
        raise ValueError("'name', 'data', and 'agent_id' are required.")

    # Use the agent_id as the user context for the storage service
    storage = StorageService(user_email=agent_id)
    
    # Ensure the name is a safe filename
    safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_')).rstrip()
    filename = f"{safe_name}.json"

    # Save the data
    saved_path = await storage.save_file(content=data, filename=filename)

    return {
        "success": True,
        "message": f"Memory '{name}' saved successfully.",
        "path": saved_path
    }
