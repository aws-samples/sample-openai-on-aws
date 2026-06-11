---
title: "Establish team standards with AGENTS.md and custom commands"
weight: 23
---

Consistent team standards maintain code quality, reduce onboarding time, and enable seamless collaboration. Codex automatically loads your team's coding conventions, project structure, and workflow patterns from AGENTS.md files, ensuring AI assistance aligns with your established practices across all development sessions.

## 1. Understanding AGENTS.md file hierarchy

![AGENTS.md keeps conventions in Codex context](/static/images/codex/onboarding-deck/slide-30.png)

Codex automatically discovers and loads AGENTS.md files from multiple locations, combining them to provide context for your project. You can place AGENTS.md files in several locations:

- **Project root** (recommended): Share standards across your entire team by checking into git
- **Parent directories**: For monorepos, place in both root and subdirectories
- **Child directories**: Codex pulls these automatically when working with files in those directories
- **Home folder** (:code[~/.codex/AGENTS.md]{showCopyAction=true}): Applies to all your Codex sessions globally

## 2. Create your team's AGENTS.md

1. Create a team-wide :code[AGENTS.md]{showCopyAction=true} file in your workshop root with your preferred terminal editor:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
${EDITOR:-nano} AGENTS.md
:::

If you use VS Code and have the `code` shell command installed, you can use `code AGENTS.md` instead.

2. Add the following team configuration to the file:

:::code{showCopyAction="true" language="markdown" copyAutoReturn="true"}
# Team Codex Configuration

## Bash commands
- python chat.py: Run the chat application
- python chat.py --single "message": Send a single message (for testing)
- python -m pytest tests/ -v: Run unit tests
- python -m pytest tests/ -v --tb=short: Run tests with short tracebacks

## Code style
- Use Python 3.11+ with type hints on all function signatures
- Follow PEP 8 style with 100-character line limit
- Use f-strings for string formatting
- IMPORTANT: Always include error handling around API calls
- Add docstrings to all public functions and classes

## Workflow
- Run tests after every change: python -m pytest tests/ -v
- YOU MUST write unit tests for new functions
- Always update README.md when adding new features
- Use descriptive commit messages that explain WHY, not just WHAT

## Repository structure
- chat.py: Main CLI entry point
- config.py: OpenAI client and model configuration
- tests/: Unit tests (mirror the module structure)

## API patterns
- Use the OpenAI Responses API (client.responses.create)
- Always pass model as a parameter (don't hardcode)
- Handle openai.BadRequestError and openai.NotFoundError explicitly
:::

## 3. Establish your project workflows with custom commands

Custom commands in AGENTS.md let you define reusable workflows:

:::code{showCopyAction="true" language="markdown" copyAutoReturn="true"}
## Custom Commands

### /add-feature
Add a new feature to the chat application:
1. Create or modify the appropriate module
2. Add type hints and docstrings
3. Write unit tests in tests/
4. Update README.md with usage instructions
5. Run full test suite to verify nothing is broken

### /debug-issue
Debug systematically:
1. Read error logs and identify root cause
2. Search codebase for similar patterns
3. Check git history for related commits
4. Reproduce in minimal test case
5. Implement fix with error handling
6. Write regression test

### /review-code
Review code changes:
1. Check code quality and PEP 8 adherence
2. Verify all new code has tests
3. Look for security vulnerabilities (API key exposure, injection)
4. Ensure proper error handling around API calls
5. Validate type hints are complete
:::

## 4. Verify your team standards

3. Start a new Codex session:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
codex
:::

4. Verify that Codex has loaded your team standards by asking:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
What are our team's coding standards?
:::

Codex should reference the content from your AGENTS.md file in its response.

5. If your Codex version supports it, test an initialization command to generate a scaffold:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/help
:::

Look for commands related to initialization or scaffolding (may be named `/init`, `/scaffold`, or similar). This can create a starter AGENTS.md if one doesn't exist.

:::alert{type="info" header="Team collaboration"}
Add the AGENTS.md file to your team's git repository and document the custom commands in your onboarding guide to share these standards across your team.
:::

## 5. Congratulations!

You've established consistent Codex practices for your team by creating AGENTS.md files and custom commands. Your team now has shared standards that Codex automatically applies to every coding session.
