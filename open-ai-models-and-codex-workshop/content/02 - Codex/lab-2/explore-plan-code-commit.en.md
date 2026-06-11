---
title: "From vibe coding to spec-driven development: The EPCC workflow"
weight: 21
---

The explore-plan-code-commit (**EPCC**) workflow is a structured approach that ensures scalable, production-ready code by creating maintainable implementations that integrate seamlessly with existing systems. In this workshop, run EPCC from the Codex App when possible so you can watch the conversation, plan, commands, and diffs evolve in one place.

:::alert{type="warning" header="Workflow methodology"}
EPCC is a development methodology that can be applied with any AI coding assistant. The specific commands shown here demonstrate the concepts - your Codex version may have different command names or approaches. Use `/help` to see available commands in your environment.
:::

## 1. The problem with vibe coding

**"Vibe coding"**—iteratively prompting AI without upfront planning—is like telling a contractor "build me a house" instead of working through blueprints together. When you jump straight to "build me a feature," the AI makes hundreds of assumptions. It'll build something that works, but "works" doesn't mean it matches your vision. Then comes the expensive part: "Actually, use a different approach" means tearing down and starting over.

EPCC gives you blueprints first—explore what exists, plan the architecture, build systematically, then validate quality—so you catch misalignments before writing code, not after.

## 2. The EPCC Phases

| Phase | Purpose | Output |
|-------|---------|--------|
| **Explore** | Understand existing codebase or evaluate technology choices | Understanding of architecture |
| **Plan** | Break down implementation into tasks with dependencies | Implementation roadmap |
| **Code** | Implement systematically following the plan | Working code |
| **Commit** | Validate quality and finalize for deployment | Tested, committed changes |

Your starting point depends on whether you're building new or working with existing code:
- **Greenfield projects** (new from scratch): Define requirements first, then Explore → Plan → Code → Commit
- **Brownfield projects** (existing codebases): Start with Explore to understand existing architecture

:::alert{type="info" header="When to skip EPCC"}
For quick changes, don't use EPCC—just prompt Codex directly:
- Bug fixes: "Fix the authentication error in login.ts"
- Styling updates: "Change the button color to blue"
- Small additions: "Add error handling to the API call"

EPCC is for structured, multi-step features that benefit from planning.
:::

## 3. Explore

Before making changes, understand what exists. This prevents:
- Breaking existing functionality by not understanding dependencies
- Duplicating code that already exists elsewhere
- Using inconsistent patterns that don't match the architecture
- Missing integration points that cause bugs

### Explore the codebase

1. Navigate to your project:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
:::

2. Open the repo in the Codex App. If you prefer the CLI, start Codex from the terminal:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex
:::

3. Request a codebase analysis:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Analyze this codebase and create a summary of:
- Project structure and key files
- How the chat application works (entry point, message flow, API calls)
- Configuration and authentication patterns
- Dependencies and integration points
- What features are missing that could be added
:::

Codex will systematically read files, search for patterns, and build a comprehensive understanding. In the App, use the file references and diff view to inspect what Codex read and how it is reasoning about the project.

### Document your exploration

Save the exploration results for reference:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Save your analysis to EXPLORATION.md in the project root
:::

## 4. Plan

With understanding of the codebase, create a detailed implementation plan.

![Use Codex plan mode to research, build a plan, then execute](/static/images/codex/onboarding-deck/slide-16.png)

### Create an implementation plan

1. Define your feature clearly:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
I want to add in-memory conversation history so the interactive chat remembers earlier turns. Single-message mode can remain stateless. Based on your exploration, create a detailed implementation plan that:
1. Lists all files that need to be created or modified
2. Identifies the order of changes (dependencies)
3. Considers our existing patterns and architecture
4. Includes testing requirements
5. Notes any potential risks or challenges
:::

2. Review the plan before proceeding. Ask clarifying questions:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
What are the risks in this plan? Are there any edge cases we should consider?
:::

3. Save the plan:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Save this implementation plan to PLAN.md
:::

:::alert{type="info" header="Plan Mode"}
If your Codex version supports plan mode, you can use it for safer planning:

```text
/plan
```

This enables analysis without executing changes until you approve.
:::

## 5. Code

Implement systematically following the plan.

### Implement the changes

1. Start implementation:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Implement the conversation history feature according to PLAN.md. Start with step 1 and proceed through each step, pausing to verify each change works before continuing.
:::

2. For each significant change, verify it works:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Run the tests to verify the changes work correctly
:::

3. Track progress as you go:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Update PLAN.md to mark completed steps and note any deviations from the original plan
:::

### Best practices during coding

| Practice | Description |
|----------|-------------|
| Incremental changes | Make small, testable changes rather than large rewrites |
| Verify each step | Run tests after each significant change |
| Document deviations | Note any changes from the original plan |
| Maintain patterns | Follow existing code style and architecture |

## 6. Commit

Validate quality and finalize the changes.

### Review and commit

1. Run the full test suite:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Run all tests and fix any failures
:::

2. Run linting and type checking:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Run linting and type checking, fix any issues
:::

3. Create a commit with a descriptive message:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Create a git commit for these changes with a descriptive message that explains what was added and why
:::

## 7. Test the feature

1. Test the conversation history feature:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
printf "My project codename is Aurora.\\nWhat is my project codename?\\nquit\\n" | python chat.py
:::

2. Verify that the assistant uses the earlier codename in its second answer. If you added a command such as `/clear`, test that clearing the history makes the assistant forget the codename.

## 8. EPCC Summary

| Phase | Key Question | Deliverable |
|-------|--------------|-------------|
| **Explore** | "What exists and how does it work?" | Codebase understanding |
| **Plan** | "What changes are needed and in what order?" | Implementation roadmap |
| **Code** | "Does each change work as expected?" | Working implementation |
| **Commit** | "Does everything pass quality checks?" | Validated, committed code |

:::alert{type="info" header="Adapt to your workflow"}
EPCC is a methodology, not a rigid process. Adapt it to your team's needs:
- Skip phases for simple changes
- Add phases for complex projects (e.g., security review)
- Combine with your existing development practices
:::

## 9. Congratulations!

You've learned the EPCC workflow for structured, spec-driven development. This approach helps you build production-ready features with fewer iterations and better alignment with existing systems.
