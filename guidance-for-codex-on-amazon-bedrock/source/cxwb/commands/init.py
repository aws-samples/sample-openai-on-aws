"""`cxwb init` — interactive profile wizard for IdC or Gateway."""

from __future__ import annotations

import re

import click
import questionary

from .. import DEFAULT_MODEL, LITELLM_RECOMMENDED_VERSION, LITELLM_STABLE_VERSIONS, profile

BEDROCK_REGIONS = ["us-east-1", "us-east-2", "us-west-2"]


def _text(prompt: str, default: str = "", validate=None) -> str:
    answer = questionary.text(prompt, default=default, validate=validate).ask()
    if answer is None:
        raise click.Abort()
    return answer.strip()


def _select(prompt: str, choices: list[str], default: str | None = None) -> str:
    answer = questionary.select(prompt, choices=choices, default=default).ask()
    if answer is None:
        raise click.Abort()
    return answer


def _confirm(prompt: str, default: bool = False) -> bool:
    answer = questionary.confirm(prompt, default=default).ask()
    if answer is None:
        raise click.Abort()
    return answer


def _idc_common() -> dict:
    data = {
        "start_url": _text(
            "IdC start URL (e.g. https://d-xxxxxxxxxx.awsapps.com/start):",
            validate=lambda v: v.startswith("https://") or "must start with https://",
        ),
        "sso_region": _text("IdC home region (e.g. us-east-1):", default="us-east-1"),
        "account_id": _text(
            "AWS account ID holding the Bedrock role:",
            validate=lambda v: bool(re.fullmatch(r"\d{12}", v)) or "12 digits",
        ),
        "permission_set": _text("Permission set name:", default="CodexBedrockUser"),
        "bedrock_region": _select(
            "Bedrock region:", BEDROCK_REGIONS, default="us-west-2"
        ),
        "model": _text("Default Codex model:", default=DEFAULT_MODEL),
        "codex_profile_name": _text(
            "Codex profile name (written into ~/.codex/config.toml):",
            default="codex",
        ),
    }
    if _confirm("Send Codex telemetry to an OTel endpoint?", default=False):
        data["otel_endpoint"] = _text("OTel endpoint URL:", default="")
    else:
        data["otel_endpoint"] = ""
    return data


def _idc_flow() -> dict:
    click.echo("\nIAM Identity Center — deploy Bedrock role + policy.\n")
    return {
        "auth": "idc",
        "manages_infra": True,
        "stack_name": _text("CloudFormation stack name:", default="codex-bedrock-idc"),
        **_idc_common(),
    }


def _existing_idc_flow() -> dict:
    click.echo("\nExisting IdC deployment — bundle-only.\n")
    click.echo(
        "Assumes you already have: a Bedrock-invoke IAM role trusted by "
        "sso.amazonaws.com and attached to a permission set in your IdC instance.\n"
    )
    return {
        "auth": "idc",
        "manages_infra": False,
        **_idc_common(),
    }


def _existing_gateway_flow() -> dict:
    click.echo("\nExisting gateway — no deploy, distribute only.\n")
    return {
        "auth": "gateway",
        "manages_infra": False,
        "gateway_url": _text(
            "Gateway base URL (include /v1, e.g. https://gw.example.com/v1):",
            validate=lambda v: v.startswith(("http://", "https://")) or "must be an http(s) URL",
        ),
        "key_mint_url": _text(
            "Self-service key endpoint (optional, leave blank if you hand out keys manually):",
            default="",
        ),
        "model": _text("Default model alias on this gateway:", default=DEFAULT_MODEL),
        "region": _select(
            "AWS region for S3 bundle uploads:", BEDROCK_REGIONS, default="us-west-2"
        ),
    }


