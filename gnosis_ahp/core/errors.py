"""Standardized error handling for the AHP server."""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

class AHPException(HTTPException):
    """Custom exception for AHP-specific errors."""
    def __init__(
        self, 
        status_code: int, 
        code: str, 
        message: str, 
        remedy: Optional[str] = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.remedy = remedy
        detail = {
            "error": {
                "code": self.code,
                "message": self.message,
            }
        }
        if self.remedy:
            detail["error"]["remedy"] = self.remedy
        super().__init__(status_code=self.status_code, detail=detail)

async def ahp_exception_handler(request: Request, exc: AHPException):
    """FastAPI exception handler for AHPException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail["error"]},
    )

# --- Pre-defined Exceptions ---

def invalid_token_exception():
    return AHPException(
        status_code=403,
        code="invalid_access_token",
        message="Invalid or missing pre-shared access token.",
        remedy="Ensure you are providing the correct 'token' query parameter."
    )

def missing_bearer_token_exception():
    return AHPException(
        status_code=401,
        code="missing_bearer_token",
        message="Missing 'bearer_token' query parameter.",
        remedy="Include your bearer token in the query string, e.g., '&bearer_token=...'"
    )

def invalid_bearer_token_exception(detail: str = "Invalid or expired token."):
    return AHPException(
        status_code=401,
        code="invalid_bearer_token",
        message=detail,
        remedy="Request a new token via the '?f=auth' endpoint."
    )

def missing_tool_name_exception():
    return AHPException(
        status_code=422,
        code="missing_tool_name",
        message="Missing 'name' query parameter for tool call.",
        remedy="Specify the tool to use, e.g., '&name=my_tool'."
    )

def tool_not_found_exception(tool_name: str):
    return AHPException(
        status_code=404,
        code="tool_not_found",
        message=f"Tool '{tool_name}' not found.",
    )

def tool_execution_exception(tool_name: str, error: str):
    return AHPException(
        status_code=400,
        code="tool_execution_failed",
        message=f"Tool '{tool_name}' failed to execute: {error}",
    )

def session_not_found_exception(session_id: str):
    return AHPException(
        status_code=404,
        code="session_not_found",
        message=f"Session ID '{session_id}' not found.",
        remedy="Start a new session using '?f=session_start'."
    )

def unknown_function_exception(function_name: str):
    return AHPException(
        status_code=404,
        code="unknown_function",
        message=f"Unknown function '{function_name}'.",
        remedy="Valid functions are 'home', 'openapi', 'auth', 'tool', 'session_start'."
    )

def internal_server_error_exception(error: str):
    return AHPException(
        status_code=500,
        code="internal_server_error",
        message=f"An unexpected error occurred: {error}",
    )
