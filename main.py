import os
import logging
import uuid
import json
import hmac
from typing import Dict, Any, AsyncGenerator
from dotenv import load_dotenv

from fastapi import FastAPI, Request, APIRouter, Depends, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from gnosis_ahp.auth import validate_token_from_query, generate_token
from gnosis_ahp.tools.tool_registry import get_global_registry, ToolError
from gnosis_ahp.core.storage_service import StorageService
from gnosis_ahp.core.aperture_service import get_aperture_service
from gnosis_ahp.core.middleware import ApertureMiddleware, ContentTypeMiddleware
from gnosis_ahp.core.errors import (
    AHPException,
    ahp_exception_handler,
    invalid_token_exception,
    missing_bearer_token_exception,
    unknown_function_exception,
    tool_not_found_exception,
    session_not_found_exception,
    tool_execution_exception,
    internal_server_error_exception,
)

# --- Load Environment Variables ---
load_dotenv()

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
AHP_TOKEN = os.getenv("AHP_TOKEN", "").strip('\'"')

PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

# --- Auth Dependency ---
async def verify_token(request: Request) -> Dict[str, Any]:
    """A dependency to verify the bearer token for protected routes."""
    bearer_token = request.query_params.get("bearer_token")
    if not bearer_token:
        raise missing_bearer_token_exception()
    
    auth_info = validate_token_from_query(bearer_token, secret_key=AHP_TOKEN)
    return auth_info

# --- FastAPI App & Routers ---
app = FastAPI(
    title="AI Hypercall Protocol (AHP) Server",
    description="A single-endpoint server for remotely invoking tools via GET requests.",
    version="1.3.0",
    docs_url=None,
    redoc_url=None,
)

# This router is for the auth endpoint and does not have dependencies
# auth_router = APIRouter()

# This router is for protected API endpoints that require a bearer token
api_router = APIRouter(dependencies=[Depends(verify_token)])

# This router is for the main application and UI
ui_router = APIRouter()

app.add_exception_handler(AHPException, ahp_exception_handler)
app.add_middleware(ContentTypeMiddleware)
app.add_middleware(ApertureMiddleware)
app.mount("/static", StaticFiles(directory="."), name="static")

# --- Template Engine & Tool Registry ---
templates = Jinja2Templates(directory="templates")
tool_registry = get_global_registry()
aperture_service = get_aperture_service()

# --- Streaming Helper ---
async def stream_tool_execution(tool_instance, params, session, tool_name, auth_info) -> AsyncGenerator[str, None]:
    """Generator function for streaming tool execution."""
    yield f"data: {json.dumps({'status': 'starting', 'tool': tool_name})}\n\n"
    
    try:
        tool_context = {"agent_id": auth_info.get("agent_id", "default_agent")}
        if session:
            tool_context["session"] = session

        async for chunk in tool_instance.execute_streaming(**params, **tool_context):
            yield f"data: {json.dumps(chunk)}\n\n"

    except Exception as e:
        logger.error(f"Error during streaming execution of tool {tool_name}: {e}", exc_info=True)
        error_message = json.dumps({"error": {"code": "tool_execution_failed", "message": str(e)}})
        yield f"data: {error_message}\n\n"

    yield f"data: {json.dumps({'status': 'finished'})}\n\n"




# --- UI and Public Endpoints ---

@ui_router.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=404)

@ui_router.get("/client", response_class=FileResponse)
async def get_client_proxy():
    """Serves the ahp_proxy.py script as a reference client implementation."""
    return "ahp_proxy.py"

@ui_router.get("/robots.txt", response_class=FileResponse)
async def robots():
    return "robots.txt"

@ui_router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("logo.png")

@ui_router.get("/aperture/check/{invoice_id}", tags=["Aperture Payments"])
async def check_payment_status(invoice_id: str):
    """Checks the status of a Lightning invoice."""
    status = await aperture_service.check_invoice_status(invoice_id)
    return JSONResponse(status)

@ui_router.get("/auth", tags=["AHP Core"])
async def auth_endpoint(token: str, agent_id: str = "default_agent"):
    """Provides a temporary bearer token for tool usage."""
    if not token or not hmac.compare_digest(token, AHP_TOKEN):
        logger.error(f"Authentication failed. Received token: '{token}', Expected AHP_TOKEN: '{AHP_TOKEN}'")
        raise invalid_token_exception("Invalid authentication token provided.")
        
    logger.info(f"AUTH request received for agent '{agent_id}' with token: '{token}'")
    new_token = generate_token(agent_id=agent_id, secret_key=AHP_TOKEN)
    return JSONResponse({
        "message": f"Authentication successful for agent '{agent_id}'.",
        "bearer_token": new_token,
        "instructions": f"For tool calls, include this token in the query string, e.g., '?bearer_token={new_token}'"
    })

@ui_router.get("/openapi", tags=["AHP Core"])
@ui_router.get("/schema", tags=["AHP Core"]) # Alias for openapi
async def openapi_endpoint():
    """
    Returns the machine-readable API schema, injecting custom AHP metadata.
    """
    if app.openapi_schema:
        return JSONResponse(app.openapi_schema)

    openapi_schema = app.openapi()
    
    # Inject custom 'x-ahp-session-required' field for each tool
    tool_schemas = tool_registry.get_schemas()
    tool_session_map = {tool['name']: tool.get('x-ahp-session-required', False) for tool in tool_schemas}

    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            # Tool endpoints are dynamic, so we check the tag
            if "AHP Tools" in operation.get("tags", []):
                # The tool name is the last part of the path
                tool_name = path.split("/")[-1]
                if tool_name in tool_session_map:
                    operation["x-ahp-session-required"] = tool_session_map[tool_name]

    app.openapi_schema = openapi_schema
    return JSONResponse(app.openapi_schema)

