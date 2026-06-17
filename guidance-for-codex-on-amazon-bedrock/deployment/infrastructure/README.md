# CloudFormation Infrastructure

This directory contains the 18 CloudFormation templates that compose the
Codex-on-Bedrock guidance. Templates are grouped by purpose and deployed
directly with `aws cloudformation deploy`.

For end-to-end walkthroughs that assemble these templates into a complete
deployment, see:

- `docs/QUICKSTART_NATIVE_AWS_ACCESS.md` — direct Bedrock access via IAM
  Identity Center or a federated identity pool.
- `docs/QUICKSTART_LLM_GATEWAY.md` — LiteLLM gateway in front of Bedrock.

## Template Index

### Authentication (`bedrock-auth-*`)

Each template provisions the IAM/identity glue for one identity provider.
Pick exactly one per deployment.

| Template                          | Purpose                                                                |
| --------------------------------- | ---------------------------------------------------------------------- |
| `bedrock-auth-idc.yaml`           | IAM Identity Center role chained from `AWSReservedSSO_*` Permission Sets. |
| `bedrock-auth-cognito-pool.yaml`  | Cognito User Pool federated through a Cognito Identity Pool.           |
| `bedrock-auth-okta.yaml`          | Okta OIDC provider federated through a Cognito Identity Pool.          |
| `bedrock-auth-azure.yaml`         | Azure AD (Entra ID) OIDC provider federated through a Cognito Identity Pool. |
| `bedrock-auth-auth0.yaml`         | Auth0 OIDC provider federated through a Cognito Identity Pool.         |

### Cognito Building Blocks

Composable pieces used by the federated `bedrock-auth-*` flows and the
landing page.

| Template                            | Purpose                                                                  |
| ----------------------------------- | ------------------------------------------------------------------------ |
| `cognito-user-pool-setup.yaml`      | Cognito User Pool, app client, and (optional) external IdP federation.   |
| `cognito-identity-pool.yaml`        | Standalone Identity Pool supporting OIDC providers or Cognito User Pools. |
| `cognito-custom-domain-cert.yaml`   | ACM certificate for a Cognito custom domain. **Must deploy in `us-east-1`.** |

### Distribution

Optional packaging and landing-page paths for handing the Codex CLI to end
users.

| Template                          | Purpose                                                            |
| --------------------------------- | ------------------------------------------------------------------ |
| `distribution.yaml`               | S3 bucket + IAM for direct package distribution.                   |
| `presigned-s3-distribution.yaml`  | Presigned-URL variant of the distribution bucket.                  |
| `landing-page-distribution.yaml`  | Authenticated landing page (ALB + Lambda + OIDC) serving the CLI bundle. |

### Monitoring (OTel + Dashboards)

| Template                       | Purpose                                                                  |
| ------------------------------ | ------------------------------------------------------------------------ |
| `networking.yaml`              | VPC, two public subnets, IGW for the OTel collector.                     |
| `otel-collector.yaml`          | ADOT Collector on ECS Fargate (OTLP → CloudWatch metrics).               |
| `metrics-aggregation.yaml`     | **Optional / advanced.** Lambda + EventBridge that rolls log-derived metrics into CloudWatch and (with the bundled `quota_monitor` Lambda) emits SNS alerts off a `QuotaPolicies` DynamoDB table. Most deployments should rely on **gateway-native quotas** (LiteLLM `/key/generate` budgets, Portkey budget limits, Kong rate-limiting plugins) instead — see `docs/QUICKSTART_LLM_GATEWAY.md` § Quota Enforcement. Use this stack only if you need policies the gateway can't express. |
| `codex-dashboard.yaml`         | CloudWatch dashboard with embedded custom-widget Lambdas (logs-based). **Requires packaging** — run `aws cloudformation package` before `deploy`, and the S3 artifacts bucket must be in the same region as the stack (see `s3bucket.yaml`). |
| `codex-otel-dashboard.yaml`    | CloudWatch dashboard sourced from OTel-emitted metrics (per-user usage, errors, spend). No Lambda code — deploys directly with `aws cloudformation deploy`. |
| `litellm-dashboard.yaml`       | CloudWatch dashboard for the LiteLLM gateway.                            |

### Artifacts

