---
title : "Example: Quality gates"
weight : 34
---

Implement automated quality checks that prevent low-quality code from being merged by running comprehensive validation on every commit.

## 1. Create a quality gates hook

Run the following commands in your **terminal** (not inside Codex).

1. Set up automated quality gates that run on code changes:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p ~/.codex/hooks

cat > ~/.codex/hooks/quality-check.sh << 'EOF'
#!/bin/bash
# Quality gate hook for Codex
# Runs before committing changes

FILE_PATH=$1

echo "Running quality checks on $FILE_PATH..."

# Check file extension and run appropriate linters
case "$FILE_PATH" in
  *.js|*.jsx|*.ts|*.tsx)
    echo "Checking JavaScript/TypeScript quality..."
    if command -v eslint &> /dev/null; then
      eslint "$FILE_PATH" --quiet
    fi
    if command -v prettier &> /dev/null; then
      prettier --check "$FILE_PATH"
    fi
    ;;
  *.py)
    echo "Checking Python quality..."
    if command -v ruff &> /dev/null; then
      ruff check "$FILE_PATH"
    fi
    if command -v black &> /dev/null; then
      black --check "$FILE_PATH"
    fi
    ;;
  *.go)
    echo "Checking Go quality..."
    if command -v gofmt &> /dev/null; then
      gofmt -l "$FILE_PATH"
    fi
    ;;
esac

echo "Quality checks complete."
EOF

chmod +x ~/.codex/hooks/quality-check.sh
:::

2. Configure the hook in your Codex settings:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cat > ~/.codex/hooks.toml << 'EOF'
[hooks]
post-edit = "~/.codex/hooks/quality-check.sh"
EOF
:::

## 2. What quality gates check

The automated quality gates perform validation including:

- **Code formatting** - Ensures consistent code style
- **Linting** - Catches common errors and anti-patterns
- **Type checking** - Verifies type safety (for typed languages)
- **Security scanning** - Identifies potential vulnerabilities
- **Test coverage** - Ensures adequate test coverage

If any gate fails, feedback is provided with detailed remediation steps.

## 3. Test the quality gates

1. Navigate to your project directory and make an edit:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
codex
:::

2. Make a change to a file and observe the quality checks run:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Add a console.log statement to the main chat API file for debugging
:::

3. The quality gates will automatically execute after the edit completes.

## 4. Customize quality gates

You can customize the quality gates for your team's specific needs:

| Gate Type | Tools | Configuration |
|-----------|-------|---------------|
| JavaScript | ESLint, Prettier | .eslintrc, .prettierrc |
| Python | Ruff, Black, MyPy | pyproject.toml |
| Go | gofmt, golint | go.mod |
| General | Custom scripts | hooks.toml |

## 5. Congratulations!

You've successfully implemented automated quality gates that ensure consistent code quality across your project. Every edit now goes through comprehensive validation, helping prevent issues from reaching your main branch and maintaining high standards across your development team.
