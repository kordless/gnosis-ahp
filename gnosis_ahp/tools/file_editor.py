"""
AHP Tools for advanced file editing, versioning, and diff application.
This tool wraps the powerful engine from diff_engine.py.
"""
from typing import Dict, Any

from gnosis_ahp.tools.base import tool
from gnosis_ahp.core import diff_engine

@tool(description="Apply a diff to a file to edit its content. Creates a versioned backup.")
async def apply_diff(file_path: str, diff_text: str, change_tag: str = None) -> Dict[str, Any]:
    """
    Applies a diff to the specified file.

    This tool uses a powerful fuzzy matching engine to apply changes, even if the
    surrounding code has slightly changed. It automatically creates a versioned
    backup of the file before making any changes.

    Args:
        file_path: The absolute path to the file to be edited.
        diff_text: The diff content to apply, using the standard format:
                   <<<<<<< SEARCH
                   content to be replaced
                   =======
                   new content to insert
                   >>>>>>> REPLACE
        change_tag (optional): A tag to associate with this change for easier restoration.

    Returns:
        A dictionary containing the result of the operation.
    """
    return await diff_engine.file_diff_write(
        file_path=file_path,
        diff_text=diff_text,
        change_tag=change_tag
    )

@tool(description="List all saved versions of a file.")
async def get_versions(file_path: str) -> Dict[str, Any]:
    """
    Retrieves the version history for a specific file.

    Args:
        file_path: The absolute path to the file.

    Returns:
        A dictionary containing the current version and a list of all past versions.
    """
    return await diff_engine.file_diff_versions(file_path=file_path)

@tool(description="Restore a file to a specific version.")
async def restore_version(file_path: str, version_number: int) -> Dict[str, Any]:
    """
    Reverts a file to a previously saved version.

    Args:
        file_path: The absolute path to the file to restore.
        version_number: The integer version number to restore to, which can be
                        obtained from the get_versions() tool.

    Returns:
        A dictionary confirming the success of the restore operation.
    """
    return await diff_engine.file_diff_restore(
        file_path=file_path,
        version_number=version_number
    )