| Template          | Purpose                                                                  |
| ----------------- | ------------------------------------------------------------------------ |
| `s3bucket.yaml`   | S3 bucket for CloudFormation Lambda code packages and artifacts.         |

The `lambda-functions/` subdirectory contains the source for Lambda code
referenced by the dashboard and aggregation templates; it is not itself a
CloudFormation template. The `quota_monitor` Lambda there is part of the
optional `metrics-aggregation.yaml` stack (see note above) and is not
required for gateway-enforced quotas.

The LiteLLM gateway ECS stack (`litellm-ecs.yaml`) lives outside this
directory at `deployment/litellm/ecs/litellm-ecs.yaml` because it depends on
runtime artifacts (image, secrets) that are not part of the base
infrastructure.

## Deployment Order and Dependencies

```
                  ┌──────────────────┐
                  │ s3bucket.yaml    │  (artifacts, optional but recommended
                  └──────────────────┘   if templates use packaged Lambdas)

  Native AWS Access path                     LLM Gateway path
  ─────────────────────                       ────────────────
  bedrock-auth-idc.yaml                       networking.yaml
        │                                          │
        │                                          ▼
        │                                   otel-collector.yaml   (optional)
        │                                          │
        │                                          ▼
        ▼                                   litellm-ecs.yaml
  (Codex CLI uses the role directly)              │
                                                  ▼
                                        litellm-dashboard.yaml (optional)

  Federated IdP variant (any of Okta/Azure/Auth0/Cognito):
  cognito-user-pool-setup.yaml  →  bedrock-auth-<idp>.yaml
  (only when the IdP variant requires its own User Pool)

  Monitoring add-ons (any path):
  networking.yaml  →  otel-collector.yaml  →  codex-otel-dashboard.yaml
  (logs-based)     metrics-aggregation.yaml  →  codex-dashboard.yaml
```

Cross-stack dependencies are wired via stack exports / `!ImportValue`. The
import names are derived from the **stack name** you choose at deploy time,
so the names below must match between the producer and the consumer.

| Producer stack (export)                              | Consumer                          |
| ---------------------------------------------------- | --------------------------------- |
| `<networking-stack>-VpcId`, `-SubnetIds`             | `otel-collector.yaml`, `litellm-ecs.yaml` |
| `<otel-stack>-endpoint`                              | `litellm-ecs.yaml` (when `EnableOtel=true`) |
| `<user-key-mapping-stack>-TableName`                 | `litellm-ecs.yaml` (when `EnableJwtMiddleware=true`) |

## Primary Template Parameters

Only the most commonly-tuned parameters are listed. Run
`aws cloudformation describe-stack-resource-drifts` or open the YAML file for
the full set, including `AllowedPattern` and default values.

### `bedrock-auth-idc.yaml`

| Parameter                    | Type               | Default                   | Notes |
| ---------------------------- | ------------------ | ------------------------- | ----- |
| `RoleName`                   | String             | `CodexBedrockIdCRole`     | Name of the chained IAM role. |
| `PolicyName`                 | String             | `CodexBedrockInvokePolicy`| Customer-managed policy name. |
| `PermissionSetNamePattern`   | String             | `CodexBedrockUser_*`      | Glob matched against `AWSReservedSSO_<PermissionSetName>_<hash>`. |
| `AllowedBedrockRegions`      | CommaDelimitedList | `us-east-1,us-west-2`     | Regions where `bedrock:InvokeModel*` is allowed. |
| `AllowedModelIdPattern`      | String             | `*`                       | Bedrock model ID glob (e.g. `openai.gpt-5-4*`). |
| `MaxSessionDurationSeconds`  | Number             | `28800`                   | 3600–43200; raise for long Codex runs. |

Outputs: `RoleArn` (exported as `${StackName}-RoleArn`), `RoleName`,
`PolicyArn` (exported as `${StackName}-PolicyArn`).

### `networking.yaml`

| Parameter              | Type   | Default        | Notes |
| ---------------------- | ------ | -------------- | ----- |
| `VpcCidr`              | String | `10.0.0.0/16`  | VPC CIDR. |
| `PublicSubnet1Cidr`    | String | `10.0.1.0/24`  | First public subnet. |
| `PublicSubnet2Cidr`    | String | `10.0.2.0/24`  | Second public subnet. |

