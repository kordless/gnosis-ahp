# Gnosis AHP Server

This server implements the Agentic Hosting Protocol (AHP).

## Agentic Hosting Protocol (AHP)

The philosophy, architecture, and protocol specification are detailed in the canonical document: [PROTOCOL.md](PROTOCOL.md). This is the single source of truth.

## Running the Server

### Prerequisites

- [Docker](https://www.docker.com/get-started)

### Instructions

1.  **Build the Docker Image:**

    ```bash
    docker build -t gnosis-ahp .
    ```

2.  **Create Environment File:**

    Create a `.env` file in the project root and add the required environment variables. You can use `.env.cloudrun` as a starting point. A pre-shared key must be set for the `AHP_TOKEN` variable.

    ```
    AHP_TOKEN="your-strong-pre-shared-key"
    ```

3.  **Run the Container:**

    ```bash
    docker run --rm -it -p 8080:8080 --env-file .env gnosis-ahp
    ```

    The server will be available at `http://localhost:8080`.

### Testing

A simple PowerShell script is provided to test the core API functions.

```powershell
./test_api.ps1
```