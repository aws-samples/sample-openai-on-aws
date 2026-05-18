"""`cxwb build` — build and push LiteLLM Docker image to ECR."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

import boto3
import click

from .. import LITELLM_RECOMMENDED_VERSION, profile

# Path to the Dockerfile and litellm_config.yaml
REPO_ROOT = Path(__file__).parent.parent.parent.parent
LITELLM_DIR = REPO_ROOT / "deployment" / "litellm"
DOCKERFILE = LITELLM_DIR / "Dockerfile"
LITELLM_CONFIG = LITELLM_DIR / "litellm_config.yaml"


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
    sts = boto3.client("sts", region_name=region)
    account_id = sts.get_caller_identity()["Account"]

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


def check_docker_running() -> bool:
    """Check if Docker daemon is running."""
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def detect_host_architecture() -> str:
    """Detect host machine architecture."""
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "arm64"
    elif machine in ("x86_64", "amd64"):
        return "amd64"
    else:
        # Default to amd64 for unknown architectures
        click.echo(f"⚠️  Unknown architecture: {machine}, defaulting to amd64", err=True)
        return "amd64"


def check_docker_buildx() -> bool:
    """Check if Docker buildx is available for multi-arch builds."""
    result = subprocess.run(
        ["docker", "buildx", "version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def build_and_push_image(
    region: str, repo_uri: str, litellm_version: str, build_context: Path,
    multi_arch: bool = True
) -> str:
    """Build Docker image(s) and push to ECR. Returns full image URI with tag.

    Args:
        region: AWS region
        repo_uri: ECR repository URI
        litellm_version: LiteLLM version tag
        build_context: Path to build context
        multi_arch: If True, build for both amd64 and arm64 (default: True)
    """
    image_tag = f"{repo_uri}:{litellm_version}"

    if not DOCKERFILE.exists():
        click.echo(f"Dockerfile not found: {DOCKERFILE}", err=True)
        sys.exit(1)

    if not LITELLM_CONFIG.exists():
        click.echo(f"LiteLLM config not found: {LITELLM_CONFIG}", err=True)
        sys.exit(1)

    # Check Docker is running before attempting build
    if not check_docker_running():
        click.echo("\n❌ Docker is not running!", err=True)
        click.echo("\nDocker Desktop must be running to build images.", err=True)
        click.echo("\nTo fix:", err=True)
        click.echo("  1. Open Docker Desktop application", err=True)
        click.echo("  2. Wait for Docker to start (whale icon in menu bar)", err=True)
        click.echo("  3. Verify with: docker ps", err=True)
        click.echo("  4. Retry: cxwb build --profile <profile-name>", err=True)
        click.echo("\nAlternative: Use existing image instead of building", err=True)
        click.echo("  1. Delete profile: rm ~/.cxwb/profiles/<profile-name>.json", err=True)
        click.echo("  2. Re-run: cxwb init", err=True)
        click.echo("  3. Select: 'Use existing image from my ECR repository'", err=True)
        sys.exit(1)

    # Detect host architecture
    host_arch = detect_host_architecture()
    click.echo(f"\n📦 Building Docker image...")
    click.echo(f"  Base image: ghcr.io/berriai/litellm:{litellm_version}")
    click.echo(f"  Host architecture: {host_arch}")

    if multi_arch:
        # Multi-architecture build (both amd64 and arm64)
        if not check_docker_buildx():
            click.echo("\n⚠️  Docker buildx not available, falling back to single-arch build for amd64", err=True)
            click.echo("  (Multi-arch builds require Docker Desktop with buildx support)", err=True)
            multi_arch = False
            target_platforms = ["linux/amd64"]
        else:
            target_platforms = ["linux/amd64", "linux/arm64"]
            click.echo(f"  Target platforms: {', '.join(target_platforms)}")

            # Create/use buildx builder
            builder_name = "cxwb-multiarch"
            subprocess.run(
                ["docker", "buildx", "create", "--name", builder_name, "--use"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            click.echo(f"  Building for multiple architectures (amd64 + arm64)...")
            click.echo(f"  This may take 2-3x longer than single-arch build")

            # Build and push multi-arch image
            result = subprocess.run(
                [
                    "docker", "buildx", "build",
                    "--platform", ",".join(target_platforms),
                    "--build-arg", f"LITELLM_VERSION={litellm_version}",
                    "-t", image_tag,
                    "--push",  # buildx requires --push for multi-arch
                    "-f", str(DOCKERFILE),
                    str(build_context),
                ],
                cwd=build_context,
            )

            if result.returncode != 0:
                click.echo("\n❌ Docker buildx multi-arch build failed.", err=True)
                click.echo("\nPossible causes:", err=True)
                click.echo("  • Base image doesn't support requested architecture", err=True)
                click.echo("  • Network issue pulling base image", err=True)
                click.echo("  • QEMU emulation not enabled in Docker Desktop", err=True)
                click.echo("\nTo fix:", err=True)
                click.echo("  1. Ensure Docker Desktop > Settings > Features > Use containerd", err=True)
                click.echo("  2. Or retry with single-arch: cxwb build --no-multi-arch", err=True)
                sys.exit(1)

            click.echo(f"✓ Multi-arch image built and pushed")
            return image_tag

    # Single-architecture build (default to amd64 for ECS compatibility)
    target_platform = "linux/amd64"
    click.echo(f"  Target platform: {target_platform}")

    if host_arch == "arm64" and target_platform == "linux/amd64":
        click.echo(f"  ⚠️  Cross-compiling: ARM64 host → x86_64 target")
        click.echo(f"     (Using QEMU emulation - build may be slower)")

    click.echo(f"  Tag: {image_tag}")

    result = subprocess.run(
        [
            "docker",
            "build",
            "--platform", target_platform,
            "--build-arg", f"LITELLM_VERSION={litellm_version}",
            "-t", image_tag,
            "-f", str(DOCKERFILE),
            str(build_context),
        ],
        cwd=build_context,
    )
    if result.returncode != 0:
        click.echo("\n❌ Docker build failed.", err=True)
        click.echo("\nPossible causes:", err=True)
        click.echo("  • Base image not found (check LiteLLM version)", err=True)
        click.echo("  • Dockerfile syntax error", err=True)
        click.echo("  • Network issue pulling base image", err=True)
        if host_arch == "arm64":
            click.echo("  • QEMU emulation issue (Docker Desktop may need restart)", err=True)
        click.echo("\nCheck output above for specific error details.", err=True)
        sys.exit(1)

    # Push image to ECR (only for single-arch builds; multi-arch already pushed)
    if not multi_arch or not check_docker_buildx():
        click.echo(f"\nPushing image to ECR...")
        result = subprocess.run(["docker", "push", image_tag])
        if result.returncode != 0:
            click.echo("\n❌ Docker push to ECR failed.", err=True)
            click.echo("\nPossible causes:", err=True)
            click.echo("  • ECR authentication expired (re-run `docker login`)", err=True)
            click.echo("  • Insufficient IAM permissions (need ecr:PutImage)", err=True)
            click.echo("  • Network connectivity issue", err=True)
            click.echo("\nCheck output above for specific error details.", err=True)
            sys.exit(1)

        click.echo(f"\n✓ Image pushed: {image_tag}")

    return image_tag


def run(profile_name: str, multi_arch: bool = True) -> None:
    """Main entry point for `cxwb build`.

    Args:
        profile_name: Name of the profile to build for
        multi_arch: If True, build for both amd64 and arm64 (default: True)
    """
    try:
        prof = profile.load(profile_name)
    except FileNotFoundError:
        click.echo(f"Profile '{profile_name}' not found. Run `cxwb init` first.", err=True)
        sys.exit(1)

    # Validate profile type
    if prof.get("auth") != "gateway":
        click.echo("Build command only applies to gateway profiles.", err=True)
        sys.exit(1)

    if not prof.get("manages_infra"):
        click.echo("Build command only applies to profiles that manage infrastructure.", err=True)
        sys.exit(1)

    # Get configuration from profile
    region = prof.get("region")
    if not region:
        click.echo("Profile missing 'region' field.", err=True)
        sys.exit(1)

    ecr_repo_name = prof.get("ecr_repo_name", "codex-litellm-gateway")
    litellm_version = prof.get("litellm_version", LITELLM_RECOMMENDED_VERSION)

    click.echo(f"\n🔨 Building LiteLLM image for profile: {profile_name}")
    click.echo(f"  Region: {region}")
    click.echo(f"  ECR repository: {ecr_repo_name}")
    click.echo(f"  LiteLLM version: {litellm_version}")
    click.echo(f"  Multi-architecture: {'Yes (amd64 + arm64)' if multi_arch else 'No (amd64 only)'}")

    # Create ECR repository
    repo_uri = create_ecr_repository(region, ecr_repo_name)

    # Login to ECR
    ecr_login(region)

    # Build and push image
    image_uri = build_and_push_image(region, repo_uri, litellm_version, LITELLM_DIR, multi_arch)

    # Update profile with image_uri
    prof["image_uri"] = image_uri
    profile.save(profile_name, prof)

    click.echo(f"\n✓ Build complete. Profile updated with image_uri.")
    if multi_arch:
        click.echo(f"\n📦 Multi-arch image supports both:")
        click.echo(f"  • x86_64 (amd64) - ECS Fargate default")
        click.echo(f"  • ARM64 (arm64) - Graviton instances")
    click.echo(f"\nNext: cxwb deploy --profile {profile_name}")
