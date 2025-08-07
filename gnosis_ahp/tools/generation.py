"""Tools for generating content, like QR codes."""

import qrcode
import io
import base64
from typing import Dict, Any

from gnosis_ahp.tools.base import tool

@tool(description="Generate a QR code. Free for short text, costs 100 satoshis for text over 128 characters.")
async def longer_qr_code(data: str) -> Dict[str, Any]:
    """
    Generates a QR code. Short text is free, longer text incurs a cost.

    Args:
        data: The text or URL to encode in the QR code.

    Returns:
        A dictionary containing the base64-encoded PNG image of the QR code.
    """
    if not data:
        raise ValueError("Data to be encoded must be provided.")

    # Dynamic cost based on data length
    cost = 100 if len(data) > 128 else 0
    
    # In a real implementation, the cost would be handled by the ApertureMiddleware.
    # For now, we will just log it.
    if cost > 0:
        print(f"This QR code would cost {cost} satoshis.")

    # Generate the QR code image
    img = qrcode.make(data)
    
    # Save image to a memory buffer
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    
    # Encode the image in base64
    base64_image = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return {
        "success": True,
        "image_format": "png",
        "image_base64": base64_image,
        "cost": cost,
        "message": f"Successfully generated QR code for: {data}"
    }
