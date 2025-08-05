"""
Aperture Service - Bitcoin Lightning Payment Integration
"""
import os
import uuid
from typing import Dict, Any, Optional

# In-memory store for mock invoices. In a real application, this would
# be managed by the Lightning node.
mock_invoices: Dict[str, Dict[str, Any]] = {}

class ApertureService:
    """
    Service for handling Bitcoin Lightning payments.

    This is a MOCK implementation for development purposes. It does not
    interact with a real Lightning node.
    """
    def __init__(self):
        # In a real implementation, these would be credentials for the LND node
        self.lnd_host = os.getenv("LND_HOST", "localhost")
        self.macaroon_path = os.getenv("LND_MACAROON_PATH", "")

    async def create_invoice(self, amount_sats: int, memo: str) -> Dict[str, Any]:
        """
        Creates a new Lightning invoice. (Mocked)
        """
        invoice_id = str(uuid.uuid4())
        
        # Mock a BOLT 11 payment request string
        mock_payment_request = f"lnbc{amount_sats}n1p..."

        invoice_data = {
            "id": invoice_id,
            "amount_sats": amount_sats,
            "memo": memo,
            "payment_request": mock_payment_request,
            "paid": False
        }
        mock_invoices[invoice_id] = invoice_data
        
        return {
            "invoice_id": invoice_id,
            "payment_request": mock_payment_request,
            "amount_sats": amount_sats
        }

    async def check_invoice_status(self, invoice_id: str) -> Dict[str, Any]:
        """
        Checks the status of a Lightning invoice. (Mocked)
        """
        invoice = mock_invoices.get(invoice_id)
        if not invoice:
            return {"status": "not_found"}
        
        # In a real scenario, you'd query the LND node.
        # Here, we can simulate payment for testing purposes.
        # For this mock, we'll consider any checked invoice as paid.
        if not invoice["paid"]:
            invoice["paid"] = True
            
        return {"status": "paid" if invoice["paid"] else "pending"}

# Global instance
aperture_service = ApertureService()

def get_aperture_service() -> ApertureService:
    """Get the global ApertureService instance."""
    return aperture_service
