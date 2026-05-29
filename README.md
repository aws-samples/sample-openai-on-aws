# Guidance for Codex on Amazon Bedrock

Production-ready deployment patterns for running OpenAI Codex at enterprise scale on Amazon Bedrock — with corporate SSO, optional quota enforcement, and observability built in.

---

## Two Deployment Patterns

```text
Need hard quota enforcement? (Block requests when limits hit)
│
├── YES → LLM Gateway
│
└── NO → Already use AWS IAM Identity Center?
          │
          ├── YES → Native AWS Access
          │
          └── NO → Choose:
                    Native AWS Access (set up IdC) OR LLM Gateway
```

| Pattern | Setup Time | Telemetry | Best For |
|---------|------------|-----------|----------|
| **[Native AWS Access](guidance-for-codex-on-amazon-bedrock/docs/QUICKSTART_NATIVE_AWS_ACCESS.md)** | 5–60 min | Optional Codex-side OTel | Teams with IdC, soft monitoring OK |
| **[LLM Gateway](guidance-for-codex-on-amazon-bedrock/docs/QUICKSTART_LLM_GATEWAY.md)** | 15 min | Provided by the gateway | Hard budgets, rate limiting |

Both patterns include:
- Corporate SSO (Okta, Azure AD, Auth0, AWS IAM Identity Center)
- Per-user CloudTrail audit trails
- One-command authentication
- Cross-platform support (Windows, macOS, Linux)
- CloudFormation templates for one-command infrastructure deployment

## Quick Start

```bash
git clone https://github.com/aws-samples/sample-openai-on-aws.git
cd sample-openai-on-aws/guidance-for-codex-on-amazon-bedrock
```

- **Native AWS Access** → [Quickstart](guidance-for-codex-on-amazon-bedrock/docs/QUICKSTART_NATIVE_AWS_ACCESS.md)
- **LLM Gateway** → [Quickstart](guidance-for-codex-on-amazon-bedrock/docs/QUICKSTART_LLM_GATEWAY.md)

## Documentation

- [Overview & decision guide](guidance-for-codex-on-amazon-bedrock/QUICKSTART.md)
- [Architecture & pattern comparison](guidance-for-codex-on-amazon-bedrock/docs/01-decide.md)
- [Monitoring & operations](guidance-for-codex-on-amazon-bedrock/docs/operate-monitoring.md)
- [Troubleshooting](guidance-for-codex-on-amazon-bedrock/docs/operate-troubleshooting.md)
- [CHANGELOG](guidance-for-codex-on-amazon-bedrock/CHANGELOG.md)

## Source Packages

| Package | Description |
|---------|-------------|
| [aws-oidc-auth/](aws-oidc-auth/) | Go credential helper — exchanges OIDC tokens or AWS IdC sessions for temporary AWS credentials. See [AUTH_HELPER.md](AUTH_HELPER.md) for full docs. |
| [otel-helper/](otel-helper/) | Go binary that enriches OTel headers with AWS credentials for the Native AWS Access OTel pipeline. |

## Archive

Older exploratory notebooks and examples (Bedrock, SageMaker, SMML/SGLang, Strands) are preserved in [archive/](archive/). They are not actively maintained.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

To report a security issue, see [CONTRIBUTING.md](CONTRIBUTING.md#security-issue-notifications). Do not open a public GitHub issue.

## License

MIT-0 — see [LICENSE](LICENSE).
