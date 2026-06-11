---
title : "Distribute standard workflows to your team"
weight : 31
---

The examples in this lab showcase how you can extend Codex. You can package and distribute these patterns to standardize workflows across your entire team.

## 1. Creating reusable workflows

Let's create a team workflow that can be shared across projects.

1. Create a new directory structure for your team workflows:

:::code{showCopyAction="true" language="bash"}
mkdir -p ~/workshop/my-team-workflows/.codex/commands
mkdir -p ~/workshop/my-team-workflows/.codex/skills/greet
cd ~/workshop/my-team-workflows
:::

2. Create a basic team greeting skill:

:::code{showCopyAction="true" language="bash"}
cat > .codex/skills/greet/SKILL.md << 'EOF'
---
name: greet
description: Generate a friendly team greeting message
---

Generate a warm and professional greeting message for our team. Include:
- A friendly welcome
- Today's date
- A motivational quote about teamwork

Keep the tone positive and encouraging.
EOF
:::

3. Create a code review command:

:::code{showCopyAction="true" language="bash"}
cat > .codex/commands/review.md << 'EOF'
---
name: review
description: Perform a comprehensive code review
---

Review the specified code for:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security implications
5. Test coverage gaps

Provide actionable feedback with specific suggestions for improvement.
EOF
:::

4. Initialize git for version control:

:::code{showCopyAction="true" language="bash"}
git init
git add .
git commit -m "Initial team workflows"
:::

## 2. Test your workflows

1. Start Codex in the workflows directory:

:::code{showCopyAction="true" language="bash"}
codex
:::

2. Test the greeting skill:

:::code{showCopyAction="true" language="text"}
use the greet skill
:::

3. Test the review command:

:::code{showCopyAction="true" language="text"}
/review the main chat API logic in our OpenAI Chat App project
:::

## 3. Share with your team

Once you've tested your workflows locally, distribute them to your team:

:::alert{type="success" header="AWS-run workshop participants"}
If you're attending an AWS-run workshop, you can skip the following steps. This section demonstrates how to create and distribute custom workflows for production team deployments.
:::

1. Push your workflows directory to a Git repository (GitHub, GitLab, Bitbucket, or self-hosted).

2. Team members clone the repository and copy the :code[.codex]{showCopyAction=true} folder to their projects or global config:

:::code{showCopyAction="true" language="bash"}
# Replace YOUR_ORG with your real GitHub organization or repository owner.
git clone https://github.com/YOUR_ORG/team-workflows.git

# Copy to global Codex config
cp -r team-workflows/.codex/* ~/.codex/
:::

3. Alternatively, add as a git submodule for automatic updates:

:::code{showCopyAction="true" language="bash"}
# Replace YOUR_ORG with your real GitHub organization or repository owner.
git submodule add https://github.com/YOUR_ORG/team-workflows.git .codex-team
:::

This ensures everyone can use the same automated workflows.

## 4. Congratulations!

You've learned about Codex's extensibility mechanisms and how to package custom workflows for team distribution. You now understand the differences between AGENTS.md, custom commands, Skills, MCP servers, and Hooks, and can create your own reusable workflows to distribute standardized practices across your team.
