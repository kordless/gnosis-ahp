"""
Gnosis AHP Deployment Script (Python)
Builds and deploys the AHP service for local (Docker Compose) or Cloud Run.
"""
import os
import subprocess
import argparse
import sys
from dotenv import dotenv_values

def run_command(command, cwd=None):
    """Runs a command and checks for errors."""
    print(f"Running: {' '.join(command)}", flush=True)
    try:
        process = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        print(process.stdout)
        if process.stderr:
            print(process.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}", file=sys.stderr)
        print(e.stdout, file=sys.stdout)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Gnosis AHP Deployment Script")
    parser.add_argument(
        "-t", "--target", 
        choices=["local", "cloudrun"],
        default="local", 
        help="Deployment target: 'local' or 'cloudrun'"
    )
    parser.add_argument(
        "--tag", 
        default="latest", 
        help="Docker image tag"
    )
    parser.add_argument(
        "--rebuild", 
        action="store_true", 
        help="Force a rebuild of the Docker image without cache"
    )
    args = parser.parse_args()

    # --- Project Configuration ---
    project_root = os.path.dirname(os.path.abspath(__file__))
    image_name = "gnosis-ahp"
    full_image_name = f"{image_name}:{args.tag}"
    dockerfile = "Dockerfile"
    compose_file = "docker-compose.yml"

    print("=== Gnosis AHP Deployment ===")
    print(f"Target: {args.target}, Image: {full_image_name}")

    # --- Build Docker Image ---
    print("\n=== Building Docker Image ===")
    build_command = ["docker", "build", "-f", dockerfile, "-t", full_image_name, "."]
    if args.rebuild:
        build_command.append("--no-cache")
    
    run_command(build_command)
    print("✓ Build completed successfully")

    # --- Deployment ---
    print(f"\n=== Deploying to {args.target} ===")
    if args.target == "local":
        print("Deploying locally with Docker Compose...")
        run_command(["docker-compose", "-f", compose_file, "down"])
        run_command(["docker-compose", "-f", compose_file, "up", "-d", "--build"])
        print("✓ Service started successfully. Available at http://localhost:8080")

    elif args.target == "cloudrun":
        print("Deploying to Google Cloud Run via Artifact Registry...")
        env_config = dotenv_values(".env.cloudrun")
        
        project_id = env_config.get("PROJECT_ID")
        service_account = env_config.get("GCP_SERVICE_ACCOUNT")
        region = env_config.get("REGION")
        repo_name = env_config.get("ARTIFACT_REGISTRY_REPO")

        if not all([project_id, service_account, region, repo_name]):
            print("Error: .env.cloudrun must contain PROJECT_ID, GCP_SERVICE_ACCOUNT, REGION, and ARTIFACT_REGISTRY_REPO.", file=sys.stderr)
            sys.exit(1)

        # Construct the full image path for Artifact Registry
        ar_image = f"{region}-docker.pkg.dev/{project_id}/{repo_name}/{image_name}:{args.tag}"

        # Tag and Push Image to Artifact Registry
        run_command(["docker", "tag", full_image_name, ar_image])
        run_command(["gcloud", "auth", "configure-docker", f"{region}-docker.pkg.dev", "--quiet"])
        run_command(["docker", "push", ar_image])
        print("✓ Image pushed successfully to Artifact Registry.")

        # Deploy to Cloud Run
        # Filter out keys that are not for the AHP server itself
        deploy_env_vars = {k: v for k, v in env_config.items() if k not in ["PROJECT_ID", "GCP_SERVICE_ACCOUNT", "REGION", "ARTIFACT_REGISTRY_REPO"]}
        env_vars_string = ",".join([f"{key}='{value}'" for key, value in deploy_env_vars.items()])
        
        deploy_command = [
            "gcloud", "run", "deploy", image_name,
            "--image", ar_image,
            "--region", region,
            "--platform", "managed",
            "--allow-unauthenticated",
            "--port", "8080",
            "--service-account", service_account
        ]
        if env_vars_string:
            deploy_command.extend(["--set-env-vars", env_vars_string])

        run_command(deploy_command)
        print("✓ CLOUD RUN DEPLOYMENT SUCCESSFUL!")

    print("\n=== Deployment Complete ===")

if __name__ == "__main__":
    main()
