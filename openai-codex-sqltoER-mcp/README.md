# Codex MySQL Schema Visibility and ER Diagram Toolkit

This project exists to make life easier for backend software engineers and
database developers using the Codex app. Its main goal is to give developers a
simple, repeatable way to connect Codex to a dev/test MySQL or Aurora MySQL
database, stay current on schema changes, and clearly understand table
structure and relationships through local ER diagrams.

Instead of manually inspecting tables, foreign keys, and database structure,
developers can use a local-only MCP server that reads schema metadata from
`INFORMATION_SCHEMA` and generates Mermaid or Markdown artifacts that Codex and
humans can both work with comfortably.

## Start Here

If you already have a dev/test MySQL or Aurora MySQL database, you can skip the
CloudFormation setup and go straight to [Codex App MCP Configuration](#codex-app-mcp-configuration).

The CloudFormation stack in this repo is mainly for testing, demo setup, or for
cases where you want a disposable Aurora environment to validate the MCP and ER
diagram flow end to end.

Important:

- if you already have a dev/test database, you usually do not need the CloudFormation stack
- if you do use the CloudFormation stack, you must explicitly provide your own
  desktop public `/24` egress CIDR at deploy time
- run the shell examples from this project directory unless a command says
  otherwise, because the examples use relative paths and `$(pwd)`
- the deploy script defaults to AWS profile `mcp` and region `us-west-2`; set
  `AWS_PROFILE_NAME` and `AWS_REGION_NAME` when you want to use a different
  profile or region
- the local MCP server requires `MYSQL_ER_SSL_CA` and refuses unverified TLS
  connections

## Prerequisites

Before using the CloudFormation test stack or the local MCP server, make sure
these tools are available:

- AWS CLI configured with a profile that can create CloudFormation, Aurora,
  Lambda, Secrets Manager, VPC, IAM, and CloudWatch Logs resources
- Python 3
- `uvx`

Install `uv` if needed so `uvx` is available:

```sh
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Why This Project Exists

Backend and database developers often need a fast answer to questions like:

- what tables exist in this database right now?
- how are they related?
- what foreign keys connect one part of the schema to another?
- what changed since the last time I looked?

This project is designed to reduce that friction. The CloudFormation stack
creates a safe dev/test environment and a tightly scoped read-only database
user. The local MCP server gives Codex a reliable way to inspect schema
metadata and generate fresh ER diagrams without exposing row data or requiring
broad database permissions.

## What This Repo Contains

- `cloudformation/aurora-mysql-test-db.yaml`: Aurora MySQL stack with a
  Lambda-backed custom resource that bootstraps a read-only user and test tables.
- `cloudformation/deploy-aurora-mysql-test-db.sh`: helper script to deploy or
  delete the stack. By default it uses the `mcp` AWS profile and `us-west-2`
  region, and both can be overridden with environment variables.
- `mcp/mysql-er-diagram`: local MCP server package that reads
  `INFORMATION_SCHEMA` and writes Mermaid or Markdown ER diagrams.
- `er-diagrams/`: generated local diagram output.
- `lambda-layers/pymysql`: dependency source for the PyMySQL Lambda layer used
  by the CloudFormation custom resource.

## Architecture

The stack creates:

- an Aurora MySQL cluster and instance
- a generated master secret in AWS Secrets Manager
- a generated `readonly_user` secret in AWS Secrets Manager
- a Lambda-backed custom resource that:
  - creates or updates the read-only user
  - grants `SELECT, SHOW VIEW` on the initial database by default
  - creates three test tables for ER diagram validation:
    - `teams`
    - `applications`, with `team_id` referencing `teams.team_id`
    - `deployments`, with `application_id` referencing `applications.application_id`
- a CloudWatch log group for the custom resource Lambda

The MCP server then connects with the read-only secret, queries only
`INFORMATION_SCHEMA`, and writes local ER diagrams without reading row data.
That gives developers and Codex a current map of the schema, not just a static
document that drifts out of date.

## Quick Start

If you already have a dev/test database, skip to
[Codex App MCP Configuration](#codex-app-mcp-configuration), set the required
environment values, and point Codex at your existing database.

Start from this project directory:

```sh
cd /path/to/openai-codex-sqltoER-mcp
```

If you need a disposable database for testing this project, deploy the Aurora
test stack. The script defaults to profile `mcp` and region `us-west-2`:

```sh
bash cloudformation/deploy-aurora-mysql-test-db.sh
```

To use a different AWS profile or region, override the script defaults:

```sh
AWS_PROFILE_NAME=your-profile \
AWS_REGION_NAME=us-west-2 \
STACK_NAME=sql-to-erdiag-codex \
bash cloudformation/deploy-aurora-mysql-test-db.sh
```

Delete the stack later with the same profile, region, and stack name:

```sh
AWS_PROFILE_NAME=your-profile \
AWS_REGION_NAME=us-west-2 \
STACK_NAME=sql-to-erdiag-codex \
bash cloudformation/deploy-aurora-mysql-test-db.sh --delete
```

Keep the same network, VPN, or hotspot between stack deployment and ER diagram
generation. The stack allows MySQL access only from the public `/24` egress
pool detected during deployment. If your public egress IP changes, the MCP
server may time out while connecting to Aurora; rerun the deploy command with
the same stack name to refresh the allowed CIDR.

Generate an ER diagram locally. Set `AWS_PROFILE` to the same profile you used
for deployment; for the default deploy script, this is `mcp`.

```sh
export MYSQL_ER_MCP_DIR="$(pwd)/mcp/mysql-er-diagram"
export AWS_PROFILE="mcp"
export AWS_REGION="us-west-2"
export STACK_NAME="sql-to-erdiag-codex"

export MYSQL_ER_HOST="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='DbClusterEndpoint'].OutputValue | [0]" \
  --output text)"

