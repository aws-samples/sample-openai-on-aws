"""`cxwb deploy` — create/update CloudFormation stacks for the active profile."""

from __future__ import annotations

import click

from .. import aws, paths, profile


def _deploy_idc(p: dict) -> None:
    region = p["bedrock_region"]
    click.echo(f"Deploying IdC Bedrock auth stack in {region}...")
    outputs = aws.deploy_stack(
        region=region,
        name=p["stack_name"],
        template=paths.IDC_TEMPLATE,
        parameters={},
        capabilities=["CAPABILITY_NAMED_IAM"],
    )
    click.echo("\nStack outputs:")
    for k, v in outputs.items():
        click.echo(f"  {k} = {v}")
    click.echo(
        "\nNext: attach the customer-managed policy to your `"
        f"{p['permission_set']}` permission set in IAM Identity Center, then run:"
        f"\n  cxwb distribute --profile <profile>"
    )


def _deploy_gateway(p: dict) -> None:
    region = p["region"]

    # Check if image_uri exists (required for deployment)
    if "image_uri" not in p or not p["image_uri"]:
        if p.get("auto_build"):
            click.echo(
                "❌ No Docker image URI found. Run `cxwb build` first to build the LiteLLM image.",
                err=True,
            )
            raise click.ClickException("Missing image_uri — run `cxwb build` first")
        else:
            click.echo(
                "❌ No Docker image URI found in profile. "
                "Re-run `cxwb init` and provide an existing image URI.",
                err=True,
            )
            raise click.ClickException("Missing image_uri in profile")

    click.echo(f"Deploying networking stack in {region}...")
    aws.deploy_stack(
        region=region,
        name=p["networking_stack"],
        template=paths.NETWORKING_TEMPLATE,
        parameters={},
        capabilities=["CAPABILITY_IAM"],
    )

    # Deploy OTel collector (if Central or Hybrid mode)
    monitoring = p.get("monitoring", {})
    monitoring_mode = monitoring.get("mode", "none")
    if monitoring_mode in ["central", "hybrid"]:
        click.echo("\nDeploying OTel collector stack...")
        net_outputs = aws.stack_outputs(region, p["networking_stack"])
        aws.deploy_stack(
            region=region,
            name=p["otel_stack"],
            template=paths.OTEL_TEMPLATE,
            parameters={
                "VpcId": net_outputs["VpcId"],
                "SubnetIds": net_outputs["SubnetIds"],
            },
            capabilities=["CAPABILITY_IAM"],
        )

    # Deploy DynamoDB table for JWT middleware (if OIDC enabled)
    if p.get("enable_oidc"):
        click.echo("\nDeploying DynamoDB table for user-key mapping...")
        aws.deploy_stack(
            region=region,
            name=p["user_key_mapping_stack"],
            template=paths.USER_KEY_MAPPING_TEMPLATE,
            parameters={
                "TableName": "codex-user-keys",
            },
            capabilities=[],
        )

    click.echo("\nDeploying LiteLLM gateway stack...")

    # Build parameters for gateway stack
    gateway_params = {
        "NetworkingStackName": p["networking_stack"],
        "EnableOtel": "true" if monitoring_mode in ["central", "hybrid"] else "false",
        "AwsRegion": region,
        "LiteLLMImage": p["image_uri"],
        "LiteLLMMasterKey": p["master_key"],
        "DBPassword": p["db_password"],
        "AllowedCidr": p["allowed_cidr"],
    }

    # Add OTel stack name if enabled
    if monitoring_mode in ["central", "hybrid"]:
        gateway_params["OtelStackName"] = p["otel_stack"]

    # Add JWT middleware parameters if OIDC enabled
    if p.get("enable_oidc"):
        if "jwt_middleware_image_uri" not in p:
            click.echo(
                "❌ No JWT middleware image URI found. Run `cxwb build-jwt` first.",
                err=True,
            )
            raise click.ClickException("Missing jwt_middleware_image_uri — run `cxwb build-jwt` first")

        gateway_params.update({
            "EnableJwtMiddleware": "true",
            "JwtMiddlewareImage": p["jwt_middleware_image_uri"],
            "JwksUrl": p["jwks_url"],
            "JwtAudience": p.get("jwt_audience", ""),
            "JwtIssuer": p.get("jwt_issuer", ""),
            "UserKeyMappingStackName": p["user_key_mapping_stack"],
        })
    else:
        gateway_params["EnableJwtMiddleware"] = "false"

    outputs = aws.deploy_stack(
        region=region,
        name=p["gateway_stack"],
        template=paths.LITELLM_TEMPLATE,
        parameters=gateway_params,
        capabilities=["CAPABILITY_IAM"],
    )

    click.echo("\nGateway outputs:")
    for k, v in outputs.items():
        click.echo(f"  {k} = {v}")

    if p.get("enable_oidc"):
        click.echo("\n✅ OIDC enabled - developers can self-generate keys at:")
        gateway_url = outputs.get("GatewayEndpoint", "").rstrip("/v1")
        click.echo(f"  {gateway_url}/api/my-key")

    # Deploy LiteLLM dashboard
    click.echo("\nDeploying CloudWatch dashboard...")
    dashboard_name = "LiteLLMGateway"
    aws.deploy_stack(
        region=region,
        name=f"{p['gateway_stack']}-dashboard",
        template=paths.LITELLM_DASHBOARD_TEMPLATE,
        parameters={
            "DashboardName": dashboard_name,
        },
        capabilities=[],
    )
    click.echo(f"\n✅ Dashboard deployed: {dashboard_name}")
    click.echo(f"   View at: https://console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:name={dashboard_name}")


def run(profile_name: str) -> None:
    p = profile.load(profile_name)
    if not p["manages_infra"]:
        click.echo(
            "Profile does not manage infrastructure — nothing to deploy. "
            "Run `cxwb distribute` to produce the bundle."
        )
        return
    if p["auth"] == "idc":
        _deploy_idc(p)
    elif p["auth"] == "gateway":
        _deploy_gateway(p)
    else:
        raise click.ClickException(f"unknown auth in profile: {p.get('auth')!r}")
