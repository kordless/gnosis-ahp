# PowerShell script to test the refactored Gnosis AHP API.
# All calls are GET requests to the root endpoint with different query parameters.

$ErrorActionPreference = "Stop"

$baseUrl = "http://localhost:8000"
$authKey = "dev_token_123" # The default pre-shared key from main.py

Write-Host "=== Starting Gnosis AHP v1.0 API Test ===" -ForegroundColor Cyan
Write-Host "Targeting API at: $baseUrl"

# --- Step 1: Health Check (Get Homepage) ---
try {
    Write-Host "`n[1] Checking server status by fetching homepage..." -ForegroundColor White
    $response = Invoke-RestMethod -Uri "$baseUrl/?f=home" -Method Get
    if ($response) {
        Write-Host "✓ SUCCESS: Server is running and returned homepage." -ForegroundColor Green
    } else {
        Write-Error "Server status check failed. No response."
    }
} catch {
    Write-Error "Failed to connect to the server at $baseUrl. Is the Docker container running? (.\deploy.ps1 -Target local)"
    exit 1
}

# --- Step 2: Get Auth Token ---
$bearerToken = $null
try {
    Write-Host "`n[2] Fetching temporary bearer token..." -ForegroundColor White
    $authUrl = "$baseUrl/?f=auth&token=$authKey"
    $authResponse = Invoke-RestMethod -Uri $authUrl -Method Get
    $bearerToken = $authResponse.bearer_token
    if ($bearerToken) {
        Write-Host "✓ SUCCESS: Acquired bearer token." -ForegroundColor Green
    } else {
        Write-Error "Failed to acquire bearer token. Response: $($authResponse | ConvertTo-Json)"
    }
} catch {
    Write-Error "An error occurred while fetching the auth token. Error: $($_.Exception.Message)"
    exit 1
}

# --- Step 3: Execute a Protected Tool ---
if (-not $bearerToken) {
    Write-Error "Cannot proceed to Step 3 without a bearer token."
    exit 1
}
try {
    Write-Host "`n[3] Executing protected tool 'send_message'..." -ForegroundColor White
    
    $toolParams = @{
        f = "tool"
        name = "send_message"
        bearer_token = $bearerToken
        to_agent = "agent_k"
        from_agent = "test_script"
        subject = "AHP Test Message"
        body = "This is a test message sent from the refactored test_api.ps1 script at $(Get-Date)."
    }
    
    # Build the full URL with encoded parameters
    $uriBuilder = New-Object System.UriBuilder($baseUrl)
    $query = [System.Web.HttpUtility]::ParseQueryString([string]::Empty)
    foreach ($key in $toolParams.Keys) {
        $query[$key] = $toolParams[$key]
    }
    $uriBuilder.Query = $query.ToString()
    $fullUrl = $uriBuilder.ToString()

    $toolResponse = Invoke-RestMethod -Uri $fullUrl -Method Get
    
    if ($toolResponse.result.success) {
        Write-Host "✓ SUCCESS: Tool 'send_message' executed successfully." -ForegroundColor Green
        Write-Host "   Message ID: $($toolResponse.result.message_id)"
    } else {
        Write-Error "Tool execution reported failure. Response: $($toolResponse | ConvertTo-Json)"
    }
    
} catch {
    $statusCode = $_.Exception.Response.StatusCode
    $responseBody = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($responseBody)
    $errorText = $reader.ReadToEnd()
    
    Write-Error "An error occurred while executing the tool. Status: $statusCode. Details: $errorText"
    exit 1
}

Write-Host "`n=== API Test Completed Successfully ===" -ForegroundColor Cyan