def _gateway_flow() -> dict:
    click.echo("\nLiteLLM Gateway path.\n")
    region = _select(
        "AWS region for the gateway:", BEDROCK_REGIONS, default="us-west-2"
    )

    # Image selection
    image_choice = _select(
        "LiteLLM Docker image:",
        choices=[
            "Build automatically from official LiteLLM image (Recommended)",
            "Use existing image from my ECR repository",
        ],
    )

    data: dict = {
        "auth": "gateway",
        "manages_infra": True,
        "region": region,
        "networking_stack": _text(
            "Networking stack name:", default="codex-networking"
        ),
        "gateway_stack": _text("Gateway stack name:", default="codex-litellm-gateway"),
        "allowed_cidr": _text(
            "CIDR allowed to reach the ALB (corporate network CIDR or VPN range, e.g. 10.0.0.0/8):",
            default="10.0.0.0/8"
        ),
        "model": _text("Default model alias:", default=DEFAULT_MODEL),
    }

    # OIDC Configuration (optional)
    enable_oidc = _select(
        "Enable OIDC/SSO self-service key generation?",
        choices=[
            "No - use admin-generated API keys (simpler)",
            "Yes - enable OIDC for self-service (requires IdP setup)",
        ],
    )

    if "Yes" in enable_oidc:
        click.echo("\n📝 OIDC Configuration")
        click.echo("You'll need these from your IdP (Okta, Azure AD, etc.):")
        click.echo("")

        data["enable_oidc"] = True
        data["jwks_url"] = _text(
            "JWKS URL from IdP (e.g., https://your-tenant.okta.com/.well-known/jwks.json):"
        )
        data["jwt_audience"] = _text(
            "JWT Audience claim (optional, press Enter to skip):",
            default="",
        )
        data["jwt_issuer"] = _text(
            "JWT Issuer claim (optional, press Enter to skip):",
            default="",
        )
        data["jwt_ecr_repo_name"] = _text(
            "ECR repository name for JWT middleware:",
            default="codex-jwt-middleware",
        )
        data["user_key_mapping_stack"] = _text(
            "DynamoDB stack name for user-key mapping:",
            default="codex-user-key-mapping",
        )

        click.echo(
            f"\n→ JWT middleware will be built via `cxwb build-jwt` before deploy.\n"
            f"  JWKS URL: {data['jwks_url']}\n"
            f"  Self-service portal will be available at: <gateway-url>/api/my-key"
        )
    else:
        data["enable_oidc"] = False
        data["key_mint_url"] = _text(
            "Self-service key endpoint (optional, leave blank if using admin-generated keys):",
            default="",
        )

    if "Build automatically" in image_choice:
        # Auto-build flow
        data["auto_build"] = True

        # LiteLLM version selection
        version_choice = _select(
            "LiteLLM version:",
            choices=[f"{LITELLM_RECOMMENDED_VERSION} (Recommended)"] +
                    [v for v in LITELLM_STABLE_VERSIONS if v != LITELLM_RECOMMENDED_VERSION],
        )
        # Strip "(Recommended)" suffix if present
        litellm_version = version_choice.replace(" (Recommended)", "")
        data["litellm_version"] = litellm_version

        # ECR repository name
        data["ecr_repo_name"] = _text(
            "ECR repository name for the image:", default="codex-litellm-gateway"
        )

        click.echo(
            f"\n→ Image will be built via `cxwb build` before deploy.\n"
            f"  Base: ghcr.io/berriai/litellm:{litellm_version}\n"
            f"  ECR: {region}/{data['ecr_repo_name']}:{litellm_version}"
        )
    else:
        # Existing image flow
        data["auto_build"] = False
        data["image_uri"] = _text(
            "LiteLLM container image URI (ECR repo:tag):",
            validate=lambda v: "/" in v or "must include a repository path",
        )

    if _confirm("Generate a random LiteLLM master key and DB password now?", True):
        import secrets

        data["master_key"] = "sk-" + secrets.token_hex(16)
        data["db_password"] = secrets.token_hex(16)
    else:
        data["master_key"] = _text("LiteLLM master key (sk-...):")
        data["db_password"] = _text("RDS master password:")
    return data


def run() -> None:
    click.echo("cxwb init — configure a deployment profile.\n")
    choice = _select(
        "Deployment path:",
        choices=[
            "IAM Identity Center — deploy new (recommended)",
            "IAM Identity Center — existing (BYO role + permission set)",
            "LiteLLM Gateway — deploy new",
            "Gateway — existing (BYO LiteLLM / Portkey / Kong AI / ...)",
        ],
    )
    flows = {
        "IAM Identity Center — deploy new (recommended)": _idc_flow,
        "IAM Identity Center — existing (BYO role + permission set)": _existing_idc_flow,
        "LiteLLM Gateway — deploy new": _gateway_flow,
        "Gateway — existing (BYO LiteLLM / Portkey / Kong AI / ...)": _existing_gateway_flow,
    }
    data = flows[choice]()

    name = _text("\nProfile name:", default="default")
    saved = profile.save(name, data)
    click.echo(f"\nSaved profile to {saved}")
    if data["manages_infra"]:
        # If auto_build is enabled, user needs to build image first
        if data.get("auto_build"):
            click.echo(f"Next: uv run cxwb build --profile {name}")
        # If OIDC is enabled, user needs to build JWT middleware first
        elif data.get("enable_oidc"):
            click.echo(f"Next: uv run cxwb build-jwt --profile {name}")
        else:
            click.echo(f"Next: uv run cxwb deploy --profile {name}")
    else:
        click.echo(f"Next: uv run cxwb distribute --profile {name} --bucket <bucket>")
