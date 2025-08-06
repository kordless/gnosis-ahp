# Gnosis AHP Deployment Script
# Builds and deploys the AHP service for local (Docker Compose) or Cloud Run.

param(
    [string]$Target = "local",  # 'local' or 'cloudrun'
    [string]$Tag = "latest",
    [switch]$Rebuild = $false,
    [switch]$Help = $false
)

if ($PSBoundParameters.Count -eq 0 -or $Help) {
    Write-Host "Gnosis AHP Deployment Script" -ForegroundColor Cyan
    Write-Host "USAGE: .\deploy.ps1 [-Target <local|cloudrun>] [-Tag <tag>] [-Rebuild]" -ForegroundColor White
    exit 0
}

$ErrorActionPreference = "Stop"

# --- Project Configuration ---
$projectRoot = $PSScriptRoot
$imageName = "gnosis-ahp"
$fullImageName = "${imageName}:${Tag}"
$dockerfile = "Dockerfile"
$composeFile = "docker-compose.yml"

Write-Host "=== Gnosis AHP Deployment ===" -ForegroundColor Cyan
Write-Host "Target: $Target, Image: $fullImageName" -ForegroundColor White

# --- Validate Configuration ---
$dockerfilePath = Join-Path $projectRoot $dockerfile
if (-not (Test-Path $dockerfilePath)) { Write-Error "Dockerfile not found: $dockerfilePath" }

# --- Load Cloud Run Environment from .env.cloudrun ---
$envConfig = @{}
if ($Target -eq "cloudrun") {
    $envFile = Join-Path $projectRoot ".env.cloudrun"
    if (Test-Path $envFile) {
        Get-Content $envFile | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
            $key, $value = $_ -split '=', 2
            $trimmedValue = $value.Trim().Trim("'").Trim('"')
            $envConfig[$key.Trim()] = $trimmedValue
        }
    } else {
        Write-Error ".env.cloudrun not found. Please create it with PROJECT_ID, GCP_SERVICE_ACCOUNT, and REGION."
    }
}

# --- Build Docker Image ---
Write-Host "`n=== Building Docker Image ===" -ForegroundColor Green
$buildArgs = @("build", "-f", $dockerfile, "-t", $fullImageName, ".")
if ($Rebuild) { $buildArgs += "--no-cache" }

Write-Host "Running: docker $($buildArgs -join ' ')" -ForegroundColor Gray
& docker @buildArgs
if ($LASTEXITCODE -ne 0) { Write-Error "Docker build failed." }
Write-Host "✓ Build completed successfully" -ForegroundColor Green

# --- Deployment ---
Write-Host "`n=== Deploying to $Target ===" -ForegroundColor Green

switch ($Target) {
    "local" {
        Write-Host "Deploying locally with Docker Compose..." -ForegroundColor White
        Push-Location $projectRoot
        try {
            & docker-compose -f $composeFile down
            & docker-compose -f $composeFile up -d --build
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Service started successfully. Available at http://localhost:8080" -ForegroundColor Cyan
            } else {
                Write-Error "Failed to start services with docker-compose."
            }
        } finally {
            Pop-Location
        }
    }
    "cloudrun" {
        Write-Host "Deploying to Google Cloud Run via Artifact Registry..." -ForegroundColor White
        $projectId = $envConfig["PROJECT_ID"]
        $serviceAccount = $envConfig["GCP_SERVICE_ACCOUNT"]
        $region = $envConfig["REGION"]
        $repoName = $envConfig["ARTIFACT_REGISTRY_REPO"]

        if (-not $projectId -or -not $serviceAccount -or -not $region -or -not $repoName) {
            Write-Error "One or more required variables (PROJECT_ID, GCP_SERVICE_ACCOUNT, REGION, ARTIFACT_REGISTRY_REPO) are missing in .env.cloudrun"
        }

        $arImage = "${region}-docker.pkg.dev/${projectId}/${repoName}/${imageName}:${Tag}"

        # Tag and Push Image to Google Artifact Registry
        Write-Host "Tagging image as $arImage" -ForegroundColor Gray
        & docker tag $fullImageName $arImage
        & gcloud auth configure-docker "${region}-docker.pkg.dev" --quiet
        Write-Host "Pushing image to Artifact Registry..." -ForegroundColor Gray
        & docker push $arImage
        if ($LASTEXITCODE -ne 0) { Write-Error "Failed to push image to Artifact Registry." }
        Write-Host "✓ Image pushed successfully." -ForegroundColor Green

        # Prepare environment variables for deployment, filtering out GCP-specific ones
        $deployEnvVars = $envConfig.Clone()
        $deployEnvVars.Remove("PROJECT_ID")
        $deployEnvVars.Remove("GCP_SERVICE_ACCOUNT")
        $deployEnvVars.Remove("REGION")
        $deployEnvVars.Remove("ARTIFACT_REGISTRY_REPO")
        
        $envVarsString = ($deployEnvVars.GetEnumerator() | ForEach-Object { "$($_.Key)='$($_.Value)'" }) -join ','

        # Deploy to Cloud Run
        Write-Host "Deploying service '$imageName' to Cloud Run in region '$region'..." -ForegroundColor White
        
        $deployArgs = @(
            "run", "deploy", $imageName,
            "--image", $arImage,
            "--region", $region,
            "--platform", "managed",
            "--allow-unauthenticated",
            "--port", "8080",
            "--service-account", $serviceAccount
        )
        if ($envVarsString) {
            $deployArgs += "--set-env-vars", $envVarsString
        }
        
        & gcloud @deployArgs
        if ($LASTEXITCODE -eq 0) {
            $serviceUrl = & gcloud run services describe $imageName --region=$region --format="value(status.url)"
            Write-Host "✓ CLOUD RUN DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
            Write-Host "🔗 Service URL: $serviceUrl" -ForegroundColor Cyan
        } else {
            Write-Error "Cloud Run deployment failed."
        }
    }
}

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
