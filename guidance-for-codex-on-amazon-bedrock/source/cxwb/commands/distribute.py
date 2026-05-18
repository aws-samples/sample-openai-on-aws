"""`cxwb distribute` — build + optionally upload a developer bundle.

One bundle per deployment:
- IdC:              bundle contains the SSO config; every dev uses the same one.
- Gateway (new):    bundle contains the gateway URL + link to self-service key endpoint.
- Gateway (BYO):    same, but pointed at a pre-existing gateway.

Per-user keys are minted by the gateway (LiteLLM `/sso/key/generate` or a
platform-team equivalent). The bundle never contains a key.
"""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

import boto3
import click

from .. import DEFAULT_MODEL, aws, paths, profile


def _build_idc_bundle(p: dict, outdir: Path) -> Path:
    cmd = [
        str(paths.GENERATE_IDC_BUNDLE),
        "--start-url", p["start_url"],
        "--sso-region", p["sso_region"],
        "--account-id", p["account_id"],
        "--permission-set", p["permission_set"],
        "--bedrock-region", p["bedrock_region"],
        "--profile-name", p["codex_profile_name"],
        "--model", p["model"],
        "--outdir", str(outdir),
    ]
    if p.get("otel_endpoint"):
        cmd += ["--otel-endpoint", p["otel_endpoint"]]
    click.echo(f"Running {paths.GENERATE_IDC_BUNDLE.name}...")
    subprocess.run(cmd, check=True)
    return outdir


def _gateway_endpoint_from_stack(p: dict) -> str:
    outs = aws.stack_outputs(p["region"], p["gateway_stack"])
    ep = outs.get("GatewayEndpoint")
    if not ep:
        raise click.ClickException(
            f"stack {p['gateway_stack']} has no GatewayEndpoint output — has it deployed?"
        )
    return ep


def _build_gateway_bundle(p: dict, outdir: Path) -> Path:
    if p["manages_infra"]:
        gateway_url = _gateway_endpoint_from_stack(p)
    else:
        gateway_url = p["gateway_url"]

    cmd = [
        str(paths.GENERATE_GATEWAY_BUNDLE),
        "--gateway-url", gateway_url,
        "--model", p.get("model", DEFAULT_MODEL),
        "--outdir", str(outdir),
    ]
    if p.get("key_mint_url"):
        cmd += ["--key-mint-url", p["key_mint_url"]]
    click.echo(f"Running {paths.GENERATE_GATEWAY_BUNDLE.name}...")
    subprocess.run(cmd, check=True)
    return outdir


def _zip_bundle(bundle_dir: Path) -> Path:
    zip_path = bundle_dir.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in bundle_dir.rglob("*"):
            if f.is_file() and f.name != _SENTINEL:
                zf.write(f, f.relative_to(bundle_dir.parent))
    return zip_path


S3_MAX_PRESIGN = 604800  # 7 days, S3's ceiling for SigV4 presigned URLs.


def _ensure_bucket_exists(bucket: str, region: str) -> None:
    """Create S3 bucket if it doesn't exist, with security best practices."""
    s3 = boto3.client("s3", region_name=region)

    try:
        # Check if bucket exists and is accessible
        s3.head_bucket(Bucket=bucket)
        click.echo(f"✓ S3 bucket exists: s3://{bucket}")
        return
    except s3.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "404":
            # Bucket doesn't exist, create it
            click.echo(f"Creating S3 bucket: s3://{bucket}")
            try:
                if region == "us-east-1":
                    # us-east-1 doesn't need LocationConstraint
                    s3.create_bucket(Bucket=bucket)
                else:
                    s3.create_bucket(
                        Bucket=bucket,
                        CreateBucketConfiguration={"LocationConstraint": region},
                    )

                # Enable versioning (best practice for recovery)
                s3.put_bucket_versioning(
                    Bucket=bucket,
                    VersioningConfiguration={"Status": "Enabled"},
                )

                # Enable server-side encryption (security best practice)
                s3.put_bucket_encryption(
                    Bucket=bucket,
                    ServerSideEncryptionConfiguration={
                        "Rules": [
                            {
                                "ApplyServerSideEncryptionByDefault": {
                                    "SSEAlgorithm": "AES256"
                                }
                            }
                        ]
                    },
                )

                # Block public access (security best practice)
                s3.put_public_access_block(
                    Bucket=bucket,
                    PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    },
                )

                # Add lifecycle rule to expire old bundles after 90 days
                s3.put_bucket_lifecycle_configuration(
                    Bucket=bucket,
                    LifecycleConfiguration={
                        "Rules": [
                            {
                                "ID": "expire-old-bundles",
                                "Status": "Enabled",
                                "Prefix": "",
                                "Expiration": {"Days": 90},
                            }
                        ]
                    },
                )

                # Add tags
                s3.put_bucket_tagging(
                    Bucket=bucket,
                    Tagging={
                        "TagSet": [
                            {"Key": "project", "Value": "codex-bedrock"},
                            {"Key": "purpose", "Value": "developer-bundles"},
                            {"Key": "managed-by", "Value": "cxwb"},
                        ]
                    },
                )

                click.echo(f"✓ Created S3 bucket with security best practices:")
                click.echo(f"  • Versioning enabled (allows recovery)")
                click.echo(f"  • Server-side encryption enabled (AES256)")
                click.echo(f"  • Public access blocked")
                click.echo(f"  • Lifecycle: expire bundles after 90 days")

            except s3.exceptions.BucketAlreadyOwnedByYou:
                # Race condition: bucket was created between check and create
                click.echo(f"✓ S3 bucket exists: s3://{bucket}")
            except Exception as create_error:
                raise click.ClickException(
                    f"Failed to create bucket s3://{bucket}: {create_error}"
                )
        elif error_code == "403":
            # Bucket exists but we don't have access
            raise click.ClickException(
                f"S3 bucket s3://{bucket} exists but you don't have access. "
                f"Check IAM permissions or use a different bucket name."
            )
        else:
            # Other error
            raise click.ClickException(f"Failed to check bucket s3://{bucket}: {e}")


