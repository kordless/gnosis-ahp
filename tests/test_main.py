import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import os

# Set a dummy token for testing purposes before importing the app
os.environ["AHP_TOKEN"] = "test_pre_shared_key"

from main import app

@pytest.fixture
def client():
    """A test client for the app."""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """An async test client for the app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

# ==================================
# Test Cases
# ==================================

def test_home(client):
    """Test the home page."""
    response = client.get("/?f=home")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AHP Server" in response.text

def test_openapi_spec(client):
    """Test the OpenAPI spec endpoint."""
    response = client.get("/?f=openapi")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert data["info"]["title"] == "AI Hypercall Protocol (AHP) Server"
    assert "paths" in data

def test_robots_txt(client):
    """Test the robots.txt endpoint."""
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "User-agent: *" in response.text

def test_unknown_function(client):
    """Test that an unknown function returns a 404 error."""
    response = client.get("/?f=nonexistent")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "unknown_function"
    assert "Unknown function 'nonexistent'" in error["message"]

# --- Auth Tests ---

def test_auth_success(client):
    """Test successful authentication with the correct pre-shared key."""
    response = client.get("/?f=auth&token=test_pre_shared_key")
    assert response.status_code == 200
    data = response.json()
    assert "bearer_token" in data
    assert data["message"] == "Authentication successful."

def test_auth_missing_token(client):
    """Test auth failure when the pre-shared key is missing."""
    response = client.get("/?f=auth")
    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "invalid_access_token"
    assert "Invalid or missing pre-shared access token" in error["message"]

def test_auth_invalid_token(client):
    """Test auth failure when the pre-shared key is incorrect."""
    response = client.get("/?f=auth&token=wrong_key")
    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "invalid_access_token"
    assert "Invalid or missing pre-shared access token" in error["message"]

# --- Tool Call Tests ---

@pytest.mark.asyncio
async def async_test_tool_call_missing_bearer_token(async_client: AsyncClient):
    """Test tool call failure when the bearer token is missing."""
    response = await async_client.get("/?f=tool&name=some_tool")
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "missing_bearer_token"
    assert "Missing 'bearer_token' query parameter" in error["message"]

@pytest.mark.asyncio
async def async_test_tool_call_invalid_bearer_token(async_client: AsyncClient):
    """Test tool call failure with an invalid or expired bearer token."""
    response = await async_client.get("/?f=tool&name=some_tool&bearer_token=invalid_jwt")
    assert response.status_code == 401 # Based on auth.py, this should be the code
    error = response.json()["error"]
    assert error["code"] == "invalid_bearer_token"
    assert "Invalid or missing bearer_token" in error["message"]

@pytest.mark.asyncio
async def async_test_tool_call_missing_tool_name(async_client: AsyncClient, client: TestClient):
    """Test tool call failure when the tool name is missing."""
    # First, get a valid bearer token
    auth_response = client.get("/?f=auth&token=test_pre_shared_key")
    bearer_token = auth_response.json()["bearer_token"]

    response = await async_client.get(f"/?f=tool&bearer_token={bearer_token}")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "missing_tool_name"
    assert "Missing 'name' query parameter" in error["message"]

@pytest.mark.asyncio
async def async_test_tool_not_found(async_client: AsyncClient, client: TestClient):
    """Test tool call failure when the requested tool does not exist."""
    auth_response = client.get("/?f=auth&token=test_pre_shared_key")
    bearer_token = auth_response.json()["bearer_token"]

    response = await async_client.get(f"/?f=tool&name=nonexistent_tool&bearer_token={bearer_token}")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "tool_not_found"
    assert "Tool 'nonexistent_tool' not found" in error["message"]
