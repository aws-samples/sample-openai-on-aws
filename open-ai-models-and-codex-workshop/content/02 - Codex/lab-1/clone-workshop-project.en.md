---
title: "Clone the workshop project"
weight: 10
---

Before starting the Codex exercises, clone the sample repository branch that contains the workshop project. All Part 2 hands-on tasks assume you are working inside the :code[bedrock-chat]{showCopyAction=false} folder from this branch.

:::alert{type="info" header="Use this branch for Part 2"}
Clone :code[codex-advanced-patterns]{showCopyAction=false} from :code[aws-samples/sample-openai-on-aws]{showCopyAction=false}. The branch includes the :code[bedrock-chat]{showCopyAction=false} project used throughout the Codex labs.
:::

## 1. Clone and enter the project

Run these commands in your terminal:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
mkdir -p ~/workshop
cd ~/workshop
git clone --branch codex-advanced-patterns --single-branch https://github.com/aws-samples/sample-openai-on-aws.git
cd sample-openai-on-aws/bedrock-chat
:::

Your working directory should now be:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
pwd
:::

Expected path:

:::code{showCopyAction="false" language="text"}
~/workshop/sample-openai-on-aws/bedrock-chat
:::

## 2. Install project dependencies

Install the Python dependencies for the chat project:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
python3 -m pip install -r requirements.txt
:::

## 3. Keep using this folder

For the rest of Part 2, open or navigate to:

:::code{showCopyAction="true" language="bash" copyAutoReturn="true"}
cd ~/workshop/sample-openai-on-aws/bedrock-chat
:::

If a later page says "your project directory" or "the chat app project," it means this folder.

## 4. Congratulations!

You have the Part 2 workshop project locally and are ready to open it in the Codex App, IDE, or CLI.
