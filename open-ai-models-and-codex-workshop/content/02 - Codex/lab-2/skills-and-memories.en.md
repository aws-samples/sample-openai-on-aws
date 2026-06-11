---
title: "Scale workflows with Skills and Memories"
weight: 25
---

Skills and memories help Codex learn from your interactions and provide reusable, domain-specific workflows that scale across your organization. In the Codex App, skills are easier to discover and apply because they appear alongside the conversation and project context.

:::alert{type="warning" header="Feature availability"}
Skills and memories are confirmed Codex features. However, the exact slash commands (like `/memories`, `/skills`) and file formats (like `skill.toml`) may vary by version. Use `/help` to see available commands in your environment.
:::

## 1. Understanding Memories

Codex can learn from your interactions and remember preferences across sessions.

### Configure memories

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/memories
:::

This opens the memories configuration where you can:

- **Enable injection**: Include relevant memories in prompts
- **Enable generation**: Learn new memories from conversations
- **View memories**: See what Codex has learned
- **Clear memories**: Reset all learned preferences

### What Codex remembers

- Coding style preferences
- Common patterns you use
- Project-specific conventions
- Frequently used commands

:::alert{type="info" header="Privacy note"}
Memories are stored locally and are not sent to the model provider. They're used to enhance your prompts locally before sending.
:::

## 2. Understanding Skills

Skills are pre-packaged workflows for common tasks that you can browse and apply.

![Use the Codex App to create automations that improve skills over time](/static/images/codex/onboarding-deck/slide-33.png)

### Browse available skills

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/skills
:::

Built-in skills include:

| Skill | Description |
|:------|:------------|
| API generation | Generate RESTful endpoints |
| Test writing | Create comprehensive test suites |
| Documentation | Generate docs from code |
| Refactoring | Apply common refactoring patterns |

### Create custom skills

Create project-specific skills in :code[.codex/skills/]{showCopyAction=false}:

1. Create the skills directory:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p .codex/skills/api-generator
:::

2. Create the skill configuration:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cat > .codex/skills/api-generator/skill.toml << 'EOF'
name = "api-generator"
description = "Generate RESTful API endpoints following team conventions"

[prompts]
scaffold = """
Create a RESTful API with CRUD operations for $resource.
Follow our AGENTS.md conventions for:
- Error handling
- Validation
- Response formats
- Testing
"""
EOF
:::

3. Use the skill:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/skills api-generator
:::

## 3. Combining memories and skills

Memories and skills work together:

- **Memories** capture your personal preferences and patterns
- **Skills** encode team-wide workflows and conventions

When you invoke a skill, Codex enhances it with relevant memories to personalize the output.

## 4. App exercise: turn repeated work into a skill

After you complete a repeated workflow in the App, ask Codex to capture it:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Review this session and identify any workflow we repeated more than once. Propose a skill that would make this workflow reusable, including the SKILL.md description, required instructions, and any scripts or references it should include.
:::

If the proposal looks useful, ask Codex to create the skill in your repo:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Create this as a repo-local skill under .codex/skills/. Keep it focused, document when to use it, and add a short example prompt.
:::

## 5. Best practices

- **Start with memories**: Let Codex learn your preferences naturally
- **Create skills for repeated workflows**: If you do something more than twice, make it a skill
- **Share skills via git**: Commit :code[.codex/skills/]{showCopyAction=false} to share with your team
- **Review memories periodically**: Clear outdated preferences with :code[/memories]{showCopyAction=true}

## 6. Congratulations!

You've learned how to use memories and skills to scale domain expertise across your team. Your workflows are now reusable and shareable.
