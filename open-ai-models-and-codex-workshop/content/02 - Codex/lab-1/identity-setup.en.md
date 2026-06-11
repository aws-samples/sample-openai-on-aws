---
title: "(Optional) Select identity and access pattern"
weight: 15
---

Choose the right AWS authentication pattern for your team's Codex on Bedrock deployment.

:::alert{type="info" header="Workshop default"}
For this workshop you already have what you need: the AWS credentials and `AWS_REGION` from Getting Started, which the CLI uses directly, and a Bedrock bearer token for the App's `~/.codex/.env`. The patterns below matter when you roll Codex out to a team and want per-user attribution and rotation.
:::

## 1. Authentication options

The built-in `amazon-bedrock` provider authenticates with AWS-native credentials. It checks for a Bedrock bearer token first, then falls back to the AWS SDK credential chain. That gives you several options depending on how your team is set up:

| Method | Setup Time | Security Level | Best For |
|:-------|:-----------|:---------------|:---------|
| **AWS credentials in the shell** | Minutes | Medium | This workshop, individual developers, the CLI |
| **Bedrock API key / bearer token** | Minutes | Medium | The App and IDE (via `~/.codex/.env`), quick testing |
| **IAM profile (`AWS_PROFILE`)** | Minutes | Medium | Developers juggling multiple AWS accounts |
| **IAM Identity Center (SSO)** | Hours | High | Team deployments with per-user attribution |

## 2. Workshop default: AWS credentials and a bearer token

For the CLI, the credentials already in your terminal are enough. For the App, a Bedrock bearer token in `~/.codex/.env` is the clean path because GUI apps do not inherit your shell environment. Both were covered in the App and CLI setup pages. To regenerate a bearer token at any time:

:::::tabs{variant="container" groupId="os"}
::::tab{label="macOS / Linux"}
:::code{showCopyAction="true" language="bash"}
export AWS_BEARER_TOKEN_BEDROCK=$(python3 -c "from aws_bedrock_token_generator import provide_token; print(provide_token(region='us-east-2'))")
:::
::::
::::tab{label="Windows"}
:::code{showCopyAction="true" language="powershell"}
$env:AWS_BEARER_TOKEN_BEDROCK = python -c "from aws_bedrock_token_generator import provide_token; print(provide_token(region='us-east-2'))"
:::
::::
:::::

## 3. Team option: IAM profile

For developers who switch between AWS accounts, configure a named profile and point Codex at it:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws configure --profile codex-bedrock
export AWS_PROFILE=codex-bedrock
export AWS_REGION=us-east-2
:::

Codex picks up the profile through the standard AWS credential chain. No extra Codex configuration is required.

## 4. Enterprise option: IAM Identity Center

For enterprise deployments with per-user cost attribution, use IAM Identity Center (SSO):

1. Configure IAM Identity Center in your AWS organization and create permission sets with Bedrock access.
2. Have each developer sign in and export the profile:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws sso login --profile codex-bedrock
export AWS_PROFILE=codex-bedrock
:::

3. Use session tags so usage attributes to individual users in Cost Explorer.

![Session Tag Setup](/static/images/codex/lab-1/iam-idc-session-tag-setup.png)

:::alert{type="info" header="Per-user cost tracking"}
IAM Identity Center session tags flow through to Cost Explorer, letting you attribute Bedrock spend to individual users or teams.
:::

Configure cost allocation tags to track usage by user or team:

![Cost Allocation Tags](/static/images/codex/lab-1/iam-idc-cost-allocation-tag.png)

A profile's `credential_process` helper can automate login, token exchange, caching, and refresh outside Codex, so developers rarely re-authenticate.

## 5. Bedrock API key for shared environments

A long-lived Bedrock API key is convenient for CI or shared boxes where interactive SSO is awkward. Export it the same way as a bearer token:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
export AWS_BEARER_TOKEN_BEDROCK="your-bedrock-api-key"
export AWS_REGION=us-east-2
:::

:::alert{type="warning" header="API key security"}
Long-lived Bedrock API keys do not rotate on their own. Prefer short-lived bearer tokens or IAM-based authentication for anything beyond quick testing.
:::

## 6. Congratulations!

You understand the AWS authentication options for Codex on Bedrock and which ones fit individual, team, and enterprise deployments.
