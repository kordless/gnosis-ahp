"""Messaging tools for agent-to-agent communication."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from pathlib import Path

from gnosis_ahp.tools.base import tool

logger = logging.getLogger(__name__)

# Message storage - in a real app, this should be a proper database.
MESSAGE_STORE = Path.home() / ".gnosis-ahp" / "messages"
MESSAGE_STORE.mkdir(parents=True, exist_ok=True)


@tool(description="Send a message to another agent")
async def send_message(
    to_agent: str,
    subject: str,
    body: str,
    from_agent: Optional[str] = "system",
    priority: str = "normal"
) -> Dict[str, Any]:
    """
    Send a message to another agent.
    
    Args:
        to_agent: The recipient agent's ID.
        subject: Message subject.
        body: Message body.
        from_agent: Sender agent ID (can be auto-filled in agent context).
        priority: Message priority (low, normal, high, urgent).
    
    Returns:
        Message confirmation with ID.
    """
    logger.info(f"MESSAGE from '{from_agent}' to '{to_agent}': {subject}")
    message = {
        "id": f"msg_{datetime.now().timestamp()}",
        "from": from_agent,
        "to": to_agent,
        "subject": subject,
        "body": body,
        "priority": priority,
        "timestamp": datetime.now().isoformat(),
        "read": False
    }
    
    # Store in recipient's inbox
    inbox_dir = MESSAGE_STORE / to_agent / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    
    message_file = inbox_dir / f"{message['id']}.json"
    with open(message_file, 'w') as f:
        json.dump(message, f, indent=2)
    
    return {
        "success": True,
        "message_id": message['id'],
        "delivered_to": to_agent,
    }


@tool(description="Check your inbox for new messages")
async def check_inbox(
    agent_id: str,
    unread_only: bool = True,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Check inbox for messages.
    
    Args:
        agent_id: Agent ID to check inbox for.
        unread_only: Only show unread messages.
        limit: Maximum number of messages to return.
    
    Returns:
        List of messages.
    """
    if not agent_id:
        raise ValueError("agent_id must be provided")
    
    inbox_dir = MESSAGE_STORE / agent_id / "inbox"
    logger.info(f"Checking inbox for agent '{agent_id}' at: {inbox_dir}")
    if not inbox_dir.exists():
        return []
    
    messages = []
    # Get all message files, sorted by timestamp (newest first)
    message_files = sorted(inbox_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    for message_file in message_files:
        with open(message_file, 'r') as f:
            message = json.load(f)
        
        if unread_only and message.get('read', False):
            continue
        
        messages.append(message)
        
        if len(messages) >= limit:
            break
    
    return messages
