# Sample: OpenAI-Compatible Clients on AWS

Helper packages for connecting OpenAI-compatible AI clients to AWS services with corporate SSO and observability.

## Packages

| Package | Description |
|---------|-------------|
| [aws-oidc-auth/](aws-oidc-auth/) | Go credential helper that exchanges OIDC tokens or AWS Identity Center sessions for temporary AWS credentials. Supports Okta, Azure AD, Auth0, Cognito, and AWS IAM Identity Center. See [AUTH_HELPER.md](AUTH_HELPER.md). |
| [otel-helper/](otel-helper/) | Go binary that extracts user identity from OIDC JWT tokens and emits them as OpenTelemetry HTTP headers for per-user attribution. |

## Archive

Older exploratory notebooks and examples (Bedrock, SageMaker, SGLang, Strands) are preserved in [archive/](archive/). They are not actively maintained.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

To report a security issue, see [CONTRIBUTING.md](CONTRIBUTING.md#security-issue-notifications). Do not open a public GitHub issue.

## License

- **Code** is licensed under [MIT No Attribution (MIT-0)](LICENSE).
- **Documentation and text content** is licensed under [CC-BY-SA 4.0](LICENSE-DOCS.md).
