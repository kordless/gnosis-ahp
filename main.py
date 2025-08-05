import os
import logging
import uuid
import json
from typing import Dict, Any, AsyncGenerator
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from gnosis_ahp.auth import validate_token_from_query
from gnosis_ahp.tools.tool_registry import get_global_registry, ToolError
from gnosis_ahp.core.storage_service import StorageService
from gnosis_ahp.core.aperture_service import get_aperture_service
from gnosis_ahp.core.middleware import ApertureMiddleware
from gnosis_ahp.core.errors import (
    AHPException,
    ahp_exception_handler,
    invalid_token_exception,
    missing_bearer_token_exception,
    missing_tool_name_exception,
    tool_not_found_exception,
    tool_execution_exception,
    session_not_found_exception,
    unknown_function_exception,
    internal_server_error_exception,
)

# --- Load Environment Variables ---
# This will load the .env file into the environment.
load_dotenv()

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
AHP_TOKEN = os.getenv("AHP_TOKEN")
PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI Hypercall Protocol (AHP) Server",
    description="A single-endpoint server for remotely invoking tools via GET requests.",
    version="1.3.0",
    docs_url=None, # Disabling docs/redoc as we have a single endpoint
    redoc_url=None,
)

app.add_exception_handler(AHPException, ahp_exception_handler)
app.add_middleware(ApertureMiddleware)


# --- Template Engine & Tool Registry ---
templates = Jinja2Templates(directory="templates")
tool_registry = get_global_registry()
aperture_service = get_aperture_service()

# --- Static File Route ---

@app.get("/robots.txt", response_class=FileResponse)
async def robots():
    return "robots.txt"

# --- Aperture Payment Endpoint ---

@app.get("/aperture/check/{invoice_id}", tags=["Aperture Payments"])
async def check_payment_status(invoice_id: str):
    """Checks the status of a Lightning invoice."""
    status = await aperture_service.check_invoice_status(invoice_id)
    return JSONResponse(status)

# --- The One and Only Endpoint ---

async def stream_tool_execution(tool_instance, params, session, tool_name, auth_info) -> AsyncGenerator[str, None]:
    """Generator function for streaming tool execution."""
    yield f"data: {json.dumps({'status': 'starting', 'tool': tool_name})}\n\n"
    
    try:


        # Add session to tool context if available
        tool_context = {}
        if session:
            tool_context["session"] = session

        async for chunk in tool_instance.execute_streaming(**params, **tool_context):
            yield f"data: {json.dumps(chunk)}\n\n"

    except Exception as e:
        logger.error(f"Error during streaming execution of tool {tool_name}: {e}", exc_info=True)
        error_message = json.dumps({"error": {"code": "tool_execution_failed", "message": str(e)}})
        yield f"data: {error_message}\n\n"

    yield f"data: {json.dumps({'status': 'finished'})}\n\n"


# --- New RESTful Endpoints ---

@app.get("/auth", tags=["AHP Core"])
async def auth_endpoint(token: str, agent_id: str = "default_agent"):
    """Provides a temporary bearer token for tool usage."""
    from gnosis_ahp.auth import generate_token
    logger.info(f"AUTH request received for agent '{agent_id}' with token: '{token}'")
    new_token = generate_token(agent_id=agent_id)
    return JSONResponse({
        "message": f"Authentication successful for agent '{agent_id}'.",
        "bearer_token": new_token,
        "instructions": f"For tool calls, include this token in the query string, e.g., '?bearer_token={new_token}'"
    })

@app.get("/openapi", tags=["AHP Core"])
@app.get("/schema", tags=["AHP Core"]) # Alias for openapi
async def openapi_endpoint():
    """Returns the machine-readable API schema."""
    return JSONResponse(app.openapi())

@app.get("/tools", tags=["AHP Core"])
async def tools_endpoint():
    """Returns the schemas of all available tools."""
    return JSONResponse(tool_registry.get_schemas())

