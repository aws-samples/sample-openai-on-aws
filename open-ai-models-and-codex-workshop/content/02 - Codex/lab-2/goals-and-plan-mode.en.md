---
title: "From vibe coding to spec-driven development: Goals and Plan Mode"
weight: 24
---

Goals and plan mode transform Codex from a reactive assistant into a proactive development partner that maintains focus and executes structured workflows. In the Codex App, this is especially useful because you can keep the plan, diffs, approvals, and follow-up questions visible while the agent works.

:::alert{type="warning" header="Command syntax"}
The goal and plan commands shown here (`/goal set`, `/goal pause`, `/plan`) demonstrate the concepts. Exact command syntax may vary by Codex version - use `/help` to see available commands.
:::

## 1. The problem with "vibe coding"

Without structure, AI-assisted development can become unfocused:

- Prompts drift from the original objective
- Changes accumulate without validation
- The codebase evolves in unexpected directions
- Technical debt grows silently

## 2. Goals: Persistent task objectives

Goals let you set a persistent objective that Codex tracks throughout your session.

### Set a goal

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/goal set Implement user authentication with JWT tokens
:::

### Goal commands

| Command | Description |
|:--------|:------------|
| :code[/goal set <description>]{showCopyAction=true} | Set a new goal |
| :code[/goal]{showCopyAction=true} | View current goal |
| :code[/goal pause]{showCopyAction=true} | Temporarily pause goal tracking |
| :code[/goal resume]{showCopyAction=true} | Resume goal tracking |
| :code[/goal clear]{showCopyAction=true} | Clear the current goal |

With a goal set, every response from Codex considers whether it advances the objective. This keeps long sessions focused.

## 3. Plan mode: Strategy before execution

Plan mode asks Codex to propose an execution strategy before implementing changes.

### Enter plan mode

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/plan
:::

In plan mode, Codex will:

1. **Analyze** the task requirements
2. **Break down** into discrete steps
3. **Identify** potential challenges
4. **Propose** implementation order
5. **Wait** for your approval before executing

### Example workflow

In this example, we'll build an **OpenAI Chat App**, a simple web application that lets users chat with the workshop model through a browser, using the GPT-on-Bedrock credentials you set up in Getting Started.

1. Set your goal:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/goal set Build an OpenAI Chat App with a React frontend and Python FastAPI backend
:::

2. Enter plan mode:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/plan
:::

3. Describe the feature:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
I need a chat application that connects to the workshop GPT model via the Responses API. It should have a React frontend with a message input, chat history display, and streaming responses. The backend should be a Python FastAPI server that reads OPENAI_BASE_URL and OPENAI_API_KEY from the environment and uses the OpenAI SDK, so it works against Bedrock unchanged.
:::

4. Codex proposes a plan:

```
Plan for OpenAI Chat App:

1. Create FastAPI backend with /chat endpoint
2. Implement OpenAI SDK client using OPENAI_BASE_URL and OPENAI_API_KEY from the environment
3. Add streaming response support via Server-Sent Events
4. Create React frontend with chat UI components
5. Implement message history state management
6. Add real-time streaming display in the chat window
7. Write tests for backend API

Shall I proceed with this plan?
```

5. Approve and execute:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Yes, proceed with the plan
:::

After executing the plan, you'll have a working chat application connected to the workshop OpenAI model — built entirely through structured, goal-driven development.

## 4. Combining goals and plan mode

The most powerful workflow combines both:

1. **Goal**: Defines the destination (what you want to achieve)
2. **Plan mode**: Maps the route (how to get there)
3. **Execution**: Builds step by step with validation

This structured approach ensures:
- Clear objectives throughout the session
- Validated implementation strategy
- Incremental progress with checkpoints
- Reduced risk of scope creep

:::alert{type="info" header="Best practice"}
For any task that takes more than a few minutes, use goals and plan mode. The upfront planning investment pays off in cleaner implementations and fewer revisions.
:::

## 5. Congratulations!

You've learned how to use goals and plan mode for structured, spec-driven development. Your coding sessions will now have clear objectives and validated implementation strategies.
