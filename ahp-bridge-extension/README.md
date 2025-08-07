# AHP Bridge for Claude - Chrome Extension

This extension allows you to execute AHP (AI Hypercall Protocol) tool calls directly from your Claude conversations.

## How to Install (for Development)

1.  **Download the code:** Make sure you have the `ahp-bridge-extension` directory on your local machine.
2.  **Open Chrome Extensions:** Open Google Chrome and navigate to `chrome://extensions`.
3.  **Enable Developer Mode:** In the top right corner of the Extensions page, toggle the "Developer mode" switch to on.
4.  **Load Unpacked:** Click the "Load unpacked" button that appears on the top left.
5.  **Select Directory:** In the file dialog, navigate to and select the `ahp-bridge-extension` directory.
6.  **Done!** The "AHP Bridge for Claude" extension should now appear in your list of extensions and be active.

## How to Use

1.  Navigate to `https://claude.ai/`.
2.  Paste an AHP URL (e.g., `http://ahp.nuts.services/get_tools`) into a chat.
3.  An "⚡ Execute" button should appear next to the URL.
4.  Click the button to execute the AHP tool call.
5.  The result will be logged to the browser's developer console (for now).
