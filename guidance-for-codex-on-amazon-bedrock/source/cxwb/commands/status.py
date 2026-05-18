"""`cxwb status` — summarize stack state for the active profile."""

from __future__ import annotations

import click

from .. import aws, profile


def stacks_for(p: dict) -> tuple[str, list[str]]:
    if not p["manages_infra"]:
        return p["region"], []
    if p["auth"] == "idc":
        return p["bedrock_region"], [p["stack_name"]]
    if p["auth"] == "gateway":
        stacks = [p["networking_stack"], p["gateway_stack"]]
        if p.get("enable_oidc"):
            stacks.insert(1, p["user_key_mapping_stack"])
        return p["region"], stacks
    raise click.ClickException(f"unknown auth: {p['auth']!r}")


def run(profile_name: str) -> None:
    p = profile.load(profile_name)
    region, stacks = stacks_for(p)
    click.echo(f"Region: {region}")
    if not stacks:
        click.echo("  (external gateway — no stacks owned by this profile)")
        return
    for name in stacks:
        status = aws.stack_exists(region, name) or "DOES_NOT_EXIST"
        click.echo(f"  {name}: {status}")
