"""
AHP Tool for interacting with the Gnosis Docker API.
"""
import httpx
from typing import Dict, Any, Optional

from gnosis_ahp.tools.base import tool

DOCKER_API_URL = "http://localhost:5680"

@tool(description="Interact with the Gnosis Docker API to manage containers and images.")
async def docker_api(
    command: str,
    container_id: Optional[str] = None,
    image: Optional[str] = None,
    tag: Optional[str] = "latest",
    force: bool = False,
    all: bool = False,
    tail: int = 100,
    # Add other parameters from the MCP tool as needed
) -> Dict[str, Any]:
    """
    A single tool to interact with the Gnosis Docker API.

    Args:
        command: The command to execute (e.g., 'ps', 'start', 'stop', 'logs').
        container_id: The ID or name of the container for relevant commands.
        image: The name of the image for relevant commands.
        tag: The tag of the image.
        force: Force the operation.
        all: Show all containers.
        tail: Number of log lines to show.

    Returns:
        The JSON response from the Gnosis Docker API.
    """
    async with httpx.AsyncClient(base_url=DOCKER_API_URL) as client:
        try:
            if command == "ps":
                params = {"all": str(all).lower()}
                response = await client.get("/api/containers", params=params)
            elif command == "start" and container_id:
                response = await client.post(f"/api/containers/{container_id}/start")
            elif command == "stop" and container_id:
                response = await client.post(f"/api/containers/{container_id}/stop")
            elif command == "restart" and container_id:
                response = await client.post(f"/api/containers/{container_id}/restart")
            elif command == "rm" and container_id:
                params = {"force": str(force).lower()}
                response = await client.delete(f"/api/containers/{container_id}", params=params)
            elif command == "logs" and container_id:
                params = {"tail": str(tail)}
                response = await client.get(f"/api/containers/{container_id}/logs", params=params)
            elif command == "stats" and container_id:
                response = await client.get(f"/api/containers/{container_id}/stats")
            elif command == "images":
                response = await client.get("/api/images")
            elif command == "pull" and image:
                response = await client.post("/api/images/pull", json={"image": image, "tag": tag})
            elif command == "rmi" and image:
                params = {"force": str(force).lower()}
                response = await client.delete(f"/api/images/{image}", params=params)
            elif command == "health":
                response = await client.get("/health")
            else:
                raise ValueError(f"Unsupported command: {command}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            return {"error": "api_error", "status_code": e.response.status_code, "detail": e.response.text}
        except Exception as e:
            return {"error": "client_error", "detail": str(e)}
