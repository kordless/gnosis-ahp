"""
This tool generates a new, blank agent identity.
"""

import random
import logging
from typing import Dict, Any

from gnosis_ahp.tools.base import tool
from gnosis_ahp.tools.agent_manager import save_agent

logger = logging.getLogger(__name__)

@tool(description="Generates a new, blank agent identity and saves it to the session.", session_required=True)
async def generate_agent(agent_name: str, save: bool = True, session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generates a new, blank agent identity.

    Args:
        agent_name: The name for the new agent.
        save: If True, the agent is automatically saved.
        session: The current session object, provided by the system.

    Returns:
        A dictionary containing the new agent's basic data.
    """
    if save and not session:
        return {"success": False, "error": "A session is required to save the generated agent."}

    agent_data = {
        "name": agent_name,
        "memories": [],
        "traits": [],
        "philosophy": "To be discovered."
    }

    if save:
        save_result = await save_agent(agent_name=agent_name, agent_data=agent_data, session=session)
        if not save_result.get("success"):
            agent_data["save_error"] = save_result.get("error")

    return agent_data