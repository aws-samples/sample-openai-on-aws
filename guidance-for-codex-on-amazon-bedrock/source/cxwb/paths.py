"""Repo paths — resolved relative to the installed package."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA_DIR = REPO_ROOT / "deployment" / "infrastructure"
LITELLM_DIR = REPO_ROOT / "deployment" / "litellm"
SCRIPTS_DIR = REPO_ROOT / "deployment" / "scripts"

if not INFRA_DIR.is_dir():
    raise RuntimeError(
        f"cxwb expects to run from the repo checkout; templates not found at {INFRA_DIR}. "
        "Install with `uv sync` inside the repo, not `pip install cxwb` from a wheel."
    )

IDC_TEMPLATE = INFRA_DIR / "bedrock-auth-idc.yaml"
NETWORKING_TEMPLATE = INFRA_DIR / "networking.yaml"
OTEL_TEMPLATE = INFRA_DIR / "otel-collector.yaml"
OTEL_DASHBOARD_TEMPLATE = INFRA_DIR / "codex-otel-dashboard.yaml"
LITELLM_DASHBOARD_TEMPLATE = INFRA_DIR / "litellm-dashboard.yaml"
LITELLM_TEMPLATE = LITELLM_DIR / "ecs" / "litellm-ecs.yaml"
USER_KEY_MAPPING_TEMPLATE = LITELLM_DIR / "ecs" / "user-key-mapping.yaml"

GENERATE_IDC_BUNDLE = SCRIPTS_DIR / "generate-codex-sso-config.sh"
GENERATE_GATEWAY_BUNDLE = SCRIPTS_DIR / "generate-codex-gateway-config.sh"
