"""
FastAPI Middleware for Project Aperture and Content-Type enforcement.
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from gnosis_ahp.tools.tool_registry import get_global_registry
from gnosis_ahp.core.aperture_service import get_aperture_service

class ContentTypeMiddleware(BaseHTTPMiddleware):
    """
    Ensures that every response has a Content-Type header.
    Defaults to application/json if no other content type is set.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if "content-type" not in response.headers:
            response.headers["Content-Type"] = "application/json"
        return response

class ApertureMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.tool_registry = get_global_registry()
        self.aperture_service = get_aperture_service()

    async def dispatch(self, request: Request, call_next):
        # Only apply to tool execution paths
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) == 1 and path_parts[0] not in self.tool_registry.RESERVED_NAMES:
            tool_name = path_parts[0]
            
            try:
                tool_instance = self.tool_registry.get_tool(tool_name)
                
                if tool_instance and tool_instance.cost > 0:
                    # This is a premium tool, check for payment
                    params = dict(request.query_params)
                    invoice_id = params.get("invoice_id")

                    if not invoice_id:
                        # No invoice provided, generate one and return 402
                        invoice = await self.aperture_service.create_invoice(
                            amount_sats=tool_instance.cost,
                            memo=f"Payment for tool: {tool_name}"
                        )
                        return JSONResponse(
                            status_code=402,
                            content={
                                "error": "payment_required",
                                "message": "This tool requires a Lightning payment to proceed.",
                                "details": invoice
                            }
                        )
                    
                    # Invoice ID provided, check its status
                    status_result = await self.aperture_service.check_invoice_status(invoice_id)
                    if status_result.get("status") != "paid":
                        return JSONResponse(
                            status_code=402,
                            content={
                                "error": "payment_pending",
                                "message": "The provided invoice has not been paid.",
                                "invoice_id": invoice_id
                            }
                        )
                    
                    # Payment is valid, proceed to the tool
                    
            except Exception:
                # Tool not found, let the normal error handling take over
                pass

        response = await call_next(request)
        return response