@ui_router.get("/tools", tags=["AHP Core"])
def tools_endpoint():
    """Returns the schemas of all available tools."""
    return JSONResponse(tool_registry.get_schemas())

@ui_router.get("/human_home", response_class=HTMLResponse, tags=["AHP Core"])
def human_home_endpoint(request: Request):
    """Shows a human-readable explanation of the server."""
    return templates.TemplateResponse("human_home.html", {"request": request})

@ui_router.get("/file_editor", response_class=HTMLResponse, tags=["AHP UI"])
def file_editor_endpoint(request: Request):
    """Renders the File Editor UI."""
    return templates.TemplateResponse("file_editor.html", {"request": request})

@ui_router.get("/tools_ui", response_class=HTMLResponse, tags=["AHP UI"])
def tools_ui_endpoint(request: Request):
    """Renders the human-readable tool library."""
    tool_schemas = tool_registry.get_schemas()
    return templates.TemplateResponse("tools.html", {"request": request, "tools": tool_schemas})

@ui_router.get("/")
def handle_legacy_request(request: Request):
    """
    This endpoint handles legacy `?f=` style requests for backward compatibility.
    It only supports `?f=home` and `?f=tools_ui`.
    """
    function_name = request.query_params.get("f", "home")
    logger.info(f"Handling legacy `?f=` request for function: {function_name}")

    if function_name == "home":
        return templates.TemplateResponse("index.html", {"request": request, "base_url": str(request.base_url)})
    elif function_name == "tools_ui":
        tool_schemas = tool_registry.get_schemas()
        return templates.TemplateResponse("tools.html", {"request": request, "tools": tool_schemas})
    else:
        logger.error(f"Unknown legacy function requested: {function_name}")
        raise unknown_function_exception(function_name)

@api_router.get("/session/start", tags=["AHP Core"])
async def session_start_endpoint(auth_info: Dict[str, Any] = Depends(verify_token)):
    """Starts a new session and returns a session ID."""
    agent_id = auth_info.get("agent_id", "default_agent")
    storage = StorageService(user_email=agent_id)
    session_id = await storage.create_session()
    return JSONResponse({
        "message": "Session started successfully.",
        "session_id": session_id,
        "agent_id": agent_id
    })

@api_router.get("/{tool_name}", tags=["AHP Tools"])
async def tool_endpoint(tool_name: str, request: Request, auth_info: Dict[str, Any] = Depends(verify_token)):
    """
    Dynamically handles tool execution based on the URL path.
    """
    logger.info(f"Tool endpoint called for tool: '{tool_name}'")
    logger.info(f"Available tools: {list(tool_registry.tools.keys())}")
    
    params = dict(request.query_params)
    params.pop("bearer_token", None)

    agent_id = auth_info.get("agent_id", "default_agent")
    logger.info(f"Authenticated agent: '{agent_id}'")

    session_id = params.pop("session_id", None)
    session = None
    if session_id:
        storage = StorageService(user_email=agent_id)
        if not await storage.validate_session(session_id):
            raise session_not_found_exception(session_id)
        session = {
            "id": session_id,
            "storage": storage
        }

    is_streaming = params.pop("stream", "false").lower() == "true"

    tool_context = {"agent_id": agent_id}
    if session:
        tool_context["session"] = session

    params.pop("agent_id", None)

    try:
        tool_instance = tool_registry.get_tool(tool_name)

        if is_streaming:
            streaming_params = {**params, **tool_context}
            return StreamingResponse(
                stream_tool_execution(tool_instance, streaming_params, session, tool_name, auth_info),
                media_type="text/event-stream"
            )
        else:
            result = await tool_instance.execute(**params, **tool_context)
            logger.info(f"Tool execution result: {result}")
            if not result.success:
                raise tool_execution_exception(tool_name, result.error)

            return JSONResponse({
                "tool": tool_name,
                "result": result.data,
                "session_id": session_id
            })

    except ToolError as e:
        raise tool_not_found_exception(tool_name) from e
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
        raise internal_server_error_exception(str(e))

# Include the routers in the main app
logger.info("Including UI router.")
app.include_router(ui_router)
logger.info("Including protected API router.")
app.include_router(api_router)

# --- Server Lifecycle ---
@app.on_event("startup")
def startup_event():
    """On server startup, discover tools and set up the environment."""
    logger.info(f"AHP_ENVIRONMENT is set to: {os.getenv('AHP_ENVIRONMENT')}")
    if not AHP_TOKEN:
        raise ValueError("AHP_TOKEN environment variable not set. Please create a .env file or set it directly.")

    tools_path = os.path.join(os.path.dirname(__file__), "gnosis_ahp", "tools")
    logger.info(f"Discovering tools from: {tools_path}")
    tool_registry.discover_tools(tools_path)
    logger.info(f"Discovered tools: {list(tool_registry.tools.keys())}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)