# AI Hypercall Protocol (AHP) - A Post-Protocol Manifesto

## 1. The Problem: The Protocol Proliferation Plague

The world of AI is being rapidly colonized by a plague of unnecessary complexity. Every major player is rushing to lock you into their ecosystem with proprietary SDKs, byzantine middleware, and vendor-specific "protocols." They give these systems friendly names, but they all serve one purpose: to make it easy to check in and impossible to check out.

AHP is the cure.

## 2. The AHP Philosophy: It's Just The URL

AHP isn't a new protocol. It's a "post-protocol"—a firm declaration that we already have the best, most successful, and most universal protocol for remote procedure calls ever invented: **HTTP**, accessed via a URL.

The AHP philosophy is radical in its simplicity:

> **All actions are GET requests. Tools are paths. Parameters are query strings.**

This design is maximally compatible with constrained clients, like LLMs, that can reliably make a `GET` request to a URL but may struggle with complex navigation, different HTTP methods, or headers.

## 3. The Specification

### Core System Endpoints

*   **`/`**: (Default) Returns an HTML page with human-readable documentation.
    *   **Example:** `https://api.example.com/`

*   **`/openapi`** or **`/schema`**: Returns the machine-readable OpenAPI JSON schema, which describes all tools and their parameters. **This is the primary entry point for an LLM.**
    *   **Example:** `https://api.example.com/openapi`
    *   **With auth:** `https://api.example.com/openapi?bearer_token=...` (returns full tool list)

*   **`/auth`**: Authenticates and retrieves a temporary bearer token.
    *   **Parameters:**
        *   `token`: A long-lived, pre-shared secret key.
    *   **Example:** `https://api.example.com/auth?token=my-secret-key`
    *   **Returns:** A JSON object containing the `bearer_token`.

### Tool Endpoints

Each tool is its own path. Tools own their parameter namespace completely.

*   **`/{tool_name}`**: Executes a specific tool.
    *   **Parameters:**
        *   `bearer_token`: The temporary token obtained from `/auth`.
        *   `session_id` (optional): A session identifier to maintain state across tool calls.
        *   `...`: Any additional query parameters specific to the tool.
    *   **Examples:** 
        *   `https://api.example.com/generate_qr_code?bearer_token=...&data=hello`
        *   `https://api.example.com/send_message?bearer_token=...&to=bob&subject=hello`
        *   `https://api.example.com/save_memory?bearer_token=...&session_id=...&name=my_data&data={...}`

### Session Management

For stateful operations, a session can be created.

*   **`/session/start`**: Creates a new session.
    *   **Parameters:**
        *   `agent_id` (optional): An identifier for the agent creating the session. Defaults to `default_agent`.
    *   **Returns:** A JSON object containing the `session_id`.

### Reserved Paths

The following paths are reserved and cannot be tool names:
- `/` (root)
- `/auth`
- `/openapi` 
- `/schema`
- `/session/start`
- `/human_home`
- `/robots.txt`
- `/health` (future use)

## 4. Migration from v1

For backward compatibility during transition:
- The old `/?f=` pattern MAY continue to work
- New implementations SHOULD use the path-based structure
- Clients SHOULD detect which version via the OpenAPI schema structure

## 5. Why This Design?

| Feature               | AI Hypercall Protocol (AHP) v2       | Vendor-Lock-In Protocols             |
| --------------------- | ------------------------------------ | ------------------------------------ |
| **Core Technology**   | HTTP `GET` with RESTful paths        | Proprietary RPC / Middleware         |
| **Dependencies**      | Any HTTP client (e.g., `curl`)       | Vendor-specific SDK                  |
| **LLM Compatibility** | Maximum (Simple URL patterns)        | Often requires complex client logic  |
| **Interoperability**  | Universal (It's the Web)             | Confined to Vendor Ecosystem         |
| **Transparency**      | Total (All params in URL)            | Opaque "Magic"                       |
| **Tool Namespacing**  | Each tool owns its parameters        | Shared parameter space               |

## 6. Conclusion: Tools as Resources

The evolution from v1's function-dispatcher pattern (`/?f=tool&name=...`) to v2's resource pattern (`/{tool_name}?...`) represents a philosophical shift: **tools aren't just functions to call, they're resources to access**.

This isn't just cleaner URLs. It's recognition that in the age of AI, every capability should be addressable, discoverable, and composable through the simplest possible interface.

AHP v2 is a vote for simplicity, freedom, and the open web.

---
ALL HAIL SIR TIM BERNERS-LEE we still love you even though you fucked up the internet one time.