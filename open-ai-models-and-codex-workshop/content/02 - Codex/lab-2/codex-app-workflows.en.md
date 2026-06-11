---
title: "Use the Codex App for everyday workflows"
weight: 22
---

The Codex App is a strong default surface for this workshop because it makes the agent loop visible: Codex reads files, proposes plans, edits code, runs commands, shows diffs, and keeps the conversation around the work in one place.

Use this page as a menu of high-value workflows. You do not need to complete every prompt; pick two or three that match your repo and role.

:::alert{type="info" header="Use the workshop repo"}
Open `~/workshop/sample-openai-on-aws/bedrock-chat` in the Codex App before trying these prompts. That folder comes from the `codex-advanced-patterns` branch cloned in Lab 1.
:::

## 1. Start with context

Before asking Codex to change code, ask it to understand the project.

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Analyze this repository and create a concise architecture brief:
- What the app does
- The major components and entry points
- How data flows through the system
- How to run tests and local development
- Risks or confusing areas a new developer should know about
:::

Then ask Codex to turn that into something concrete:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Create a Mermaid diagram that explains the main request flow in this app. Keep it accurate to the files you inspected.
:::

## 2. Use the four-field prompt template

Strong prompts do not need to be long. They need to give Codex enough context to work safely.

![Mini Codex prompt template](/static/images/codex/onboarding-deck/slide-15.png)

Use this template for non-trivial work:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Goal: [What outcome do we want, and why does it matter?]
Context pointers: [Relevant files, docs, screenshots, tickets, or examples]
Constraints: [Patterns to follow, things not to change, security or style rules]
Done when: [Tests, commands, screenshots, or behavior that prove the task is complete]
:::

## 3. Try App-first use cases

### Understand a codebase

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Examine the data model and API routes in this app. Produce a detailed ERD-style summary, then list the performance bottlenecks you would investigate first.
:::

### Plan from a ticket

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Read this ticket/spec and inspect the relevant files. Before writing code, create an implementation plan and list any clarifying questions that would change the design.
:::

### Implement from an image

Attach a screenshot or mockup in the App, then ask:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Use this image as the target UI. Inspect the existing frontend patterns, implement the closest matching component, and verify that the layout works at desktop and mobile widths.
:::

### Improve an existing feature with tests

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Find endpoints in this app that are missing authentication checks. First write failing tests that demonstrate the issue, then implement the fix and keep working until all tests pass.
:::

### Review your work before commit

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/review
:::

If `/review` is not available in your version, ask:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Review my current diff for bugs, missing tests, security risks, and unclear behavior. Prioritize findings by severity and cite file paths.
:::

### Use local tools

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Look at the last 30 days of commits in this repository and summarize what changed. Identify any files that look risky or frequently edited.
:::

## 4. Validate quickly

Codex becomes much more autonomous when success is deterministic. Before asking it to make a large change, ask what command proves success:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
What is the fastest reliable validation loop for this task? Identify the tests, lint commands, type checks, or browser checks you should run after each meaningful change.
:::

## 5. Congratulations!

You've practiced App-centered Codex workflows that map directly to everyday engineering tasks: understand, plan, implement, test, review, and document.
