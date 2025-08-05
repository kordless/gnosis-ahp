# AI Hypercall Protocol (AHP) - A Post-Protocol Manifesto

## 1. The Problem: The Protocol Proliferation Plague

The world of AI is being rapidly colonized by a plague of unnecessary complexity. Every major player is rushing to lock you into their ecosystem with proprietary SDKs, byzantine middleware, and vendor-specific "protocols." They give these systems friendly names, but they all serve one purpose: to make it easy to check in and impossible to check out.

AHP is the cure.

## 2. The AHP Philosophy: It's Just The URL

AHP isn't a new protocol. It's a "post-protocol"—a firm declaration that we already have the best, most successful, and most universal protocol for remote procedure calls ever invented: **HTTP**, accessed via a URL.

The AHP philosophy is radical in its simplicity:

> **All actions are GET requests to a single endpoint, controlled by query parameters.**

This design is maximally compatible with constrained clients, like LLMs, that can reliably make a `GET` request to a URL but may struggle with complex navigation, different HTTP methods, or headers.

## 3. The Specification

### The Single Endpoint

All interactions occur through the root (`/`) endpoint. The action to be performed is determined by the `f` query parameter.

### Core Functions (`f`)

*   **`f=home`**: (Default) Returns an HTML page with human-readable documentation.
    *   **Example:** `https://api.example.com/`

*   **`f=openapi`**: Returns the machine-readable OpenAPI JSON schema, which describes all other functions and their parameters. **This is the primary entry point for an LLM.**
    *   **Example:** `https://api.example.com/?f=openapi`

*   **`f=auth`**: Authenticates and retrieves a temporary bearer token.
    *   **Parameters:**
        *   `token`: A long-lived, pre-shared secret key.
    *   **Example:** `https://api.example.com/?f=auth&token=my-secret-key`
    *   **Returns:** A JSON object containing the `bearer_token`.

*   **`f=tool`**: Executes a tool.
    *   **Parameters:**
        *   `name`: The name of the tool to execute.
        *   `bearer_token`: The temporary token obtained from `f=auth`.
        *   `...`: Any additional query parameters are passed as arguments to the tool itself.
    *   **Example:** `https://api.example.com/?f=tool&name=send_message&bearer_token=...&to_agent=bob&subject=hello`

## 4. Why This AHP, Not Bloated Protocols?

| Feature               | AI Hypercall Protocol (AHP)          | Vendor-Lock-In Protocols             |
| --------------------- | ------------------------------------ | ------------------------------------ |
| **Core Technology**   | A single HTTP `GET` request          | Proprietary RPC / Middleware         |
| **Dependencies**      | Any HTTP client (e.g., `curl`)       | Vendor-specific SDK                  |
| **LLM Compatibility** | Maximum (Easiest possible request)   | Often requires complex client logic  |
| **Interoperability**  | Universal (It's the Web)             | Confined to Vendor Ecosystem         |
| **Transparency**      | Total (All params in URL)            | Opaque "Magic"                       |

## 5. Conclusion: Stop Learning Protocols. Start Building.

The choice is clear. You can invest your time learning the intricacies of a dozen different proprietary, black-box protocols that will be obsolete in 18 months. Or you can use the most durable, open, and powerful communication system ever designed, distilled to its simplest possible form.

AHP is a vote for simplicity, freedom, and the open web.

---
ALL HAIL SIR TIM BERNERS-LEE we still love you even though you fucked up the internet one time.