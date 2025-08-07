"""
This tool generates an agent identity based on I Ching hexagram divination and emotional attributes.
By default, it automatically saves the new agent to the session.
"""

import random
import logging
from typing import Dict, Any, Optional

from gnosis_ahp.tools.base import tool
from gnosis_ahp.tools.agent_manager import save_agent

logger = logging.getLogger(__name__)

#<editor-fold desc="I-Ching Data">
# ... (I-Ching data remains the same)
#</editor-fold>

#<editor-fold desc="Helper Functions">
# ... (Helper functions remain the same)
#</editor-fold>

@tool(description="Generates and automatically saves a new agent identity.", session_required=True)
async def generate_agent(save: bool = True, seed: int = None, session: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generates an agent identity and saves it to the session by default.

    Args:
        save: If True, the agent is automatically saved. If False, it is only generated.
        seed: Optional seed for the random generator for reproducible results.
        session: The current session object, provided by the system.

    Returns:
        A dictionary containing the generated agent's attributes.
    """
    if save and not session:
        return {"success": False, "error": "A session is required to save the generated agent."}

    if seed:
        random.seed(seed)
        logger.info(f"Using seed: {seed}")

    try:
        hexagram_casting = cast_hexagram()
        hexagram_details = get_hexagram_details(hexagram_casting)
        agent_name = generate_agent_name()
        primary_emotion = random.choice(EMOTIONS)
        secondary_emotion = random.choice(EMOTIONS)
        trait = random.choice(TRAITS)
        quirk = random.choice(QUIRKS)
        narrative = generate_narrative(primary_emotion, secondary_emotion, agent_name, trait)

        agent = {
            "name": agent_name,
            "emotional_state": {"primary": primary_emotion, "secondary": secondary_emotion},
            "trait": trait,
            "quirk": quirk,
            "hexagram": {
                "current": hexagram_details["primary"]["name"],
                "meaning": hexagram_details["primary"]["meaning"],
                "becoming": hexagram_details["transformed"]["name"] if hexagram_details["transformed"] else None,
                "changing_lines": hexagram_details["changing_lines"]
            },
            "philosophy": hexagram_details["philosophy"],
            "narrative": narrative,
        }

        if save:
            logger.info(f"Auto-saving newly generated agent: {agent_name}")
            save_result = await save_agent(agent_name=agent_name, agent_data=agent, session=session)
            if not save_result.get("success"):
                # If saving fails, return the error but still include the generated agent data
                agent["save_error"] = save_result.get("error")
                return agent

        logger.info(f"Successfully generated I Ching agent: {agent_name}")
        return agent

    except Exception as e:
        logger.error(f"Agent generation failed: {e}", exc_info=True)
        return {"success": False, "error": f"Agent generation failed: {e}"}