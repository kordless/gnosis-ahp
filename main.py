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

# --- In-Memory Session Storage ---
# A simple dictionary to hold session data.
# In a production environment, this should be replaced with a more robust solution like Redis.
sessions: Dict[str, Dict[str, Any]] = {}

# --- FastAPI App Initialization ---
app = FastAPI(
    title="AI Hypercall Protocol (AHP) Server",
    description="A single-endpoint server for remotely invoking tools via GET requests.",
    version="1.3.0",
    docs_url=None, # Disabling docs/redoc as we have a single endpoint
    redoc_url=None,
)

app.add_exception_handler(AHPException, ahp_exception_handler)


# --- Template Engine & Tool Registry ---
templates = Jinja2Templates(directory="templates")
tool_registry = get_global_registry()

# --- Static File Route ---

@app.get("/robots.txt", response_class=FileResponse)
async def robots():
    return "robots.txt"

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
            if chunk.get("type") == "final":
                # If in a session, store the interaction
                if session:
                    session["history"].append({
                        "tool_name": tool_name,
                        "params": params,
                        "result": chunk.get("data")
                    })

    except Exception as e:
        logger.error(f"Error during streaming execution of tool {tool_name}: {e}", exc_info=True)
        error_message = json.dumps({"error": {"code": "tool_execution_failed", "message": str(e)}})
        yield f"data: {error_message}\n\n"

    yield f"data: {json.dumps({'status': 'finished'})}\n\n"


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

    elif function_name == "openapi":
        # Manually return the openapi schema, as the auto-docs are disabled
        return JSONResponse(app.openapi())

    elif function_name == "tools":
        return JSONResponse(tool_registry.get_schemas())

    elif function_name == "tools_ui":
        tool_schemas = tool_registry.get_schemas()
        return templates.TemplateResponse("tools.html", {"request": request, "tools": tool_schemas})

    elif function_name == "human_home":
        return templates.TemplateResponse("human_home.html", {"request": request})

    elif function_name == "auth":
        from gnosis_ahp.auth import generate_token # Local import to avoid circularity issues
        
        # For testing: accept any provided token and log it.
        provided_token = params.get("token")
        logger.info(f"AUTH request received with token: '{provided_token}'")
        
        new_token = generate_token()
        return JSONResponse({
            "message": "Authentication successful (development mode).",
            "bearer_token": new_token,
            "instructions": f"For tool calls, include this token in the query string, e.g., '&bearer_token={new_token}'"
        })


    elif function_name == "session_start":
        bearer_token = params.pop("bearer_token", None)
        if not bearer_token:
            raise missing_bearer_token_exception()
        
        validate_token_from_query(bearer_token) # Validate token, but we don't need the info for this call
        
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"history": []}
        logger.info(f"Started new session: {session_id}")
        
        return JSONResponse({
            "message": "Session started successfully.",
            "session_id": session_id,
        })

    elif function_name == "tool":
        bearer_token = params.pop("bearer_token", None)
        if not bearer_token:
            raise missing_bearer_token_exception()
        
        # Validate the token
        auth_info = validate_token_from_query(bearer_token)

        # Handle session
        session_id = params.pop("session_id", None)
        session = None
        if session_id:
            if session_id not in sessions:
                raise session_not_found_exception(session_id)
            session = sessions[session_id]

        tool_name = params.pop("name", None)
        if not tool_name:
            raise missing_tool_name_exception()
            
        # Check for streaming request
        is_streaming = params.pop("stream", "false").lower() == "true"

        try:
            tool_instance = tool_registry.get_tool(tool_name)

            if is_streaming:
                return StreamingResponse(
                    stream_tool_execution(tool_instance, params, session, tool_name, auth_info),
                    media_type="text/event-stream"
                )
            else:
                # Add session and auth info to tool context
            tool_context = {"agent_id": auth_info["agent_id"]}
            if session:
                tool_context["session"] = session

            # The remaining params are the arguments for the tool
            result = await tool_instance.execute(**params, **tool_context)

                if not result.success:
                    raise tool_execution_exception(tool_name, result.error)

                # If in a session, store the interaction
                if session:
                    session["history"].append({
                        "tool_name": tool_name,
                        "params": params,
                        "result": result.data
                    })

                return JSONResponse({
                    "tool": tool_name, 
                    "result": result.data, 
                    "invoked_by": auth_info["agent_id"],
                    "session_id": session_id
                })

        except ToolError as e:
            # ToolError from get_tool maps to tool_not_found
            raise tool_not_found_exception(tool_name) from e
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            raise internal_server_error_exception(str(e)) from e
            
    else:
        raise unknown_function_exception(function_name)


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