Outputs (all exported): `VpcId`, `PublicSubnet1`, `PublicSubnet2`,
`SubnetIds` (comma-joined).

### `otel-collector.yaml`

| Parameter            | Type               | Default                                          | Notes |
| -------------------- | ------------------ | ------------------------------------------------ | ----- |
| `VpcId`              | String             | —                                                | Required. Pass via `!ImportValue` from the networking stack. |
| `SubnetIds`          | CommaDelimitedList | —                                                | At least 2 subnets (ALB requirement). |
| `CollectorImage`     | String             | `public.ecr.aws/aws-observability/aws-otel-collector:latest` | ADOT image. |
| `MetricsNamespace`   | String             | `LiteLLMGateway`                                 | CloudWatch metrics namespace. |
| `CustomDomainName`   | String             | —                                                | Required. HTTPS endpoint domain. |
| `HostedZoneId`       | String             | —                                                | Required. Route53 zone for certificate validation. |
| `OidcIssuerUrl`      | String             | `''`                                             | Optional: enable ALB JWT validation. |
| `OidcJwksEndpoint`   | String             | `''`                                             | JWKS URL for ALB JWT signature validation. |
| `OidcClientId`       | String             | `''`                                             | OIDC client ID for `aud` claim validation. |
| `EnableAnalytics`    | String             | `false`                                          | `true` enables dual-export (OTLP + EMF). |

Outputs: `VpcId`, `SubnetIds`, `CollectorEndpoint` (exported as
`${StackName}-endpoint`), `ALBEndpoint` (exported as `${StackName}-alb-dns`),
`ConfigParameterName`, `LogGroupName`, `Note`.

### `litellm-ecs.yaml` (in `deployment/litellm/ecs/`)

| Parameter                  | Type    | Default                    | Notes |
| -------------------------- | ------- | -------------------------- | ----- |
| `NetworkingStackName`      | String  | `codex-test-networking`    | Imports `<name>-VpcId` and `<name>-SubnetIds`. |
| `OtelStackName`            | String  | `codex-test-otel-collector`| Imports `<name>-endpoint` only when `EnableOtel=true`. |
| `EnableOtel`               | String  | `false`                    | Set to `true` only after deploying an OTel collector. |
| `LiteLLMMasterKey`         | String  | —                          | `NoEcho`. Stored in Secrets Manager. |
| `DBUsername`               | String  | —                          | `NoEcho`. RDS PostgreSQL username. |
| `DBPassword`               | String  | —                          | `NoEcho`. RDS PostgreSQL password. |
| `AwsRegion`                | String  | `us-east-2`                | Bedrock region for upstream calls. Use `us-east-2` for the default GPT-5.4 / GPT-5.5 Mantle setup. |
| `LiteLLMImage`             | String  | —                          | Required. Fully-qualified ECR URI. |
| `AllowedCidr`              | String  | `10.0.0.0/8`               | ALB ingress CIDR. **Never** `0.0.0.0/0`. |
| `AlbCertificateArn`        | String  | —                          | Required ACM certificate ARN for HTTPS listener. |
| `AlbDomainName`            | String  | `''`                       | Optional DNS name matching `AlbCertificateArn`; used in endpoint output. |
| `EnableJwtMiddleware`      | String  | `false`                    | `true` swaps API-key auth for OIDC JWT validation. |
| `JwtMiddlewareImage`       | String  | `''`                       | Required when `EnableJwtMiddleware=true`. |
| `JwksUrl`                  | String  | `''`                       | IdP JWKS endpoint. |
| `JwtAudience`              | String  | `''`                       | Optional `aud` check. |
| `JwtIssuer`                | String  | `''`                       | Optional `iss` check. |
| `UserKeyMappingStackName`  | String  | `''`                       | Required when `EnableJwtMiddleware=true`; must export `<name>-TableName`. |

Outputs: `GatewayEndpoint` (exported as `${StackName}-GatewayEndpoint`),
`OtelEndpoint` (only when `EnableOtel=true`).

## Quick Start: Native AWS Access (IAM Identity Center)

Single-stack deployment. The Codex CLI uses the chained IAM role directly via
the AWS SDK.

