---
title: "Summary 🎉"
weight: 60
---

Congratulations on completing the OpenAI Codex workshop! You've learned how to run Codex on GPT models hosted by Amazon Bedrock across the App, IDE, and CLI.

## 1. What you accomplished

**Lab 1:** Installed and configured Codex to run GPT on Amazon Bedrock through the built-in `amazon-bedrock` provider, reusing the AWS credentials from Getting Started. You set up the Codex App and CLI, explored the IDE extension, opened a repo, and planned Bedrock quotas and cost monitoring for a team rollout.

**Lab 2:** Established App-centered workflows to enhance your development experience and enable effective team collaboration. You learned the EPCC workflow (Explore-Plan-Code-Commit), prompt templates, goals and plan mode, skills and memories, subagents, git workflows, and multimodal inputs.

**Lab 3:** Explored advanced patterns that can be packaged and distributed across your team. These reusable workflows enable standardized security reviews, automated documentation, quality gates, and development loops that any team member can leverage.

**Lab 4:** Planned a rollout path for Codex teams, including AGENTS.md, skills, rules, approved integrations, and governance practices. You also reviewed Bedrock monitoring patterns with OpenTelemetry, CloudWatch dashboards, analytics pipelines, and quota monitoring.

## 2. Key concepts learned

| Concept | Description |
|---------|-------------|
| **EPCC Workflow** | Explore-Plan-Code-Commit methodology for structured development |
| **AGENTS.md** | Project instructions file for team standards and coding conventions |
| **Goals and Plan Mode** | Structured approach for exploring and implementing features |
| **Codex App workflows** | Visual surface for exploration, planning, diffs, validation, skills, and parallel work |
| **Skills and Memories** | Reusable workflows and persistent context across sessions |
| **Subagents and custom agents** | Parallel task execution and reusable specialized reviewers |
| **MCP Servers** | External tool integration via Model Context Protocol |
| **Rules** | Command approval policies for safe automation |
| **Hooks** | Automated actions triggered at workflow events |
| **OpenTelemetry** | Telemetry collection for monitoring and observability |

## 3. Codex command reference

:::alert{type="info" header="Command availability"}
Command names and syntax may vary by Codex version. Use `/help` in your Codex session to see all available commands. The commands below represent common patterns.
:::

| Command | Description |
|---------|-------------|
| :code[/help]{showCopyAction=true} | List all available commands |
| :code[/status]{showCopyAction=true} | Check session status and configuration |
| :code[/plan]{showCopyAction=true} | Enter plan mode for exploration |
| :code[/skills]{showCopyAction=true} | List available skills |
| :code[/mcp]{showCopyAction=true} | List MCP servers |
| :code[/hooks]{showCopyAction=true} | View configured hooks |

## 4. Additional resources

Continue your journey with these resources:

- [OpenAI Codex documentation](https://platform.openai.com/docs/codex)
- [Amazon Bedrock documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS MCP servers repository](https://awslabs.github.io/mcp/)
- [Model Context Protocol specification](https://modelcontextprotocol.io/)

## 5. Clean up resources

If you deployed any AWS resources during this workshop, remember to clean them up to avoid ongoing charges:

1. Delete CloudWatch dashboards:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws cloudwatch delete-dashboards --dashboard-names CodexMonitoring
:::

2. Delete CloudWatch log groups:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws logs delete-log-group --log-group-name /aws/codex/metrics
:::

3. Delete CloudWatch alarms:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws cloudwatch delete-alarms --alarm-names Codex-HighCostUsage Codex-HighTokenUsage
:::

4. Delete DynamoDB tables (if created):

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws dynamodb delete-table --table-name CodexUserQuotas
aws dynamodb delete-table --table-name CodexQuotaPolicies
:::

5. Delete SNS topics (if created):

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
aws sns delete-topic --topic-arn arn:aws:sns:us-east-2:ACCOUNT_ID:codex-quota-alerts
:::

## 6. Feedback

We'd love to hear about your experience with this workshop. Your feedback helps us improve the content and create better learning experiences for the community.

Share your thoughts, suggestions, or questions through the workshop feedback channels.
