#!/usr/bin/env python3

import glob
import logging
import os
import sys
import threading
import time
from typing import Iterable

from aws_bedrock_token_generator import provide_token

LOGGER = logging.getLogger("bedrock-mantle-refresh")
DEFAULT_REGION = "us-east-1"
DEFAULT_REFRESH_INTERVAL_SECONDS = 300
DEFAULT_FAILURE_RETRY_SECONDS = 30
PRISMA_QUERY_ENGINE_CANDIDATES = (
    "query-engine-debian-openssl-3.0.x",
    "query-engine-linux-musl-openssl-3.0.x",
    "query-engine-debian-openssl-1.1.x",
    "query-engine-linux-musl",
)


def _coerce_positive_int(raw_value: str | None, default: int) -> int:
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        LOGGER.warning("Invalid integer value %r, using default %s", raw_value, default)
        return default
    if value <= 0:
        LOGGER.warning("Non-positive integer value %r, using default %s", raw_value, default)
        return default
    return value


def _unset_blank_aws_credentials() -> None:
    for env_name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        if os.environ.get(env_name, "").strip() == "":
            os.environ.pop(env_name, None)


def _resolve_region() -> str:
    return (
        os.environ.get("BEDROCK_MANTLE_REGION")
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or DEFAULT_REGION
    )


def _configure_prisma_runtime() -> None:
    prisma_home_dir = os.environ.get("PRISMA_HOME_DIR") or os.environ.get("HOME") or "/home/appuser"
    os.environ["PRISMA_HOME_DIR"] = prisma_home_dir

    if os.environ.get("PRISMA_QUERY_ENGINE_BINARY"):
        return

    search_root = os.path.join(prisma_home_dir, ".cache", "prisma-python")
    for candidate in PRISMA_QUERY_ENGINE_CANDIDATES:
        matches = glob.glob(
            os.path.join(
                search_root,
                "binaries",
                "*",
                "*",
                "node_modules",
                "prisma",
                candidate,
            )
        )
        for match in matches:
            if os.path.isfile(match) and os.access(match, os.X_OK):
                os.environ["PRISMA_QUERY_ENGINE_BINARY"] = match
                LOGGER.info("Using Prisma query engine binary at %s", match)
                return

    LOGGER.warning(
        "Could not find a Prisma query engine binary under %s; LiteLLM will fall back to its default Prisma resolution",
        search_root,
    )


def _refresh_bedrock_token() -> None:
    _unset_blank_aws_credentials()
    region = _resolve_region()
    os.environ["BEDROCK_MANTLE_REGION"] = region
    os.environ["AWS_REGION"] = region
    os.environ["AWS_DEFAULT_REGION"] = region

    token = provide_token()
    if not token:
        raise RuntimeError("aws-bedrock-token-generator returned an empty token")

    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = token
    # Keep the legacy env in sync for any LiteLLM internals that still read it.
    os.environ["BEDROCK_MANTLE_API_KEY"] = token


def _validate_proxy_args(args: Iterable[str]) -> None:
    args = list(args)
    if "--run_gunicorn" in args or "--run_hypercorn" in args or "--run_granian" in args:
        raise SystemExit(
            "This reference wrapper only supports the default single-process LiteLLM server mode."
        )

    if "--num_workers" in args:
        index = args.index("--num_workers")
        if index + 1 >= len(args):
            raise SystemExit("--num_workers requires a value")
        if args[index + 1] != "1":
            raise SystemExit(
                "This reference wrapper requires --num_workers 1 so token refresh stays in-process."
            )


def _token_refresh_loop(refresh_interval_seconds: int, failure_retry_seconds: int) -> None:
    while True:
        try:
            _refresh_bedrock_token()
            time.sleep(refresh_interval_seconds)
        except Exception:
            LOGGER.exception("Failed to refresh the Bedrock Mantle bearer token")
            time.sleep(failure_retry_seconds)


def main(argv: list[str]) -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    _validate_proxy_args(argv)

    refresh_interval_seconds = _coerce_positive_int(
        os.environ.get("BEDROCK_TOKEN_REFRESH_INTERVAL_SECONDS"),
        DEFAULT_REFRESH_INTERVAL_SECONDS,
    )
    failure_retry_seconds = _coerce_positive_int(
        os.environ.get("BEDROCK_TOKEN_REFRESH_FAILURE_RETRY_SECONDS"),
        DEFAULT_FAILURE_RETRY_SECONDS,
    )

    _configure_prisma_runtime()
    _refresh_bedrock_token()
    LOGGER.info("Initialized refreshable Bedrock Mantle bearer token for region %s", _resolve_region())

    refresher = threading.Thread(
        target=_token_refresh_loop,
        args=(refresh_interval_seconds, failure_retry_seconds),
        daemon=True,
        name="bedrock-mantle-token-refresh",
    )
    refresher.start()

    from litellm.proxy.proxy_cli import run_server as litellm_proxy_cli

    litellm_proxy_cli.main(args=argv, prog_name="litellm", standalone_mode=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
