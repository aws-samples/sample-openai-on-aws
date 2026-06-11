---
title: "Lab 2: Function Calling"
weight: 20
---

In Lab 1 you sent prompts and got text back. But what happens when the model needs information it doesn't have, like today's weather, a customer's order status, or a live database query?

**Function calling** lets the model request that *your code* execute a specific function and return the result. The model doesn't run the function itself. It tells you what to call and with what arguments, then you execute it and feed the result back.

This is the foundation of agentic AI: the model reasons about *which* tool to use, *what* arguments to pass, whether calls can run in parallel, and *how* to incorporate the result into its answer. You'll do it all with custom tools that your own code executes.

**Time:** ~15 minutes **Prerequisites:** Lab 1 complete

---

## 1. How it works

1. You define one or more tools (functions) with names, descriptions, and parameter schemas
2. You send a prompt along with the tool definitions
3. The model decides whether it needs a tool. If yes, it returns a `function_call` output instead of text
4. Your code executes the function with the model's chosen arguments
5. You send the function result back to the model
6. The model uses the result to generate its final text answer

This round-trip is called the **tool use loop**. In Lab 4, you'll see how the Agents SDK automates this loop entirely. Here, you'll do it yourself to understand what's happening under the hood.

| Aspect | Details |
|--------|---------|
| **Tool type** | `function` (client-side) |
| **Who executes** | Your code |
| **Model output** | `function_call` item with name + arguments |
| **Your response** | `function_call_output` item with the result |

:::alert{type="info" header="Function tools vs MCP tools"}
Use **function calling** when the model needs your application, database, AWS account, or business logic that lives in your own code. Use **MCP tools** when you want to connect the model to a remote Model Context Protocol server that publishes its own set of tools. Both are exposed through the same `tools` parameter, which is why the Responses API is a good foundation for agentic workflows.
:::
