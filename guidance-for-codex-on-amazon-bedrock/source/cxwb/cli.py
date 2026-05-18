"""`cxwb` — top-level click group."""

from __future__ import annotations

from pathlib import Path

import click

from . import __version__, profile
from .commands import build as build_cmd
from .commands import build_jwt as build_jwt_cmd
from .commands import deploy as deploy_cmd
from .commands import destroy as destroy_cmd
from .commands import distribute as distribute_cmd
from .commands import init as init_cmd
from .commands import status as status_cmd


@click.group(help="Guided deploy for Codex on Amazon Bedrock.")
@click.version_option(__version__)
def cli() -> None:
    pass


@cli.command(help="Configure a deployment profile (interactive).")
def init() -> None:
    init_cmd.run()


@cli.command(help="Build and push LiteLLM Docker image to ECR.")
@click.option("--profile", "profile_name", default="default", show_default=True)
@click.option(
    "--multi-arch/--no-multi-arch",
    default=True,
    show_default=True,
    help="Build for both amd64 and arm64 architectures (requires Docker buildx)",
)
def build(profile_name: str, multi_arch: bool) -> None:
    build_cmd.run(profile_name, multi_arch)


@cli.command("build-jwt", help="Build and push JWT middleware Docker image to ECR.")
@click.option("--profile", "profile_name", default="default", show_default=True)
def build_jwt(profile_name: str) -> None:
    build_jwt_cmd.run(profile_name)


@cli.command(help="Deploy the stacks for a profile.")
@click.option("--profile", "profile_name", default="default", show_default=True)
def deploy(profile_name: str) -> None:
    deploy_cmd.run(profile_name)


@cli.command(help="Show CloudFormation stack status for a profile.")
@click.option("--profile", "profile_name", default="default", show_default=True)
def status(profile_name: str) -> None:
    status_cmd.run(profile_name)


@cli.command(help="Delete all stacks owned by a profile.")
@click.option("--profile", "profile_name", default="default", show_default=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def destroy(profile_name: str, yes: bool) -> None:
    destroy_cmd.run(profile_name, yes)


@cli.command(help="Build the developer bundle (one per deployment), optionally upload + presign.")
@click.option("--profile", "profile_name", default="default", show_default=True)
@click.option(
    "--outdir",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for the bundle (default: ./dist/<profile-name>-config).",
)
@click.option("--bucket", default=None, help="S3 bucket for upload (optional).")
@click.option("--expires", default=604800, show_default=True, help="Presign TTL, seconds.")
@click.option("--force", is_flag=True, help="Overwrite --outdir even if it was not created by cxwb.")
def distribute(
    profile_name: str, outdir: Path | None, bucket: str | None, expires: int, force: bool
) -> None:
    if outdir is None:
        outdir = Path(f"./dist/{profile_name}-config")
    distribute_cmd.run(profile_name, outdir, bucket, expires, force)


@cli.command("list", help="List saved profiles.")
def list_cmd() -> None:
    names = profile.list_profiles()
    if not names:
        click.echo("No profiles. Run `cxwb init` to create one.")
        return
    for n in names:
        click.echo(n)


def main() -> None:
    cli()
