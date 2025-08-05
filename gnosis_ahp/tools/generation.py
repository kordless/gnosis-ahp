"""Tools for generating content, like QR codes."""

import qrcode
import io
import base64
from typing import Dict, Any

from gnosis_ahp.tools.base import tool

@tool(description="Generate a QR code from text data.")
async def generate_qr_code(data: str) -> Dict[str, Any]:
    """
    Generates a QR code containing the provided data.

    Args:
        data: The text or URL to encode in the QR code.

    Returns:
        A dictionary containing the base64-encoded PNG image of the QR code.
    """
    if not data:
        raise ValueError("Data to be encoded must be provided.")

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
        "message": f"Successfully generated QR code for: {data}"
    }
