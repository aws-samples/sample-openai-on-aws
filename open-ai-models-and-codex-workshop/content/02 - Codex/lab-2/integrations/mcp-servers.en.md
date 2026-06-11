---
title: "(Optional) Connect to external tools with MCP servers"
weight: 1
---

Model Context Protocol (MCP) servers extend Codex's capabilities by providing access to external tools, data sources, and specialized functionality. AWS MCP Servers serve as an excellent example of how these integrations work in practice.

:::alert{type=info header="New: AWS Labs agent plugins"}
Explore [awslabs/mcp](https://awslabs.github.io/mcp/) — a curated registry of MCP servers for AI coding assistants, maintained by AWS Labs. Browse ready-made integrations you can add to your workflow.
:::

## 1. What is the Model Context Protocol (MCP)?

The Model Context Protocol (MCP) is an open protocol that enables seamless integration between LLM applications and external data sources and tools. MCP servers are lightweight programs that expose specific capabilities through this standardized protocol.

:::alert{type=info header="Did you know?"}
The Model Context Protocol is an open source project created by Anthropic and open to contributions from the entire community. For more information on MCP, you can find further documentation [here](https://modelcontextprotocol.io/).
:::

## 2. Why MCP servers?

MCP servers enhance the capabilities of foundation models in several key ways:

- **Improved output quality** - Reduces hallucinations and provides accurate technical details by surfacing relevant information directly in the model's context
- **Access to latest documentation** - Bridges knowledge gaps with up-to-date AWS documentation, APIs, and SDKs
- **Workflow automation** - Converts common workflows like CDK and Terraform into tools that models can use directly
- **Specialized domain knowledge** - Provides deep AWS service expertise that enhances cloud development responses

:::alert{type=info header="Installation documentation"}
For detailed installation instructions and configuration options, refer to the [AWS MCP Servers installation documentation](https://awslabs.github.io/mcp/installation).
:::

## 3. Installing AWS MCP servers with Codex

You'll install the AWS Cost Explorer MCP Server, which provides specialized cost management capabilities:

- Query AWS Cost Explorer data
- Generate cost reports and analysis
- Provide actionable recommendations for cost optimization

1. In the terminal, add the MCP server to your Codex configuration. First, create or edit your MCP configuration file:

:::code{showCopyAction="true" language="bash"}
mkdir -p ~/.codex
cat > ~/.codex/mcp.json << 'EOF'
{
  "mcpServers": {
    "cost-explorer-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["awslabs.cost-explorer-mcp-server@latest"]
    }
  }
}
EOF
:::

:::alert{type="info" header="MCP server scope"}
You can configure MCP servers globally in :code[~/.codex/mcp.json]{showCopyAction=true} or per-project in a :code[.mcp.json]{showCopyAction=true} file at your project's root directory.
:::

2. Start Codex:

:::code{showCopyAction="true" language="bash"}
codex
:::

3. View your installed MCP servers:

:::code{showCopyAction="true" language="text"}
/mcp
:::

This displays a list of all installed MCP servers, their status, and available commands.

4. Test the Cost Explorer functionality:

:::code{showCopyAction="true" language="text"}
Can you help me analyze my AWS costs using the AWS Cost Explorer MCP?
:::

:::alert{type="info" header="Workshop environment note"}
At AWS-run events, no cost data may be available in the workshop AWS account. However, you can still explore its cost intelligence capabilities and how MCP servers enable Codex to analyze AWS costs, provide optimization recommendations, and surface actionable insights directly within your development workflow.
:::

## 4. Explore more AWS MCP servers

![AWS MCP Servers](/static/images/codex/aws-mcp-servers.png)

The AWS MCP Servers suite includes 60+ specialized servers for different AWS workflows and services. Here are some particularly useful ones:

- **AWS Core MCP Server** - A starting point for using AWS MCP servers through a dynamic proxy server strategy. Provides planning and orchestration with prompt understanding and translation to AWS services.
- **AWS CDK/Terraform MCP Server** - Infrastructure as code with security compliance
- **AWS Diagram MCP Server** - Generate architecture diagrams from your infrastructure
- **Amazon Bedrock Knowledge Bases Retrieval MCP Server** - Query knowledge bases with citations
- **Git Repo Research MCP Server** - Semantic code search and repository analysis
- **AWS Pricing MCP Server** - Pre-deployment cost estimation for AWS services

Explore the complete collection at [AWS MCP Servers](https://awslabs.github.io/mcp/) to find more servers that can enhance your development workflow.

## 5. Congratulations!

You've successfully integrated MCP servers into Codex, extending its capabilities with real-time AWS documentation and cost analysis tools. You now understand how MCP servers bridge the gap between foundation models and external data sources, enabling Codex to provide specialized AWS guidance and actionable insights directly within your development environment.