def _upload_and_presign(
    zip_path: Path, bucket: str, region: str, expires: int, profile_name: str
) -> str:
    if expires > S3_MAX_PRESIGN:
        click.echo(f"  clamping --expires to S3 ceiling of {S3_MAX_PRESIGN}s")
        expires = S3_MAX_PRESIGN

    # Ensure bucket exists before uploading
    _ensure_bucket_exists(bucket, region)

    s3 = boto3.client("s3", region_name=region)
    key = f"{profile_name}/{zip_path.name}"
    click.echo(f"\nUploading s3://{bucket}/{key}...")
    s3.upload_file(str(zip_path), bucket, key)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


_SENTINEL = ".cxwb-bundle"


def _prepare_outdir(outdir: Path, force: bool) -> None:
    """Create (or re-create) a bundle output directory.

    Only wipes a directory we created (marked with a sentinel file) unless
    the user passes --force. Refuses to touch filesystem root or $HOME.
    """
    home = Path.home().resolve()
    dangerous = {Path("/"), home, home.parent}
    outdir = outdir.resolve()
    if outdir in dangerous or outdir.parent == outdir:
        raise click.ClickException(f"refusing to use {outdir} as an output directory")

    if outdir.exists():
        if any(outdir.iterdir()):
            if not (outdir / _SENTINEL).exists() and not force:
                raise click.ClickException(
                    f"{outdir} is not empty and was not created by cxwb. "
                    f"Pass --force to overwrite, or choose a different --outdir."
                )
            shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    (outdir / _SENTINEL).write_text("cxwb bundle output — safe to delete\n")


def run(
    profile_name: str,
    outdir: Path,
    bucket: str | None,
    expires: int,
    force: bool,
) -> None:
    p = profile.load(profile_name)
    outdir = outdir.resolve()
    _prepare_outdir(outdir, force)

    if p["auth"] == "idc":
        if not paths.GENERATE_IDC_BUNDLE.exists():
            raise click.ClickException(f"missing: {paths.GENERATE_IDC_BUNDLE}")
        _build_idc_bundle(p, outdir)
        region = p["bedrock_region"]
    elif p["auth"] == "gateway":
        if not paths.GENERATE_GATEWAY_BUNDLE.exists():
            raise click.ClickException(f"missing: {paths.GENERATE_GATEWAY_BUNDLE}")
        _build_gateway_bundle(p, outdir)
        region = p["region"]
    else:
        raise click.ClickException(f"unknown auth: {p.get('auth')!r}")

    zip_path = _zip_bundle(outdir)
    click.echo(f"✓ Bundle created: {zip_path}")

    if bucket:
        url = _upload_and_presign(zip_path, bucket, region, expires, profile_name)
        click.echo(f"\n✓ Presigned URL (expires in {expires}s):\n{url}")
        click.echo(f"\nShare this URL with developers to download the bundle.")

    # Show admin access instructions for gateway deployments
    if p["auth"] == "gateway" and p["manages_infra"]:
        gateway_url = _gateway_endpoint_from_stack(p)
        base_url = gateway_url.rstrip("/v1")

        click.echo("\n" + "="*70)
        click.echo("📊 ADMIN ACCESS TO LITELLM DASHBOARD")
        click.echo("="*70)
        click.echo(f"\nDashboard URL: {base_url}/ui")
        secret_id = f"{p['gateway_stack']}/litellm-master-key"
        click.echo("\nTo retrieve the master key:")
        click.echo(f"  aws secretsmanager get-secret-value \\")
        click.echo(f"    --region {region} \\")
        click.echo(f"    --secret-id {secret_id} \\")
        click.echo(f"    --query SecretString \\")
        click.echo(f"    --output text")
        click.echo("\nOr copy it directly to clipboard (macOS):")
        click.echo(f"  aws secretsmanager get-secret-value \\")
        click.echo(f"    --region {region} \\")
        click.echo(f"    --secret-id {secret_id} \\")
        click.echo(f"    --query SecretString \\")
        click.echo(f"    --output text | pbcopy")
        click.echo("\nThen:")
        click.echo(f"  1. Open {base_url}/ui in your browser")
        click.echo(f"  2. Login with the master key (starts with 'sk-')")
        click.echo(f"  3. Navigate to 'Logs' or 'Analytics' to view usage")
        click.echo("\n💡 Tip: To generate user API keys, navigate to 'Keys' section")
        click.echo("="*70)
    else:
        # Generate suggested bucket name
        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        suggested_bucket = f"codex-bundles-{account_id}-{region}"

        click.echo("\n⚠️  Skipping S3 upload (no --bucket specified).")
        click.echo(f"\nBundle saved locally at: {zip_path}")
        click.echo(f"\nTo upload to S3 and generate a presigned URL:")
        click.echo(f"  uv run cxwb distribute --profile {profile_name} --bucket {suggested_bucket}")
        click.echo(f"\nThe bucket will be created automatically with:")
        click.echo(f"  • Versioning enabled")
        click.echo(f"  • Server-side encryption (AES256)")
        click.echo(f"  • Public access blocked")
        click.echo(f"  • Auto-expire bundles after 90 days")
