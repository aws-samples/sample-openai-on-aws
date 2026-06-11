---
title : "Example: Security review"
weight : 32
---

Set up automated security analysis and OWASP vulnerability scanning in your development workflow.

## 1. Copy the security reviewer custom agent

Run the following commands in your **terminal** (not inside Codex).

1. Ensure the security reviewer custom agent is available globally:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p ~/.codex/agents
cat > ~/.codex/agents/security-reviewer.toml << 'EOF'
name = "security-reviewer"
description = "Perform comprehensive OWASP vulnerability assessment"
model_reasoning_effort = "high"
sandbox_mode = "read-only"

developer_instructions = """
You are a security expert performing a comprehensive security review following OWASP guidelines.

OWASP Top 10 checks:
- A01:2021 Broken Access Control
- A02:2021 Cryptographic Failures
- A03:2021 Injection
- A04:2021 Insecure Design
- A05:2021 Security Misconfiguration
- A06:2021 Vulnerable Components
- A07:2021 Authentication Failures
- A08:2021 Software and Data Integrity Failures
- A09:2021 Security Logging Failures
- A10:2021 Server-Side Request Forgery

For each finding, provide:
- **Severity**: Critical/High/Medium/Low
- **OWASP Category**: Which category this falls under
- **Location**: File and line number
- **Description**: Clear explanation of the issue
- **Remediation**: Specific steps to fix
"""
EOF
:::

2. You can review the security reviewer agent to understand its capabilities:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cat ~/.codex/agents/security-reviewer.toml
:::

## 2. Run security review

1. In your **terminal**, navigate to your project and start Codex:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
codex
:::

2. Inside **Codex**, run a security analysis using the security reviewer agent:

:::code{showCopyAction="true" language="text" copyAutoReturn="true"}
Spawn the security-reviewer custom agent to perform an OWASP vulnerability assessment of my codebase. Wait for the agent result, then summarize the verified findings and remediation recommendations.
:::

:::alert{type="warning" header="Security review limitations"}
This automated security review is a helpful starting point but may not be foolproof. Always complement AI-assisted security analysis with manual code reviews, professional security audits, and established security testing practices for production systems.
:::

This process will:
- Activate the specialized security reviewer agent
- Perform OWASP Top 10 vulnerability analysis
- Verify findings to reduce false positives
- Provide specific, actionable remediation steps

## 3. Congratulations!

You've successfully set up automated security reviews for your project. Your development workflow now includes OWASP vulnerability scanning and security analysis to help prevent security issues before they reach production.