export MYSQL_ER_PORT="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='DbClusterPort'].OutputValue | [0]" \
  --output text)"

export MYSQL_ER_DATABASE="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='DatabaseName'].OutputValue | [0]" \
  --output text)"

export MYSQL_ER_SECRET_ARN="$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ReadOnlySecretArn'].OutputValue | [0]" \
  --output text)"

export MYSQL_ER_READONLY_USERNAME="readonly_user"
export MYSQL_ER_SSL_CA="$(pwd)/mcp/mysql-er-diagram/us-west-2-bundle.pem"

MYSQL_ER_CLI=1 uvx --from "$MYSQL_ER_MCP_DIR" mysql-er-diagram-mcp \
  --output er-diagrams/schema-er.md
```

Generate Mermaid only:

```sh
MYSQL_ER_CLI=1 uvx --from "$MYSQL_ER_MCP_DIR" mysql-er-diagram-mcp \
  --mermaid-only \
  --output er-diagrams/schema-er.mmd
```

## CloudFormation Stack

This section is optional. It exists to help you stand up a disposable dev/test
Aurora environment for validating the MCP server and ER diagram generation
flow.

If your team already has a deployed dev/test MySQL or Aurora database, you do
not need this stack. You can go directly to
[Codex App MCP Configuration](#codex-app-mcp-configuration) and use your
existing database endpoint and read-only credentials.

Main template:

```text
cloudformation/aurora-mysql-test-db.yaml
```

The deploy script:

- uses the `mcp` profile from `~/.aws/credentials` by default
- uses `us-west-2` by default
- derives default VPC public subnet inputs
- computes your public desktop egress pool from `https://checkip.amazonaws.com`
- publishes the PyMySQL Lambda layer
- deploys the stack in one command

Default deployment:

```sh
bash cloudformation/deploy-aurora-mysql-test-db.sh
```

Optional overrides:

```sh
AWS_PROFILE_NAME=your-profile \
AWS_REGION_NAME=us-west-2 \
STACK_NAME=sql-to-erdiag-codex \
bash cloudformation/deploy-aurora-mysql-test-db.sh
```

If the script is marked executable in your checkout, you can run it directly as
`cloudformation/deploy-aurora-mysql-test-db.sh`. Using `bash` works either way.

## Public Access Model

This dev/test stack sets the Aurora instance to `PubliclyAccessible: true`, but
the database security group allows inbound MySQL only from:

- the custom resource Lambda security group
- the configured desktop `/24` egress pool

The deploy script computes this CIDR from your current public egress IP each
time it runs:

```sh
curl -fsS https://checkip.amazonaws.com | awk -F. '{print $1 "." $2 "." $3 ".0/24"}'
```

For safety, the CloudFormation template does not include a real default for
`DesktopEgressPoolCidr`. If you deploy the template directly instead of using
the helper script, you must provide an explicit value at deployment time.

If ER diagram generation fails with a MySQL connection timeout, check whether
your network, VPN, or hotspot changed after deployment. Rerunning the deploy
script with the same stack name updates the configured desktop `/24` egress
pool.

## Observability

The custom resource Lambda logs create, update, and delete requests, database
connection success, grant operations, and CloudFormation response submission.
It never logs passwords or secret values.

The Lambda sends the custom resource completion signal back to CloudFormation by
issuing an HTTP `PUT` to the stack-provided `ResponseURL`. On success it sends
`SUCCESS`; on failure it sends `FAILED`, so the stack does not silently hang.

## MCP Server

The local MCP server lives here:

```text
mcp/mysql-er-diagram
```

Safeguards:

- is intended to run with a database user that has read-only grants, typically
  `readonly_user`
- the actual read-only guarantee comes from the database grants on that user,
  not from the MCP process itself
