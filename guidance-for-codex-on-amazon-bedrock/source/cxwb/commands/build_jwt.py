"""`cxwb build-jwt` — build and push JWT middleware Docker image to ECR."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import boto3
import click

from .. import profile

# Path to JWT middleware directory
REPO_ROOT = Path(__file__).parent.parent.parent.parent
JWT_MIDDLEWARE_DIR = REPO_ROOT / "deployment" / "litellm" / "jwt-middleware"
DOCKERFILE = JWT_MIDDLEWARE_DIR / "Dockerfile"


def create_ecr_repository(region: str, repo_name: str) -> str:
    """Create ECR repository if it doesn't exist. Returns repository URI."""
    ecr = boto3.client("ecr", region_name=region)
    sts = boto3.client("sts", region_name=region)
    account_id = sts.get_caller_identity()["Account"]

    try:
        response = ecr.describe_repositories(repositoryNames=[repo_name])
        repo_uri = response["repositories"][0]["repositoryUri"]
        click.echo(f"ECR repository exists: {repo_uri}")
    except ecr.exceptions.RepositoryNotFoundException:
        click.echo(f"Creating ECR repository: {repo_name}")
        response = ecr.create_repository(
            repositoryName=repo_name,
            tags=[{"Key": "project", "Value": "codex-bedrock"}],
        )
        repo_uri = response["repository"]["repositoryUri"]
        click.echo(f"Created: {repo_uri}")

    return repo_uri


def ecr_login(region: str) -> None:
    """Authenticate Docker to ECR."""
    click.echo(f"Logging Docker into ECR ({region})...")
    ecr = boto3.client("ecr", region_name=region)

    token = ecr.get_authorization_token()
    password = token["authorizationData"][0]["authorizationToken"]
    endpoint = token["authorizationData"][0]["proxyEndpoint"]

    # Use base64 to decode the password
    import base64
    username, pwd = base64.b64decode(password).decode().split(":")

    result = subprocess.run(
        ["docker", "login", "--username", username, "--password-stdin", endpoint],
        input=pwd.encode(),
        capture_output=True,
    )
    if result.returncode != 0:
        click.echo(f"Docker login failed: {result.stderr.decode()}", err=True)
        sys.exit(1)
    click.echo("Docker authenticated.")


def build_and_push_image(region: str, repo_uri: str, tag: str = "latest") -> str:
    """Build JWT middleware Docker image and push to ECR. Returns full image URI with tag."""
    image_tag = f"{repo_uri}:{tag}"

    if not DOCKERFILE.exists():
        click.echo(f"Dockerfile not found: {DOCKERFILE}", err=True)
        sys.exit(1)

    click.echo(f"\n📦 Building JWT middleware Docker image...")
    click.echo(f"  Tag: {image_tag}")

    result = subprocess.run(
        [
            "docker",
            "build",
            "--platform", "linux/amd64",
            "-t", image_tag,
            "-f", str(DOCKERFILE),
            str(JWT_MIDDLEWARE_DIR),
        ],
        cwd=JWT_MIDDLEWARE_DIR,
    )
    if result.returncode != 0:
        click.echo("\n❌ Docker build failed.", err=True)
        sys.exit(1)

    # Push image to ECR
    click.echo(f"\nPushing image to ECR...")
    result = subprocess.run(["docker", "push", image_tag])
    if result.returncode != 0:
        click.echo("\n❌ Docker push to ECR failed.", err=True)
        sys.exit(1)

    click.echo(f"\n✓ Image pushed: {image_tag}")
    return image_tag


def run(profile_name: str) -> None:
    """Main entry point for `cxwb build-jwt`."""
    try:
        prof = profile.load(profile_name)
    except FileNotFoundError:
        click.echo(f"Profile '{profile_name}' not found. Run `cxwb init` first.", err=True)
        sys.exit(1)

    # Validate profile type
    if prof.get("auth") != "gateway":
        click.echo("JWT middleware only applies to gateway profiles.", err=True)
        sys.exit(1)

    if not prof.get("manages_infra"):
        click.echo("JWT middleware only applies to profiles that manage infrastructure.", err=True)
        sys.exit(1)

    if not prof.get("enable_oidc"):
        click.echo("JWT middleware requires OIDC to be enabled in profile.", err=True)
        click.echo("Run `cxwb init` and enable OIDC, or manually set 'enable_oidc': true in profile.", err=True)
        sys.exit(1)

    # Get configuration from profile
    region = prof.get("region")
    if not region:
        click.echo("Profile missing 'region' field.", err=True)
        sys.exit(1)

    jwt_repo_name = prof.get("jwt_ecr_repo_name", "codex-jwt-middleware")

    click.echo(f"\n🔨 Building JWT middleware for profile: {profile_name}")
    click.echo(f"  Region: {region}")
    click.echo(f"  ECR repository: {jwt_repo_name}")

    # Create ECR repository
    repo_uri = create_ecr_repository(region, jwt_repo_name)

    # Login to ECR
    ecr_login(region)

    # Build and push image
    image_uri = build_and_push_image(region, repo_uri)

    # Update profile with jwt_middleware_image_uri
    prof["jwt_middleware_image_uri"] = image_uri
    profile.save(profile_name, prof)

    click.echo(f"\n✓ Build complete. Profile updated with jwt_middleware_image_uri.")
    click.echo(f"\nNext: cxwb deploy --profile {profile_name}")
