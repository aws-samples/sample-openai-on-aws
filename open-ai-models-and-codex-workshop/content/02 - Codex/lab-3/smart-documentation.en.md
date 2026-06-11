---
title : "Example: Smart documentation"
weight : 33
---

Set up automated documentation generation following the Diataxis framework with smart routing for different types of documentation needs.

## 1. Create documentation commands

Run the following commands in your **terminal** (not inside Codex).

1. Set up the documentation commands:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p ~/.codex/commands

cat > ~/.codex/commands/docs-tutorial.md << 'EOF'
---
name: docs-tutorial
description: Generate a tutorial for learning a concept
---

Create a step-by-step tutorial that:
1. Introduces the learning goal
2. Provides hands-on exercises
3. Builds knowledge incrementally
4. Includes practical examples
5. Ends with a summary of what was learned

Focus on the learning journey, not just the end result.
EOF

cat > ~/.codex/commands/docs-howto.md << 'EOF'
---
name: docs-howto
description: Generate a how-to guide for accomplishing a task
---

Create a practical how-to guide that:
1. States the goal clearly
2. Lists prerequisites
3. Provides numbered steps
4. Includes code examples
5. Addresses common issues

Focus on getting the task done efficiently.
EOF

cat > ~/.codex/commands/docs-reference.md << 'EOF'
---
name: docs-reference
description: Generate reference documentation
---

Create comprehensive reference documentation that:
1. Documents all functions, methods, or APIs
2. Includes parameter descriptions
3. Shows return values and types
4. Provides usage examples
5. Notes edge cases and limitations

Focus on completeness and accuracy.
EOF

cat > ~/.codex/commands/docs-explanation.md << 'EOF'
---
name: docs-explanation
description: Generate explanatory documentation
---

Create explanatory documentation that:
1. Provides background and context
2. Explains the "why" behind decisions
3. Discusses trade-offs and alternatives
4. Connects concepts to broader patterns
5. Addresses common misconceptions

Focus on understanding, not just facts.
EOF
:::

2. View your documentation commands:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
ls ~/.codex/commands/
:::

## 2. Generate documentation

1. In your **terminal**, navigate to your project and start Codex:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
codex
:::

2. Inside **Codex**, use the documentation commands to generate different types of content:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/docs-tutorial Create a tutorial for understanding the chat session state management
:::

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/docs-howto Create a guide for adding a new chat feature
:::

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/docs-reference Create API reference for the chat app's public functions
:::

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
/docs-explanation Explain the architectural decisions in this chat application
:::

## 3. Understanding the Diataxis framework

The Diataxis framework organizes documentation into four types:

| Type | Purpose | User Need |
|------|---------|-----------|
| **Tutorial** | Learning-oriented | "I want to learn" |
| **How-to** | Task-oriented | "I want to accomplish" |
| **Reference** | Information-oriented | "I want to look up" |
| **Explanation** | Understanding-oriented | "I want to understand" |

Using these distinct documentation types helps ensure your documentation serves all user needs effectively.

## 4. Congratulations!

You've successfully set up smart documentation generation that automatically creates comprehensive, well-organized documentation following proven frameworks. Your team can now generate consistent, high-quality documentation that serves different user needs and learning styles.
