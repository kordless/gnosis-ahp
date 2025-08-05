import httpx
from typing import Optional, Dict, Any

from .config import get_config_value, set_config_value

class AHPClient:
    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or get_config_value("server_url")
        if not self.server_url:
            raise ValueError("AHP server URL not configured. Please run 'geminicli configure --server-url <url>'.")
        
        self.http_client = httpx.Client(base_url=self.server_url)
        self.bearer_token = get_config_value("bearer_token")

    def _get_bearer_token(self):
        """Authenticates with the server to get a new bearer token."""
        ahp_token = get_config_value("ahp_token")
        if not ahp_token:
            raise ValueError("AHP pre-shared key not configured. Please run 'geminicli configure --ahp-token <token>'.")

        response = self.http_client.get(f"/?f=auth&token={ahp_token}")
        response.raise_for_status()
        data = response.json()
        self.bearer_token = data["bearer_token"]
        set_config_value("bearer_token", self.bearer_token)
        return self.bearer_token

    def _make_request(self, params: Dict[str, Any]) -> httpx.Response:
        """Makes a request to the server, handling authentication."""
        if not self.bearer_token:
            self._get_bearer_token()

        params["bearer_token"] = self.bearer_token
        response = self.http_client.get("/", params=params)

        if response.status_code == 401: # Token expired or invalid
            self._get_bearer_token()
            params["bearer_token"] = self.bearer_token
            response = self.http_client.get("/", params=params)
        
        response.raise_for_status()
        return response

    def get_openapi_spec(self) -> Dict[str, Any]:
        """Gets the OpenAPI specification from the server."""
        response = self.http_client.get("/?f=openapi")
        response.raise_for_status()
        return response.json()

    def get_tools(self) -> Dict[str, Any]:
        """Gets the available tools and their schemas from the server."""
        response = self.http_client.get("/?f=tools")
        response.raise_for_status()
        return response.json()

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Executes a tool on the server."""
        params = {"f": "tool", "name": tool_name, **kwargs}
        response = self._make_request(params)
        return response.json()
