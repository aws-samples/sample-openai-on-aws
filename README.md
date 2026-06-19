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
| **[Native AWS Access](https://github.com/openai-on-aws/guidance-codex/blob/main/docs/QUICKSTART_NATIVE_AWS_ACCESS.md)** | 5–60 min | Optional Codex-side OTel | Teams with IdC, soft monitoring OK |
| **[LLM Gateway](https://github.com/openai-on-aws/guidance-codex/blob/main/docs/QUICKSTART_LLM_GATEWAY.md)** | 15 min | Provided by the gateway | Hard budgets, rate limiting |

Both patterns include:
- Corporate SSO (Okta, Azure AD, Auth0, AWS IAM Identity Center)
- Per-user CloudTrail audit trails
- One-command authentication
- Cross-platform support (Windows, macOS, Linux)
- CloudFormation templates for one-command infrastructure deployment

## Quick Start

```bash
git clone https://github.com/openai-on-aws/guidance-codex.git
cd guidance-codex
```

- **Native AWS Access** → [Quickstart](https://github.com/openai-on-aws/guidance-codex/blob/main/docs/QUICKSTART_NATIVE_AWS_ACCESS.md)
- **LLM Gateway** → [Quickstart](https://github.com/openai-on-aws/guidance-codex/blob/main/docs/QUICKSTART_LLM_GATEWAY.md)

## Documentation

- [Overview & decision guide](https://github.com/openai-on-aws/guidance-codex/blob/main/QUICKSTART.md)
- [Architecture & pattern comparison](https://github.com/openai-on-aws/guidance-codex/blob/main/docs/01-decide.md)
- [Monitoring & operations](https://github.com/openai-on-aws/guidance-codex/blob/main/docs/operate-monitoring.md)
- [Troubleshooting](https://github.com/openai-on-aws/guidance-codex/blob/main/docs/operate-troubleshooting.md)
- [CHANGELOG](https://github.com/openai-on-aws/guidance-codex/blob/main/CHANGELOG.md)

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

This repository is dual-licensed:

- **Code** (`.py`, `.js`, `.ts`, `.go`, configuration files, and other source) is licensed under the [MIT No Attribution (MIT-0)](LICENSE) license.
- **Documentation, media, and text content** (`.md` documentation, images, and diagrams) is licensed under the [Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0)](LICENSE-DOCS.md) license.
