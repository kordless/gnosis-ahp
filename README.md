# 🧠 Gnosis AHP Server
**A lightweight, RESTful server for securely exposing tools to AI agents.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Powered-05998b?logo=fastapi)](https://fastapi.tiangolo.com/)

[Quick Start](#-quick-start) • [Features](#-features) • [Core-Concepts](#-core-concepts) • [API-Reference](#-api-reference)

---

## ✨ Features

- 🚀 **RESTful by Design:** Tools are first-class URL paths, not query parameters.
- 🔌 **Dynamic Tool Discovery:** Automatically discovers and registers tools at startup.
- 🔒 **Secure:** Uses bearer token authentication for tool execution.
- 📦 **Session Management:** Supports stateful operations through a session-based storage system.
- 📄 **Self-Documenting:** Provides an OpenAPI schema of all available tools.
- 🐳 **Dockerized:** Ready for containerized deployment.
- 🐍 **Simple Tool Development:** Create new tools with a simple Python decorator.

## 💡 Core Concepts

The **AI Hypercall Protocol (AHP)** is a "post-protocol" manifesto. It argues that we already have the perfect protocol for remote procedure calls: **HTTP**.

The AHP philosophy is simple:

> **All actions are GET requests. Tools are paths. Parameters are query strings.**

This design is maximally compatible with constrained clients, like LLMs, that can reliably make a `GET` request to a URL.

For a full breakdown of the philosophy and specification, see [PROTOCOL.md](PROTOCOL.md).

## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/get-started)

### Instructions

1.  **Build the Docker Image:**

    ```bash
    docker build -t gnosis-ahp .
    ```

2.  **Create Environment File:**

    Create a `.env` file in the project root. A pre-shared key must be set for the `AHP_TOKEN` variable.

    ```
    AHP_TOKEN="your-strong-pre-shared-key"
    ```

3.  **Run the Container:**

    ```bash
    docker run --rm -it -p 8080:8080 --env-file .env gnosis-ahp
    ```

    The server will be available at `http://ahp.nuts.services`.

## 📡 API Reference

### 1. Discover Tools

Get a machine-readable list of all available tools.

```bash
curl http://ahp.nuts.services/openapi
```

### 2. Authenticate

Get a temporary bearer token to use with tool calls.

```bash
# For the default agent
curl http://ahp.nuts.services/auth?token=your-pre-shared-key

# For a specific agent
curl http://ahp.nuts.services/auth?token=your-pre-shared-key&agent_id=my_agent
```

### 3. Start a Session (Optional)

For stateful operations, start a session to get a `session_id`.

```bash
curl http://ahp.nuts.services/session/start?agent_id=my_agent
```

### 4. Execute a Tool

Execute a tool by calling its path with the required parameters.

```bash
# Stateless tool call
curl "http://ahp.nuts.services/generate_qr_code?data=hello&bearer_token=..."

# Stateful tool call using a session
curl "http://ahp.nuts.services/save_memory?name=my_data&data=...&session_id=...&bearer_token=..."
```

## 🔧 Tool Development

To add a new tool:

1.  Create a Python file in `gnosis_ahp/tools/`.
2.  Use the `@tool` decorator. The server will automatically discover it.

**Stateless Example:**

```python
from gnosis_ahp.tools.base import tool

@tool(description="A simple tool that echoes text.")
def echo(text: str) -> str:
    return text
```

**Stateful Example (using session):**

```python
from gnosis_ahp.tools.base import tool
from typing import Dict, Any

@tool(description="A tool that uses session state.")
def my_stateful_tool(session: Dict[str, Any], name: str) -> str:
    """
    The 'session' object is automatically injected by the server.
    """
    storage = session["storage"]  # Get the StorageService instance
    session_id = session["id"]
    # Use storage to save/get files related to this session
    return f"Accessed session {session_id} for '{name}'"
```

## Reserved Paths

The following paths are reserved for core system functions and cannot be used as tool names:

- `/`
- `/auth`
- `/openapi`
- `/schema`
- `/session/start`
- `/human_home`
- `/robots.txt`
- `/health` (future use)

---
*Trek has spoken.*
