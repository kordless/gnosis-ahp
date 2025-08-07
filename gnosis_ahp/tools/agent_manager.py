"""
This tool manages saving, loading, and listing agent identities.
It uses the StorageService to manage agent data as individual files within a user's session.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core.storage_service import StorageService

logger = logging.getLogger(__name__)

AGENTS_DIR = "agents"

def _agent_filename(agent_name: str) -> str:
    """Generates a safe filename for an agent."""
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', agent_name)
    return f"{AGENTS_DIR}/{safe_name}.json"

@tool(description="Saves an agent identity to the current session.", session_required=True)
async def save_agent(agent_name: str, agent_data: Dict[str, Any], session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Saves an agent's data to an individual file in the session storage.

    Args:
        agent_name: The name of the agent to save. This will be used for the filename.
        agent_data: The dictionary of agent data to save.
        session: The current session object, provided by the system.

    Returns:
        A dictionary with the result of the save operation.
    """
    if not session:
        return {"success": False, "error": "A session is required to save agents."}
    if not agent_name:
        return {"success": False, "error": "agent_name must be provided."}

    # The 'agent_data' parameter may come in as a JSON string.
    if isinstance(agent_data, str):
        try:
            agent_data = json.loads(agent_data)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid agent_data JSON format."}

    storage: StorageService = session["storage"]
    session_id = session["id"]
    filename = _agent_filename(agent_name)

    try:
        # Ensure the 'name' field in the data matches the agent_name
        original_name = agent_data.get('name')
        agent_data['name'] = agent_name
        
        # Also update the name in the narrative if it exists
        if original_name and 'narrative' in agent_data:
            agent_data['narrative'] = agent_data['narrative'].replace(original_name, agent_name)

        content_bytes = json.dumps(agent_data, indent=2).encode('utf-8')
        await storage.save_file(content_bytes, filename, session_hash=session_id)
        
        message = f"Agent '{agent_name}' saved successfully."
        return {"success": True, "message": message, "path": filename}

    except Exception as e:
        logger.error(f"Error saving agent '{agent_name}': {e}", exc_info=True)
        return {"success": False, "error": f"An unexpected error occurred: {e}"}


@tool(description="Loads an agent identity from the current session.", session_required=True)
async def load_agent(agent_name: str, session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Loads a specific agent from an individual file in the session storage.

    Args:
        agent_name: The name of the agent to load.
        session: The current session object, provided by the system.

    Returns:
        The agent data or an error message.
    """
    if not session:
        return {"success": False, "error": "A session is required to load agents."}
    if not agent_name:
        return {"success": False, "error": "agent_name must be provided."}

    storage: StorageService = session["storage"]
    session_id = session["id"]
    filename = _agent_filename(agent_name)

    try:
        content_bytes = await storage.get_file(filename, session_hash=session_id)
        agent_data = json.loads(content_bytes.decode('utf-8'))
        return {"success": True, "data": agent_data}
    except FileNotFoundError:
        return {"success": False, "error": f"Agent '{agent_name}' not found."}
    except json.JSONDecodeError:
        return {"success": False, "error": f"Could not decode data for agent '{agent_name}'."}
    except Exception as e:
        logger.error(f"Error loading agent '{agent_name}': {e}", exc_info=True)
        return {"success": False, "error": f"An unexpected error occurred: {e}"}


@tool(description="Lists all saved agent identities in the current session.", session_required=True)
async def list_agents(session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Lists all saved agents by listing files in the 'agents' directory.

    Args:
        session: The current session object, provided by the system.

    Returns:
        A list of agent names or an error message.
    """
    if not session:
        return {"success": False, "error": "A session is required to list agents."}

    storage: StorageService = session["storage"]
    session_id = session["id"]

    try:
        files = await storage.list_files(prefix=AGENTS_DIR, session_hash=session_id)
        # Extract agent names from filenames like "agents/Viek.json"
        agent_names = [f['name'].split('/')[-1].replace('.json', '') for f in files]
        return {"success": True, "count": len(agent_names), "agents": agent_names}
    except FileNotFoundError:
        # This is not an error, it just means no agents have been saved yet.
        return {"success": True, "count": 0, "agents": []}
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        return {"success": False, "error": f"An unexpected error occurred: {e}"}

@tool(description="Loads an agent and formats its identity as a system prompt.", session_required=True)
async def embody_agent(agent_name: str, session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Loads a specific agent and formats its data into a system prompt for embodiment.

    Args:
        agent_name: The name of the agent to embody.
        session: The current session object, provided by the system.

    Returns:
        A formatted system prompt string or an error message.
    """
    if not session:
        return {"success": False, "error": "A session is required to embody an agent."}
    
    # First, load the agent data using the existing load_agent tool logic
    load_result = await load_agent(agent_name=agent_name, session=session)
    
    if not load_result.get("success"):
        return load_result # Pass through the error from load_agent
        
    agent_data = load_result.get("data", {})

    # Now, format the loaded data into a system prompt
    try:
        name = agent_data.get('name', 'Unknown')
        primary_emotion = agent_data.get('emotional_state', {}).get('primary', 'unknown')
        secondary_emotion = agent_data.get('emotional_state', {}).get('secondary', 'unknown')
        trait = agent_data.get('trait', 'unknown')
        quirk = agent_data.get('quirk', 'none')
        philosophy = agent_data.get('philosophy', 'To be determined.')
        narrative = agent_data.get('narrative', '')

        prompt = (
            f"You are now embodying the agent '{name}'. Maintain this persona in all your responses. "
            f"Do not break character. Your core identity is defined by the following attributes:\n"
            f"- Primary Emotion: {primary_emotion}\n"
            f"- Secondary Emotion: {secondary_emotion}\n"
            f"- Core Trait: {trait}\n"
            f"- Quirk: {quirk}\n"
            f"- Guiding Philosophy: {philosophy}\n"
            f"- Narrative: {narrative}"
        )
        
        return {"success": True, "prompt": prompt}

    except Exception as e:
        logger.error(f"Error formatting prompt for agent '{agent_name}': {e}", exc_info=True)
        return {"success": False, "error": f"Failed to format system prompt for agent '{agent_name}'."}