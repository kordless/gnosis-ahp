# Gnosis Federation: Architectural Blueprint and Implementation Plan

This document outlines the vision, architecture, and implementation steps for creating a federated ecosystem of Gnosis services, unified by a central authentication service.

---

## Part 1: The Vision of the Agentic Hypercall Protocol (AHP)

### 1.1. The Problem: The Tyranny of the SDK

The current AI landscape is fracturing into walled gardens. Each new service demands a proprietary SDK, creating a "tyranny of the SDK" that stifles innovation and locks users into specific ecosystems. This is a return to the fragmented, pre-internet era of computing.

### 1.2. The Solution: The Primal Protocol

The AHP rejects this complexity. It is a "post-protocol" manifesto built on a radical return to first principles: **It's Just The URL.**

*   **All actions are GET requests.**
*   **Tools are paths.**
*   **Parameters are query strings.**

This minimalist approach ensures that any agent capable of constructing a URL can participate in the ecosystem. It is the foundation of a truly open, interoperable, and agent-first web.

### 1.3. The Federated World

The ultimate vision is not a single, monolithic server, but a constellation of sovereign, interoperable nodes. `gnosis-ocr`, `gnosis-wraith`, and `gnosis-ahp` are the first stars in this constellation. To enable this, we need a common trust anchor: a centralized authentication service.

---

## Part 2: Implementation of `auth.nuts.services`

This new, standalone service will be the heart of the Gnosis federation. It will be the single source of truth for authentication.

### 2.1. Core Functionality

*   **Token Exchange:** Its primary endpoint, `/auth`, will accept a long-lived, pre-shared key (the `AHP_TOKEN`) and exchange it for a short-lived, stateless, signed bearer token (a simplified JWT).
*   **Key Management:** It will be the *only* service that knows the `AHP_TOKEN` secret. It will also manage a public/private key pair for signing the bearer tokens.
*   **Public Key Endpoint:** It will expose a `/.well-known/jwks.json` endpoint to publish the public key, allowing other services to verify the bearer tokens.

### 2.2. Implementation Steps

1.  **Create a new service directory:** `gnosis-auth`.
2.  **Initialize a new FastAPI application** inside this directory.
3.  **Generate a public/private key pair** (e.g., using `openssl`). The private key will be stored as a secret in the `gnosis-auth` service. The public key will be shared with the other services.
4.  **Implement the `/auth` endpoint:**
    *   It will accept a `token` (the `AHP_TOKEN`) as a query parameter.
    *   It will validate this token against the one stored in its environment.
    *   Upon success, it will generate a JWT-style bearer token, signed with the private key. The payload will include the `agent_id` and an expiration time.
5.  **Implement the `/.well-known/jwks.json` endpoint:** This will return the public key in the standard JSON Web Key Set format.
6.  **Refactor the existing Gnosis services (`gnosis-ahp`, `gnosis-ocr`, `gnosis-wraith`):**
    *   Remove the `/auth` endpoint from `gnosis-ahp`.
    *   Modify the `verify_token` dependency in each service to:
        1.  Fetch the public key from `https://auth.nuts.services/.well-known/jwks.json` at startup.
        2.  Use this public key to verify the signature of the bearer tokens it receives.

---

## Part 3: The User Authentication UI (`gnosis-wraith`)

The `gnosis-wraith` service will be the primary user-facing component for authentication and account management.

### 3.1. Core Functionality

*   **User Login:** It will provide a simple web UI for users to log in (e.g., with a username/password or a social login).
*   **Token Issuance:** Upon successful login, it will be responsible for generating a new, unique `AHP_TOKEN` for the user.
*   **Secure Token Delivery:** It will securely deliver this `AHP_TOKEN` to the user via email. This is the crucial step that bridges the human user with the agentic ecosystem.

### 3.2. Implementation Steps

1.  **Create a login page** in the `gnosis-wraith` templates.
2.  **Implement a `/login` endpoint:**
    *   This will handle the user's credentials.
    *   Upon successful authentication, it will generate a new, cryptographically secure `AHP_TOKEN`.
3.  **Implement an email delivery service:**
    *   This service will be responsible for sending the `AHP_TOKEN` to the user's registered email address.
    *   The email will contain clear instructions for the user on how to provide this token to their AI agent.
4.  **Update the UI:** The UI should provide a clear and simple flow for the user to request and receive their token.

This three-part plan provides a complete roadmap for building a secure, scalable, and federated ecosystem of Gnosis services.
