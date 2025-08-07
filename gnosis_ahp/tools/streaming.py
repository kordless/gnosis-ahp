"""
Tools that demonstrate streaming capabilities.
"""
import httpx
import json
from typing import Dict, Any, Optional, AsyncGenerator

from gnosis_ahp.tools.base import tool

DOCKER_API_URL = "http://host.docker.internal:5680"

@tool(description="Stream the logs of a Docker container in real-time.")
async def stream_logs(
    container_id: str,
    tail: int = 100
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Connects to the Gnosis Docker API and streams back the logs for a
    specified container.

    Args:
        container_id: The ID or name of the container to stream logs from.
        tail: The number of recent log lines to start with.

    Yields:
        A dictionary containing a chunk of the log stream.
    """
    async with httpx.AsyncClient(base_url=DOCKER_API_URL) as client:
        try:
            async with client.stream("GET", f"/api/containers/{container_id}/logs", params={"stream": "true", "tail": str(tail)}) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    # The Docker API might send multiple JSON objects in one chunk,
                    # so we need to handle that.
                    lines = chunk.decode('utf-8').splitlines()
                    for line in lines:
                        if line:
                            try:
                                # Each line should be a JSON object
                                log_entry = json.loads(line)
                                yield {"type": "log_chunk", "data": log_entry}
                            except json.JSONDecodeError:
                                # If it's not JSON, send it as raw text
                                yield {"type": "raw_chunk", "data": line}
        except httpx.HTTPStatusError as e:
            yield {"type": "error", "data": f"API Error: {e.response.text}"}
        except Exception as e:
            yield {"type": "error", "data": f"Client Error: {str(e)}"}

