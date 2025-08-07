#!/usr/bin/env pwsh
# Production deployment - mirrors staging approach but for production
param(
    [switch]$SkipBuild = $false,
    [switch]$AutoConfirm = $false,
    [switch]$TrafficOnly = $false
)

# Configuration
$PROJECT_ID = "gnosis-459403"
$SERVICE_NAME = "gnosis-wraith"
$REGION = "us-central1"
$IMAGE_NAME = "us-central1-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/$SERVICE_NAME"
$ENV_FILE = ".env.cloudrun"

Write-Host "`n=== Production Deployment ===" -ForegroundColor Red
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host "Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Registry: Artifact Registry (migrated from GCR)" -ForegroundColor DarkGray

# Safety check for production
if (-not $AutoConfirm -and -not $TrafficOnly) {
    Write-Host "`n⚠️  WARNING: This will deploy to PRODUCTION!" -ForegroundColor Red
    $response = Read-Host "Are you sure you want to continue? (yes/no)"
    if ($response -ne "yes") {
        Write-Host "Deployment cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Just update traffic if requested
if ($TrafficOnly) {
    Write-Host "`nUpdating traffic to latest revision..." -ForegroundColor Yellow
    gcloud run services update-traffic $SERVICE_NAME `
        --to-latest `
        --region=$REGION `
        --project=$PROJECT_ID
    
    Write-Host "`n✓ Traffic updated to latest revision!" -ForegroundColor Green
    exit 0
}

# Build and push if not skipped
if (-not $SkipBuild) {
    # Configure Docker authentication for Artifact Registry
    Write-Host "`n=== Configuring Docker Authentication ===" -ForegroundColor Yellow
    
    # Ensure we're using the correct project
    gcloud config set project $PROJECT_ID
    
    # Configure docker auth
    gcloud auth configure-docker $REGION-docker.pkg.dev --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to configure Docker authentication!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n=== Building Docker Image ===" -ForegroundColor Yellow
    docker build -t $IMAGE_NAME .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker build failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n=== Pushing to Artifact Registry ===" -ForegroundColor Yellow
    docker push $IMAGE_NAME
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Docker push failed!" -ForegroundColor Red
        exit 1
    }
}

# Load environment variables
Write-Host "`n=== Loading Environment Variables ===" -ForegroundColor Yellow
if (-not (Test-Path $ENV_FILE)) {
    Write-Host "ERROR: $ENV_FILE not found!" -ForegroundColor Red
    exit 1
}

$envVars = @()
Get-Content $ENV_FILE | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.*)$') {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        if ($key -and $value) {
            $envVars += "--set-env-vars=$key=$value"
            Write-Host "  ✓ $key" -ForegroundColor DarkGray
        }
    }
}

Write-Host "  Loaded $($envVars.Count) environment variables" -ForegroundColor Green

# Deploy to Cloud Run
Write-Host "`n=== Deploying to Cloud Run (PRODUCTION) ===" -ForegroundColor Red
$deployArgs = @(
    "run", "deploy", $SERVICE_NAME,
    "--image", $IMAGE_NAME,
    "--platform", "managed",
    "--region", $REGION,
    "--project", $PROJECT_ID,
    "--allow-unauthenticated",
    "--memory", "2Gi",
    "--cpu", "2",
    "--timeout", "300",
    "--concurrency", "100",
    "--port", "5678",
    "--max-instances", "10"
) + $envVars

# Execute deployment
gcloud @deployArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Production deployment complete!" -ForegroundColor Green
    Write-Host "  Service URL: https://$SERVICE_NAME-$PROJECT_ID.uc.r.appspot.com" -ForegroundColor Cyan
    Write-Host "  Custom domain: https://wraith.nuts.services" -ForegroundColor Cyan
} else {
    Write-Host "`n✗ Deployment failed!" -ForegroundColor Red
    exit 1
}