- intended grant is `SELECT, SHOW VIEW` on the initial database only
- queries only:
  - `INFORMATION_SCHEMA.TABLES`
  - `INFORMATION_SCHEMA.COLUMNS`
  - `INFORMATION_SCHEMA.STATISTICS`
  - `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`
  - `INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS`
- writes local Mermaid `.mmd` or Markdown `.md` output
- does not execute raw SQL from users
- does not read table row data
- does not log credentials
- runs over local stdio only

Available MCP tools:

- `schema_summary`
- `generate_er_markdown`
- `generate_mermaid`

In practice, this means a developer can ask Codex for a current schema summary
or a refreshed ER diagram and get an answer based on live metadata from the
database they are actively building against.

Do not point this MCP server at an admin or write-capable database secret. Use
the scoped database user created for schema visibility, and rely on the DB
grants to enforce read-only access.

## Codex App MCP Configuration

The Codex desktop app MCP entry should use `uvx`:

```toml
[mcp_servers.mysql-er-diagram]
command = "uvx"
args = [
    "--from",
    "<PROJECT_ROOT>/mcp/mysql-er-diagram",
    "mysql-er-diagram-mcp",
]

[mcp_servers.mysql-er-diagram.env]
AWS_PROFILE = "mcp"
AWS_REGION = "us-west-2"
MYSQL_ER_HOST = "your-aurora-endpoint"
MYSQL_ER_PORT = "3306"
MYSQL_ER_DATABASE = "workshop"
MYSQL_ER_READONLY_USERNAME = "readonly_user"
MYSQL_ER_SECRET_ARN = "arn:aws:secretsmanager:us-west-2:123456789012:secret:readonly-secret"
MYSQL_ER_SSL_CA = "<PROJECT_ROOT>/mcp/mysql-er-diagram/us-west-2-bundle.pem"
```

After updating `~/.codex/config.toml`, restart Codex or reload its MCP/config
state.

Replace `<PROJECT_ROOT>` with the local filesystem path where you cloned this
project.

`MYSQL_ER_SSL_CA` is required. The MCP server fails closed if the CA bundle is
missing so Aurora/MySQL connections always use certificate and hostname
verification.

If you choose to use a local secret file instead of Secrets Manager, keep it
outside version control. The repo `.gitignore` excludes common secret-file
patterns, but the safer default is to use `MYSQL_ER_SECRET_ARN`.

## What The `us-west-2-bundle.pem` File Is For

`mcp/mysql-er-diagram/us-west-2-bundle.pem` is the AWS RDS regional CA bundle.
It is used by the local MCP server when it opens a TLS connection to Aurora.

Why it matters:

- Aurora is configured to require encrypted client connections
- the client needs a trusted CA bundle to verify the database server certificate
- this prevents the client from blindly trusting any endpoint claiming to be the database

In this project, the file is passed through `MYSQL_ER_SSL_CA`. The MCP server
then gives that CA bundle to PyMySQL so certificate verification and hostname
verification are both enabled.

Without it, the connection may fail TLS verification, or you would be tempted
to disable certificate checks, which is not what we want.

## Security Posture

- Aurora requires encrypted client connections with
  `require_secure_transport=ON`
- the intended database user is meant only for local schema inspection and ER
  diagram generation
- the effective read-only boundary is the database `GRANT`, not a special MCP
  enforcement layer
- default grant scope is the initial database, not all databases
- no hardcoded database credentials are committed in the repo

The default grant is:

```sql
GRANT SELECT, SHOW VIEW ON `workshop`.* TO 'readonly_user'@'%';
```

Set `ReadOnlyGrantScope=AllDatabases` only when schema inspection across all
databases is genuinely required.

## Security Review Findings - 2026-06-04

Local non-supply-chain scans were run with `cfn-lint`, `checkov`, `trivy`, and
explicit local `semgrep` checks. Python package vulnerability scanners were
intentionally excluded from this review pass.

Results:

- `cfn-lint` passed with no CloudFormation syntax or schema findings
- `trivy` secret scanning found no committed secrets
- `trivy` misconfiguration scanning reported 11 CloudFormation findings:
  1 high and 10 low
- `checkov` reported 30 passed checks and 13 failed CloudFormation benchmark checks
- local `semgrep` checks found no `0.0.0.0/0` exposure

Findings to consider:

- Aurora storage encryption is enabled, but the cluster does not specify a
  customer-managed KMS key
- Secrets Manager secrets use AWS-managed encryption instead of a
  customer-managed KMS key
- the CloudWatch log group uses default encryption instead of a
  customer-managed KMS key
- RDS IAM database authentication is not enabled
- RDS enhanced monitoring and Performance Insights are not enabled
- security group rules are missing descriptions
- the Lambda function does not enable X-Ray tracing, reserved concurrency, or a DLQ

Overall, the remaining findings are mostly production-hardening items around
customer-managed KMS keys, monitoring, tracing, and benchmark controls.
