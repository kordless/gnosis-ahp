# HOWTO: Implement Payments and Federated Identity

This guide explains how to use the AHP server's two most powerful features: **Project Aperture** for monetizing tools and the **Federated Identity** model for secure, centralized authentication.

---

## 1. Project Aperture: Monetizing Tools with Bitcoin Lightning

Project Aperture allows you to require a Bitcoin Lightning payment to execute specific tools. This turns your AHP server into a true pay-per-use platform.

### How to Enable Payments on a Tool

Enabling payments is incredibly simple. You only need to add the `cost` parameter to the `@tool` decorator in your tool's Python file. The cost is denominated in **satoshis**, the smallest unit of Bitcoin.

**Example: Making a tool cost 150 satoshis**

```python
# In your tool's file, e.g., gnosis_ahp/tools/my_premium_tool.py

from gnosis_ahp.tools.base import tool

# Before: A free tool
@tool(description="A tool that does something amazing.")
def amazing_tool(prompt: str) -> str:
    return f"Amazing result for: {prompt}"

# After: A premium tool that costs 150 sats
@tool(description="A tool that does something amazing.", cost=150)
def amazing_tool(prompt: str) -> str:
    return f"Amazing result for: {prompt}"
```

That's it. The AHP server's middleware will now automatically enforce a payment requirement for `amazing_tool`.

### The Payment Workflow (For an API Consumer)

As a developer (human or AI) calling a premium tool, you must follow this specific workflow:

**Step 1: Initial Request (Fails as Expected)**

First, you make a normal request to the tool.

```bash
curl -s "http://localhost:8080/amazing_tool?prompt=test&bearer_token=..."
```

**Step 2: Receive `402 Payment Required` and Invoice**

The server will reject this request with an `HTTP 402` error and provide a Lightning invoice in the response body.

```json
{
    "error": "payment_required",
    "message": "This tool requires a Lightning payment to proceed.",
    "details": {
        "invoice_id": "a1b2c3d4-e5f6-...",
        "payment_request": "lnbc150n1p...",
        "amount_sats": 150
    }
}
```

-   `payment_request`: The BOLT 11 invoice to be paid by a Lightning wallet.
-   `invoice_id`: A unique ID for this payment attempt.

**Step 3: Pay the Lightning Invoice**

The client application uses a Lightning-compatible wallet to pay the `payment_request`.

**Step 4: Retry with Proof of Payment**

You make the *exact same request* again, but this time you add the `invoice_id` from Step 2 as a query parameter. This serves as your proof of payment.

```bash
curl -s "http://localhost:8080/amazing_tool?prompt=test&bearer_token=...&invoice_id=a1b2c3d4-e5f6-..."
```

**Step 5: Receive Successful `200 OK` Response**

The server's middleware validates that the invoice has been paid. The request is allowed to proceed, the tool executes, and you receive the successful result.

---

## 2. The Federated Identity Model

The identity system allows a central, authoritative server (like `https://ahp.nuts.services`) to issue tokens that can be trusted and validated by other, separate services (like a local AHP node).

### How It Works: The "Corporate ID Badge" Analogy

-   **Central Authority (`ahp.nuts.services`):** This is your company's World Headquarters (HQ). It's the only place that issues official ID badges.
-   **Bearer Token:** This is your secure, corporate ID badge.
-   **Local AHP Node:** This is a secure, regional branch office.

The workflow is as follows:

1.  **Get Your Badge from HQ:** A user (human or AI) authenticates with the central authority (`/auth`) to get a bearer token.
2.  **Visit a Branch Office:** The user makes a request to a local AHP node, presenting this token.
3.  **The Local Node Verifies with HQ:** The local node doesn't trust the token blindly. It makes a secure, server-to-server call back to the central authority (e.g., to a hypothetical `/auth/validate` endpoint) to confirm the token is valid.
4.  **Access Granted:** Once the central authority confirms the token's validity, the local node trusts the user's identity and grants access.

---

## 3. How Identity and Payments Work Together

Identity and Payments are two separate but complementary systems that combine to create a secure, monetizable platform.

> **Identity answers the question: *Who are you?***
> (Authentication & Authorization)
>
> **Payments answer the question: *Have you paid the toll for this specific action?***
> (Metering & Monetization)

For a premium tool, both checks must pass:

1.  You must first present a valid **Bearer Token** to prove you are an authenticated user.
2.  Then, you must present a paid **`invoice_id`** to prove you have paid for this specific tool execution.

This powerful combination allows you to build a robust ecosystem where trusted, authenticated agents can securely purchase access to premium, on-demand capabilities across a distributed network of services.
