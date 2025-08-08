"""
AHP Tool for basic network connectivity testing.
"""
import socket
from typing import Dict, Any

from gnosis_ahp.tools.base import tool

@tool(description="Performs a basic TCP socket connection test to a specified host and port.")
async def network_test(host: str, port: int, timeout: int = 10) -> Dict[str, Any]:
    """
    Attempts to open a TCP socket to a host and port to test connectivity.

    Args:
        host: The hostname or IP address to connect to.
        port: The port number to connect to.
        timeout: The connection timeout in seconds.

    Returns:
        A dictionary indicating whether the connection was successful.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return {"success": True, "message": f"Successfully connected to {host} on port {port}."}
    except socket.gaierror as e:
        return {"success": False, "error": "Hostname could not be resolved.", "details": str(e)}
    except socket.timeout:
        return {"success": False, "error": "Connection timed out.", "details": f"No response from {host}:{port} within {timeout} seconds."}
    except ConnectionRefusedError:
        return {"success": False, "error": "Connection refused.", "details": f"The server at {host}:{port} actively refused the connection."}
    except Exception as e:
        return {"success": False, "error": "An unexpected network error occurred.", "details": str(e)}