@app.get("/human_home", response_class=HTMLResponse, tags=["AHP Core"])
async def human_home_endpoint(request: Request):
    """Shows a human-readable explanation of the server."""
    return templates.TemplateResponse("human_home.html", {"request": request})


@app.get("/")
async def handle_request(request: Request):
    """
    This single endpoint handles all requests based on the 'f' query parameter.
    - ?f=home: Shows the documentation page.
    - ?f=openapi: Returns the machine-readable API schema.
    - ?f=tools: Returns the schemas of all available tools (JSON).
    - ?f=tools_ui: Shows a human-readable list of tools.
    - ?f=auth&token={key}: Provides a temporary bearer token.
    - ?f=session_start&bearer_token={token}: Starts a new session.
    - ?f=tool&name={tool_name}&bearer_id={token}&session_id={sid}&...: Executes a tool.
    - ?f=tool&...&stream=true: Executes a tool and streams the response.
    """
    params = dict(request.query_params)
    function_name = params.pop("f", "home")

    # --- Function Dispatcher ---
    
    if function_name == "home":
        return templates.TemplateResponse("index.html", {"request": request, "base_url": str(request.base_url)})

    elif function_name == "tools_ui":
        tool_schemas = tool_registry.get_schemas()
        return templates.TemplateResponse("tools.html", {"request": request, "tools": tool_schemas})
            
    else:
        raise unknown_function_exception(function_name)


@app.get("/session/start", tags=["AHP Core"])
async def session_start_endpoint(agent_id: str = "default_agent"):
    """Starts a new session and returns a session ID."""
    storage = StorageService(user_email=agent_id)
    session_id = await storage.create_session()
    return JSONResponse({
        "message": "Session started successfully.",
        "session_id": session_id,
        "agent_id": agent_id
    })


@app.get("/{tool_name}", tags=["AHP Tools"])
async def tool_endpoint(tool_name: str, request: Request):
    """
    Dynamically handles tool execution based on the URL path.
    The tool name is derived from the path, and all query parameters
    are passed as arguments to the tool.
    
    Example:
    /generate_qr_code?data=hello&bearer_token={token}
    """
    params = dict(request.query_params)
    
    # --- Authentication ---
    bearer_token = params.pop("bearer_token", None)
    if not bearer_token:
        raise missing_bearer_token_exception()
    auth_info = validate_token_from_query(bearer_token)
    agent_id = auth_info.get("agent_id", "default_agent")

    # --- Session Handling ---
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

    # --- Streaming ---
    is_streaming = params.pop("stream", "false").lower() == "true"

    # --- Tool Context ---
    tool_context = {"agent_id": agent_id}
    if session:
        tool_context["session"] = session

    # Remove agent_id from params to avoid conflict with the one in tool_context
    params.pop("agent_id", None)

    try:
        tool_instance = tool_registry.get_tool(tool_name)

        if is_streaming:
            # Note: streaming execute needs the context passed in as well
            streaming_params = {**params, **tool_context}
            return StreamingResponse(
                stream_tool_execution(tool_instance, streaming_params, session, tool_name, auth_info),
                media_type="text/event-stream"
            )
        else:
            result = await tool_instance.execute(**params, **tool_context)

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
        raise internal_server_error_exception(str(e)) from e


# --- Server Lifecycle ---

@app.on_event("startup")
def startup_event():
    """On server startup, discover tools and set up the environment."""
    if not AHP_TOKEN:
        raise ValueError("AHP_TOKEN environment variable not set. Please create a .env file or set it directly.")

    # Discover tools from the 'tools' directory
    tools_path = os.path.join(os.path.dirname(__file__), "gnosis_ahp", "tools")
    logger.info(f"Discovering tools from: {tools_path}")
    tool_registry.discover_tools(tools_path)
    logger.info(f"Discovered tools: {list(tool_registry.tools.keys())}")

if __name__ == "__main__":
    import uvicorn
    # Note: ngrok is removed from here as it's better handled by the deploy script or a separate process
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