```bash
aws cloudformation deploy \
  --template-file deployment/infrastructure/bedrock-auth-idc.yaml \
  --stack-name codex-bedrock-idc \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      RoleName=CodexBedrockIdCRole \
      PermissionSetNamePattern='CodexBedrockUser_*' \
      AllowedBedrockRegions=us-east-1,us-west-2 \
      AllowedModelIdPattern='openai.gpt-5-*'

aws cloudformation describe-stacks \
  --stack-name codex-bedrock-idc \
  --query 'Stacks[0].Outputs'
```

Then attach the resulting `PolicyArn` (or grant `sts:AssumeRole` on
`RoleArn`) to the IdC Permission Set used by your Codex users. See
`docs/QUICKSTART_NATIVE_AWS_ACCESS.md` for the matching client-side config.

## Quick Start: LLM Gateway

Multi-stack deployment. Order matters because of stack exports.

```bash
# 1) Networking — VPC + 2 public subnets
aws cloudformation deploy \
  --template-file deployment/infrastructure/networking.yaml \
  --stack-name codex-networking \
  --capabilities CAPABILITY_IAM

# 2) (Optional) OTel collector — required only if EnableOtel=true on the gateway
aws cloudformation deploy \
  --template-file deployment/infrastructure/otel-collector.yaml \
  --stack-name codex-otel-collector \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
      VpcId=$(aws cloudformation list-exports \
                --query "Exports[?Name=='codex-networking-VpcId'].Value" \
                --output text) \
      SubnetIds=$(aws cloudformation list-exports \
                --query "Exports[?Name=='codex-networking-SubnetIds'].Value" \
                --output text) \
      CustomDomainName=telemetry.example.com \
      HostedZoneId=Z1234567890ABC \
      MetricsNamespace=CodexGateway

# 3) LiteLLM gateway on ECS Fargate
aws cloudformation deploy \
  --template-file deployment/litellm/ecs/litellm-ecs.yaml \
  --stack-name codex-litellm \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
      NetworkingStackName=codex-networking \
      OtelStackName=codex-otel-collector \
      EnableOtel=false \
      LiteLLMMasterKey=$(aws secretsmanager get-random-password \
                            --exclude-punctuation --password-length 40 \
                            --query RandomPassword --output text) \
      DBUsername=litellm \
      DBPassword=$(aws secretsmanager get-random-password \
                      --exclude-punctuation --password-length 32 \
                      --query RandomPassword --output text) \
      AwsRegion=us-east-1 \
      LiteLLMImage=<account>.dkr.ecr.<region>.amazonaws.com/codex-litellm:latest \
      AlbCertificateArn=arn:aws:acm:<region>:<account>:certificate/<id> \
      AlbDomainName=litellm.example.com \
      AllowedCidr=10.0.0.0/8

# 4) (Optional) Gateway dashboard
aws cloudformation deploy \
  --template-file deployment/infrastructure/litellm-dashboard.yaml \
  --stack-name codex-litellm-dashboard \
  --parameter-overrides MetricsNamespace=CodexGateway

aws cloudformation describe-stacks \
  --stack-name codex-litellm \
  --query 'Stacks[0].Outputs[?OutputKey==`GatewayEndpoint`].OutputValue' \
  --output text
```

The `GatewayEndpoint` output is what Codex points at via `OPENAI_BASE_URL` in
its config. See `docs/QUICKSTART_LLM_GATEWAY.md` for the full flow.

## Validation

Before deploying, validate templates locally and check parameter coverage:

```bash
# Lint each template (requires AWS CLI v2)
for f in deployment/infrastructure/*.yaml; do
  echo "=== $f ==="
  aws cloudformation validate-template --template-body file://$f >/dev/null \
    && echo "OK" || echo "FAILED"
done

# Confirm all 18 templates are present
ls deployment/infrastructure/*.yaml | wc -l    # → 18

# Diff against a deployed stack before applying changes
aws cloudformation deploy \
  --template-file deployment/infrastructure/<template>.yaml \
  --stack-name <stack> \
  --no-execute-changeset \
  --parameter-overrides ...
```

After deploying, inspect outputs and exports:

```bash
aws cloudformation describe-stacks --stack-name <stack> \
  --query 'Stacks[0].Outputs'

aws cloudformation list-exports \
  --query "Exports[?starts_with(Name, '<stack>-')]"
```

For OTel-stack health, use `deployment/scripts/check-otel-pipeline.sh`.
