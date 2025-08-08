# Debugging Ollama Connection in Production

## The Issue
gnosis-ahp can't connect to `ollama.nuts.services:11434` in production, while gnosis-ocr can.

## Key Differences Found

### 1. Environment Variable Configuration
- **gnosis-ocr** explicitly sets `OLLAMA_API_URL` in its Cloud Run deployment
- **gnosis-ahp** relies on `AHP_ENVIRONMENT` to determine the URL

### 2. The Problem
In the production Cloud Run deployment, `AHP_ENVIRONMENT` is likely not being set, causing it to default to "local" and try to connect to `http://host.docker.internal:11434` instead of `http://ollama.nuts.services:11434`.

## Solution

You need to set the environment variable in your Cloud Run deployment:

```bash
# Option 1: Set AHP_ENVIRONMENT to anything other than "local"
AHP_ENVIRONMENT=production

# Option 2: Explicitly set OLLAMA_BASE_URL
OLLAMA_BASE_URL=http://ollama.nuts.services:11434
```

## Quick Fix for .env.cloudrun

Add this to your `.env.cloudrun` file:

```
AHP_ENVIRONMENT=production
OLLAMA_BASE_URL=http://ollama.nuts.services:11434
```

## Verify in Cloud Run Console

1. Go to Cloud Run console
2. Find your gnosis-ahp service
3. Click "EDIT & DEPLOY NEW REVISION"
4. Go to "Variables & Secrets" tab
5. Add:
   - Name: `AHP_ENVIRONMENT`, Value: `production`
   - Name: `OLLAMA_BASE_URL`, Value: `http://ollama.nuts.services:11434`

## Test Command

After deployment, test with:
```bash
curl https://your-cloud-run-url/list_ollama_models?bearer_token=your-token
```

The updated code now includes better logging that will show exactly what URL is being used and what type of error is occurring.
