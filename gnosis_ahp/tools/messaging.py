"""Messaging tools for agent-to-agent communication."""

import logging
from typing import Dict, Any, List, Optional

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core.storage_service import StorageService

logger = logging.getLogger(__name__)

@tool(description="Send a message to another agent's session-based inbox.")
async def send_message(
    to_agent: str,
    subject: str,
    body: str,
    session: Dict[str, Any],
    from_agent: Optional[str] = "system",
    priority: str = "normal"
) -> Dict[str, Any]:
    """
    Send a message to another agent using the session storage service.
    
    Args:
        to_agent: The recipient agent's ID.
        subject: Message subject.
        body: Message body.
        session: The current session object, provided by the system.
        from_agent: Sender agent ID (can be auto-filled in agent context).
        priority: Message priority (low, normal, high, urgent).
    
    Returns:
        Message confirmation with ID.
    """
    logger.info(f"MESSAGE from '{from_agent}' to '{to_agent}': {subject}")
    
    # Use the recipient's ID to create a dedicated storage service for their inbox
    recipient_storage = StorageService(user_email=to_agent)
    
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
    
    # Use a consistent session hash for the inbox to ensure all messages land in the same "place"
    inbox_session_hash = recipient_storage._compute_user_hash("inbox")
    
    await recipient_storage.save_file(
        content=json.dumps(message, indent=2),
        filename=f"{message['id']}.json",
        session_hash=inbox_session_hash
    )
    
    return {
        "success": True,
        "message_id": message['id'],
        "delivered_to": to_agent,
    }

@tool(description="Check your inbox for new messages.")
async def check_inbox(
    agent_id: str,
    session: Dict[str, Any],
    unread_only: bool = True,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Check inbox for messages using the session storage service.
    
    Args:
        agent_id: Agent ID to check inbox for.
        session: The current session object, provided by the system.
        unread_only: Only show unread messages.
        limit: Maximum number of messages to return.
    
    Returns:
        List of messages.
    """
    if not agent_id:
        raise ValueError("agent_id must be provided")
    
    storage: StorageService = session["storage"]
    inbox_session_hash = storage._compute_user_hash("inbox")

    try:
        message_files = await storage.list_files(session_hash=inbox_session_hash)
    except FileNotFoundError:
        return [] # Inbox doesn't exist yet

    messages = []
    # Sort files by name (which includes the timestamp)
    message_files.sort(key=lambda x: x['name'], reverse=True)

    for file_info in message_files:
        content = await storage.get_file(file_info['name'], session_hash=inbox_session_hash)
        message = json.loads(content)
        
        if unread_only and message.get('read', False):
            continue
            
        messages.append(message)
        
        if len(messages) >= limit:
            break
            
    return messages
