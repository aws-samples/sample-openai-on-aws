# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## What This Is

An AWS Workshop Studio workshop titled "Diving Deep into OpenAI models and Codex on Amazon Bedrock." Content is authored in markdown and rendered via the Workshop Studio build system (contentspec.yaml v2.0).

## Repository Structure

- `content/` — Workshop markdown pages organized by module. Each directory needs an `index.en.md` with YAML frontmatter (`title`, `weight` for ordering).
- `static/` — Images and static assets referenced from content pages.
- `contentspec.yaml` — Workshop Studio build configuration. Locale is en-US.
- `FACILITATOR_GUIDE_TEMPLATE.md` — Template for the facilitator guide (rename to `FACILITATOR_GUIDE.md` when ready to publish).

## Workshop Modules

1. **00 - Prerequisites** — Account setup (self-paced or event-based)
2. **01 - Bedrock Open AI Models** — Invoking GPT-5.4 on Bedrock Mantle via curl, boto3, OpenAI SDK, OpenAI CLI, web search, remote MCP, Agents SDK, and Guardrails
3. **02 - Codex** — Configuring OpenAI Codex CLI with Amazon Bedrock:
   - Getting Started (setup)
   - Lab 1: Setup Codex for teams (identity, environment, IDE extension, quotas, cost monitoring)
   - Lab 2: Team standards and workflows (AGENTS.md, goals/plan mode, skills/memories, git, MCP servers, session tips)
   - Lab 3: Advanced workflows (quality gates, security review, smart documentation)
   - Lab 4: Observability and governance (OpenTelemetry, CloudWatch, quotas, analytics)

## Content Authoring Conventions

- Filenames: `<weight-or-name>.en.md` with YAML frontmatter at top
- Workshop Studio directives are used: `:::alert{type="info"}`, `:::code{showCopyAction="true"}`, `:::::tabs{variant="container"}`, `::::tab{id="python" label="Python"}`, `:::expand{header="..."}`
- Code samples use `openai.gpt-5.4` or `openai.gpt-oss-120b` as model IDs
- The Bedrock Mantle endpoint pattern: `https://bedrock-mantle.<region>.api.aws/v1`
- Authentication uses `@aws/bedrock-token-generator` (TS) or `aws_bedrock_token_generator` (Python)

## Build & Preview

This is a Workshop Studio content-only repo (no application code to build). To preview:
- Push to the connected Workshop Studio content source and use the build/preview in Workshop Studio console
- Markdown is rendered by Workshop Studio's Hugo-based pipeline

## Key Technical Details

- The `bedrock-mantle` endpoint is distinct from `bedrock-runtime` — uses IAM namespace `bedrock-mantle:*` and managed policy `AmazonBedrockMantleInferenceAccess`
- OpenAI Responses API format (stateless, items-based) is the primary API used throughout Module 01
- Module 02 (Codex) references the `codex` CLI tool configured with `OPENAI_BASE_URL` pointing at Bedrock Mantle
