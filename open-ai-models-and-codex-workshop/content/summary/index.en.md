---
title: "Summary 🎉"
weight: 40
---

You made it. You now have the core patterns for building with OpenAI models and Codex in a real engineering workflow: API calls, structured outputs, tools, vision, agents, app-based development, team standards, and governance.

This workshop started with a simple setup step: join the OpenAI organization, create an API key, and use that same key across the model labs and Codex. From there, you moved from single model calls to the patterns that matter in production.

## 1. What you built up

| Area | What you can now do |
|------|---------------------|
| **OpenAI setup** | Use the workshop OpenAI API key across scripts, the Codex App, IDE workflows, and CLI workflows |
| **Responses API** | Send text and image inputs, stream responses, continue conversations, and choose how to manage state |
| **Structured outputs** | Return JSON and typed Python objects instead of brittle free-form text |
| **Function calling** | Let the model choose tools, pass structured arguments, and incorporate tool results |
| **Parallel tool calls** | Handle multiple independent tool calls in one model turn |
| **Hosted tools** | Understand when to use OpenAI-hosted capabilities such as web search or file search |
| **Vision** | Analyze dashboards, extract structured data from images, and reason over visual information while validating exact values |
| **Agents SDK** | Move from hand-rolled loops to cleaner agent orchestration patterns |
| **Codex App** | Work with Codex in a visual surface for chat, diffs, terminal output, files, and parallel tasks |
| **Team workflows** | Use AGENTS.md, rules, config, skills, subagents, and review patterns to make Codex repeatable across a team |

## 2. The big idea

OpenAI models are not just chat boxes. The Responses API gives you a single interface for input, output, state, tools, structured data, images, and agentic workflows. Codex then brings those same capabilities into software delivery: reading code, planning changes, editing files, running checks, and helping teams standardize how work gets done.

The important shift is this:

| Old pattern | New pattern |
|-------------|-------------|
| Prompt once and copy text | Build repeatable model-powered workflows |
| Parse prose manually | Ask for structured output your code can validate |
| Guess which API call to make | Let the model choose tools with schemas |
| Treat screenshots as manual evidence | Use vision for first-pass analysis and extraction |
| Use AI as a side window | Bring Codex into the repo, terminal, IDE, and review loop |
| Rely on individual prompting style | Capture team standards in AGENTS.md, rules, skills, and config |

## 3. What to take back to your team

1. **Start with one useful workflow.** Pick a real team pain point: cost summaries, support ticket triage, code review, documentation, migration planning, or test generation.
2. **Make outputs structured early.** If another system needs the answer, use JSON, Pydantic, or schema-backed outputs from the start.
3. **Keep humans in the loop where risk is high.** Vision, reasoning, and tool use are powerful, but exact financial, security, and production decisions still need validation.
4. **Use Codex where the work already lives.** The Codex App is the recommended workshop surface, while IDE and CLI paths are there for editor-first and terminal-first developers.
5. **Turn good habits into shared defaults.** Put project guidance in AGENTS.md, capture safe command rules, define reusable skills, and use subagents for focused review or parallel investigation.

## 4. A strong next step

Take the sample app from Part 2 and choose one improvement that would matter in a real customer conversation:

- Add a production-quality evaluation or regression test.
- Add a structured output contract for model responses.
- Add a small custom tool that calls an AWS service or internal API.
- Add a Codex skill for your team's most common review workflow.
- Add an AGENTS.md file to one of your own repos and try an EPCC-style change with Codex.

## 5. Final reminder

For this workshop run, keep using the **OpenAI API key from preliminary setup** unless your facilitator explicitly switches you to the Bedrock-hosted path. The Bedrock references are included so teams can adapt the same patterns for AWS-hosted deployments later.

You now have the pieces. The next move is to turn them into one small, useful, repeatable workflow for your own team.
