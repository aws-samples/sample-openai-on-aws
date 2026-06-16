#!/usr/bin/env python3
"""Local-only MCP server for read-only MySQL schema ER diagrams."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
import pymysql
from mcp.server.fastmcp import FastMCP


LOGGER = logging.getLogger("mysql-er-diagram")
READONLY_USERNAME = os.environ.get("MYSQL_ER_READONLY_USERNAME", "readonly_user")
IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")

mcp = FastMCP(
    "mysql-er-diagram",
    instructions=(
        "Local-only authorized developer tool. Generates Mermaid ER diagrams "
        "from MySQL INFORMATION_SCHEMA metadata using a read-only database user."
    ),
)


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_ca: str | None


def _aws_region() -> str | None:
    return (
        os.environ.get("MYSQL_ER_AWS_REGION")
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
    )


def _load_secret_from_secrets_manager(secret_id: str) -> dict[str, Any]:
    client_kwargs: dict[str, Any] = {}
    region = _aws_region()
    if region:
        client_kwargs["region_name"] = region

    client = boto3.client("secretsmanager", **client_kwargs)
    response = client.get_secret_value(SecretId=secret_id)
    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError("Secrets Manager secret did not contain SecretString.")
    return json.loads(secret_string)


def _load_secret() -> dict[str, Any]:
    secret_id = os.environ.get("MYSQL_ER_SECRET_ARN") or os.environ.get("MYSQL_ER_SECRET_NAME")
    secret_json = os.environ.get("MYSQL_ER_SECRET_JSON")
    secret_file = os.environ.get("MYSQL_ER_SECRET_FILE")

    if secret_id:
        return _load_secret_from_secrets_manager(secret_id)

    if secret_json:
        return json.loads(secret_json)

    if secret_file:
        with open(secret_file, "r", encoding="utf-8") as handle:
            return json.load(handle)

    password = os.environ.get("MYSQL_ER_PASSWORD")
    if password:
        return {"username": READONLY_USERNAME, "password": password}

    raise RuntimeError(
        "Missing readonly credentials. Set MYSQL_ER_SECRET_ARN, "
        "MYSQL_ER_SECRET_NAME, MYSQL_ER_SECRET_JSON, "
        "MYSQL_ER_SECRET_FILE, or MYSQL_ER_PASSWORD."
    )


def _require_identifier(value: str, label: str) -> str:
    if not IDENTIFIER_RE.match(value):
        raise ValueError(f"{label} must be a simple MySQL identifier.")
    return value


def _config(database: str | None = None) -> DbConfig:
    secret = _load_secret()
    username = secret.get("username")
    password = secret.get("password")

    if username != READONLY_USERNAME:
        raise RuntimeError(
            f"This MCP server only allows the configured read-only user "
            f"{READONLY_USERNAME!r}."
        )
    if not password:
        raise RuntimeError("Read-only secret is missing a password value.")
    ssl_ca = os.environ.get("MYSQL_ER_SSL_CA")
    if not ssl_ca:
        raise RuntimeError(
            "MYSQL_ER_SSL_CA is required. Set it to an AWS RDS CA bundle path so "
            "the MCP server verifies the Aurora/MySQL server certificate."
        )
    ssl_ca_path = Path(ssl_ca).expanduser()
    if not ssl_ca_path.exists():
        raise RuntimeError(
            f"MYSQL_ER_SSL_CA does not exist: {ssl_ca}. Provide a valid AWS RDS "
            "CA bundle path."
        )

    db_name = database or os.environ.get("MYSQL_ER_DATABASE", "")
    return DbConfig(
        host=os.environ["MYSQL_ER_HOST"],
        port=int(os.environ.get("MYSQL_ER_PORT", "3306")),
        database=_require_identifier(db_name, "database"),
        username=username,
        password=password,
        ssl_ca=str(ssl_ca_path),
    )


def _connect(config: DbConfig):
    connect_args: dict[str, Any] = {
        "host": config.host,
        "port": config.port,
        "user": config.username,
        "password": config.password,
        "database": "information_schema",
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "read_timeout": 15,
        "write_timeout": 15,
        "connect_timeout": 10,
        "autocommit": True,
        "ssl_ca": config.ssl_ca,
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
    }
    return pymysql.connect(**connect_args)


def _fetch_schema(config: DbConfig) -> dict[str, Any]:
    """Fetch schema metadata only from INFORMATION_SCHEMA."""
    with _connect(config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TABLE_NAME, TABLE_TYPE, ENGINE, TABLE_COMMENT
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
                """,
                (config.database,),
            )
            tables = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    TABLE_NAME,
                    COLUMN_NAME,
                    ORDINAL_POSITION,
                    COLUMN_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY,
                    COLUMN_DEFAULT,
                    EXTRA,
                    COLUMN_COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
                """,
                (config.database,),
            )
            columns = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    TABLE_NAME,
                    INDEX_NAME,
                    NON_UNIQUE,
                    SEQ_IN_INDEX,
                    COLUMN_NAME
                FROM INFORMATION_SCHEMA.STATISTICS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
                """,
                (config.database,),
            )
            indexes = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    kcu.CONSTRAINT_NAME,
                    kcu.TABLE_NAME,
                    kcu.COLUMN_NAME,
                    kcu.REFERENCED_TABLE_NAME,
                    kcu.REFERENCED_COLUMN_NAME,
                    rc.UPDATE_RULE,
                    rc.DELETE_RULE
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                LEFT JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                    ON rc.CONSTRAINT_SCHEMA = kcu.CONSTRAINT_SCHEMA
                    AND rc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                    AND rc.TABLE_NAME = kcu.TABLE_NAME
                WHERE kcu.TABLE_SCHEMA = %s
                  AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY kcu.TABLE_NAME, kcu.CONSTRAINT_NAME, kcu.ORDINAL_POSITION
                """,
                (config.database,),
            )
            foreign_keys = cursor.fetchall()

    return {
        "database": config.database,
        "tables": tables,
        "columns": columns,
        "indexes": indexes,
        "foreign_keys": foreign_keys,
    }


def _group_by(items: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(str(item[key]), []).append(item)
    return grouped


def _mermaid_type(column_type: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", column_type.upper()).strip("_") or "UNKNOWN"


def render_mermaid(schema: dict[str, Any], include_indexes: bool = False) -> str:
    columns_by_table = _group_by(schema["columns"], "TABLE_NAME")
    indexes_by_table = _group_by(schema["indexes"], "TABLE_NAME")
    lines = ["erDiagram"]

    for table in schema["tables"]:
        table_name = table["TABLE_NAME"]
        lines.append(f"  {table_name} {{")
        for column in columns_by_table.get(table_name, []):
            markers = []
            if column.get("COLUMN_KEY") == "PRI":
                markers.append("PK")
            elif column.get("COLUMN_KEY") == "UNI":
                markers.append("UK")

            suffix = " ".join(markers)
            column_type = _mermaid_type(str(column["COLUMN_TYPE"]))
            column_name = column["COLUMN_NAME"]
            lines.append(f"    {column_type} {column_name} {suffix}".rstrip())

        if include_indexes:
            for index in indexes_by_table.get(table_name, []):
                index_name = index["INDEX_NAME"]
                index_col = index["COLUMN_NAME"]
                unique = "UNIQUE" if index["NON_UNIQUE"] == 0 else "INDEX"
                lines.append(f"    string idx_{index_name}_{index_col} {unique}")

        lines.append("  }")

    for fk in schema["foreign_keys"]:
        child_table = fk["TABLE_NAME"]
        parent_table = fk["REFERENCED_TABLE_NAME"]
        child_column = fk["COLUMN_NAME"]
        parent_column = fk["REFERENCED_COLUMN_NAME"]
        label = f"{child_column} references {parent_column}"
        lines.append(f'  {child_table} }}o--|| {parent_table} : "{label}"')

    return "\n".join(lines) + "\n"


def render_markdown(schema: dict[str, Any], mermaid: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    tables = schema["tables"]
    foreign_keys = schema["foreign_keys"]
    return (
        f"# MySQL ER Diagram - {schema['database']}\n\n"
        f"Generated: `{now}`\n\n"
        "Scope: schema metadata only from `INFORMATION_SCHEMA`. "
        "No table row data is queried or written.\n\n"
        f"- Tables/views: {len(tables)}\n"
        f"- Foreign keys: {len(foreign_keys)}\n\n"
        "```mermaid\n"
        f"{mermaid}"
        "```\n"
    )


def _safe_output_path(output_path: str) -> Path:
    path = Path(output_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@mcp.tool()
def schema_summary(database: str | None = None) -> dict[str, Any]:
    """Return table, column, index, and FK counts for the initial database."""
    config = _config(database)
    schema = _fetch_schema(config)
    return {
        "database": schema["database"],
        "table_count": len(schema["tables"]),
        "column_count": len(schema["columns"]),
        "index_count": len(schema["indexes"]),
        "foreign_key_count": len(schema["foreign_keys"]),
        "tables": [table["TABLE_NAME"] for table in schema["tables"]],
    }


@mcp.tool()
def generate_er_markdown(
    output_path: str = "er-diagrams/schema-er.md",
    database: str | None = None,
    include_indexes: bool = False,
) -> dict[str, Any]:
    """Generate a local Markdown file containing a Mermaid ER diagram."""
    config = _config(database)
    schema = _fetch_schema(config)
    mermaid = render_mermaid(schema, include_indexes=include_indexes)
    markdown = render_markdown(schema, mermaid)
    path = _safe_output_path(output_path)
    path.write_text(markdown, encoding="utf-8")
    return {
        "database": schema["database"],
        "output_path": str(path),
        "table_count": len(schema["tables"]),
        "foreign_key_count": len(schema["foreign_keys"]),
    }


@mcp.tool()
def generate_mermaid(
    output_path: str = "er-diagrams/schema-er.mmd",
    database: str | None = None,
    include_indexes: bool = False,
) -> dict[str, Any]:
    """Generate a local Mermaid .mmd file from INFORMATION_SCHEMA metadata."""
    config = _config(database)
    schema = _fetch_schema(config)
    mermaid = render_mermaid(schema, include_indexes=include_indexes)
    path = _safe_output_path(output_path)
    path.write_text(mermaid, encoding="utf-8")
    return {
        "database": schema["database"],
        "output_path": str(path),
        "table_count": len(schema["tables"]),
        "foreign_key_count": len(schema["foreign_keys"]),
    }


def cli() -> None:
    parser = argparse.ArgumentParser(description="Generate a local Mermaid ER diagram.")
    parser.add_argument("--database", help="Database/schema name. Defaults to MYSQL_ER_DATABASE.")
    parser.add_argument("--output", default="er-diagrams/schema-er.md")
    parser.add_argument("--mermaid-only", action="store_true")
    parser.add_argument("--include-indexes", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=os.environ.get("MYSQL_ER_LOG_LEVEL", "WARNING"))
    config = _config(args.database)
    schema = _fetch_schema(config)
    mermaid = render_mermaid(schema, include_indexes=args.include_indexes)
    content = mermaid if args.mermaid_only else render_markdown(schema, mermaid)
    path = _safe_output_path(args.output)
    path.write_text(content, encoding="utf-8")
    print(json.dumps({"database": schema["database"], "output_path": str(path)}))


def main() -> None:
    if os.environ.get("MYSQL_ER_CLI") == "1":
        cli()
    else:
        logging.basicConfig(level=os.environ.get("MYSQL_ER_LOG_LEVEL", "WARNING"))
        mcp.run()
