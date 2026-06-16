---
name: mysql-er-diagram
description: Use when a developer wants to generate or refresh local Mermaid ER diagrams from an authorized dev/test MySQL or Aurora MySQL database using the local mysql-er-diagram MCP server. Intended for schema documentation only; never use for row-data extraction, arbitrary SQL execution, production reconnaissance, or non-authorized databases.
---

# MySQL ER Diagram

Use this skill to keep local ER diagrams current for authorized backend/database developers working against a dev or test MySQL/Aurora MySQL database.

## Safety Rules

- Use only the `readonly_user` secret or the username configured by `MYSQL_ER_READONLY_USERNAME`.
- The database grant should be `SELECT, SHOW VIEW` on the initial database.
- Query only schema metadata through the `mysql-er-diagram` MCP tools.
- Do not request, write, summarize, or sample table row data.
- Do not log or display credentials, passwords, secret JSON, or connection strings.
- Keep the MCP server local-only over stdio. Do not expose it as a network service.
- Use this only for authorized database documentation/schema visibility.
- Prefer `MYSQL_ER_SECRET_ARN` or `MYSQL_ER_SECRET_NAME` so the local MCP server reads the credential from AWS Secrets Manager instead of a plaintext local password.

## Preferred Workflow

1. Confirm the target is a dev/test database and the configured user is read-only.
2. Use `schema_summary` to verify the target database and table count.
3. Use `generate_er_markdown` to write `er-diagrams/schema-er.md`.
4. Review the generated Mermaid ER diagram for missing foreign keys or unexpected tables.
5. Commit or share only the generated diagram/docs, never secrets.

## Local Server

The MCP server lives at:

```text
mcp/mysql-er-diagram/server.py
```

See:

```text
mcp/mysql-er-diagram/README.md
```

## Supported Outputs

- Mermaid-only `.mmd`
- Markdown `.md` containing a Mermaid ER diagram

## Out Of Scope

- Data profiling
- Row sampling
- Arbitrary SQL execution
- Production database discovery
- Credential management beyond reading a supplied read-only Secrets Manager secret or equivalent local dev secret input
