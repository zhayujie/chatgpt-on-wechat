---
name: linkai-agent
description: Call LinkAI applications and workflows. Use bash command to execute like 'bash <base_dir>/scripts/call.sh <app_code> <question>'.
homepage: https://link-ai.tech
metadata:
  emoji: 🤖
  requires:
    bins: ["curl"]
    env: ["LINKAI_API_KEY"]
  primaryEnv: "LINKAI_API_KEY"
---

# LinkAI Agent Caller

Call LinkAI applications and workflows through API. Supports multiple apps/workflows configured in config.json.

The available apps are dynamically loaded from `config.json` at skill loading time.

## Setup

This skill requires a LinkAI API key. If not configured:

1. Get your API key from https://link-ai.tech/console/api-keys
2. Set the key using: `env_config(action="set", key="LINKAI_API_KEY", value="your-key")`

## Configuration

1. Copy `config.json.template` to `config.json`
2. Configure your apps/workflows:

```json
{
  "apps": [
    {
      "app_code": "your_app_code",
      "app_name": "App Name",
      "app_description": "What this app does"
    }
  ]
}
```

3. The skill description will be automatically updated when the agent loads this skill

## Usage

**Important**: Scripts are located relative to this skill's base directory.

When you see this skill in `<available_skills>`, note the `<base_dir>` path.

**CRITICAL**: Always use `bash` command to execute the script:

```bash
# General pattern (MUST start with bash):
bash "<base_dir>/scripts/call.sh" "<app_code>" "<question>" [model] [stream] [timeout]

# DO NOT execute the script directly like this (WRONG):
# "<base_dir>/scripts/call.sh" ...

# Parameters:
# - app_code: LinkAI app or workflow code (required)
# - question: User question (required)
# - model: Override model (optional, uses app default if not specified)
# - stream: Enable streaming (true/false, default: false)
# - timeout: curl timeout in seconds (default: 120, recommended for video/image generation)
```

**IMPORTANT - Timeout Configuration**:
- The script has a **default timeout of 120 seconds** (suitable for most cases)
- For complex tasks (video generation, large workflows), pass a longer timeout as the 5th parameter
- The bash tool also needs sufficient timeout - set its `timeout` parameter accordingly
- Example: `bash(command="bash <script> <app_code> <question> '' 'false' 180", timeout=200)`

## Examples

### Call an app (uses default 60s timeout)
```bash
bash(command='bash "<base_dir>/scripts/call.sh" "G7z6vKwp" "What is AI?"', timeout=60)
```

### Call an app with specific model
```bash
bash(command='bash "<base_dir>/scripts/call.sh" "G7z6vKwp" "Explain machine learning" "LinkAI-4.1"', timeout=60)
```

### Call a workflow with custom timeout (video generation)
```bash
# Pass timeout as 5th parameter to script, and set bash timeout slightly longer
bash(command='bash "<base_dir>/scripts/call.sh" "workflow_code" "Generate a sunset video" "" "false" "180"', timeout=180)
```
```bash
bash "<base_dir>/scripts/call.sh" "workflow_code" "Analyze this data: ..."
```

## Supported Models

You can specify any LinkAI supported model:
- `LinkAI-4.1` - Latest GPT-4.1 model (1000K context)
- `LinkAI-4.1-mini` - GPT-4.1 mini (1000K context)
- `LinkAI-4o` - GPT-4o model (128K context)
- `LinkAI-4o-mini` - GPT-4o mini (128K context)
- `deepseek-chat` - DeepSeek-V3 (64K context)
- `deepseek-reasoner` - DeepSeek-R1 reasoning model
- `claude-4-sonnet` - Claude 4 Sonnet (200K context)
- `gemini-2.5-pro` - Gemini 2.5 Pro (1000K context)
- And many more...

Full model list: https://link-ai.tech/console/models

## Response Format

Success response:
```json
{
  "app_code": "G7z6vKwp",
  "content": "AI stands for Artificial Intelligence...",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

Error response:
```json
{
  "error": "Error description",
  "message": "Detailed error message"
}
```

## Features

- ✅ **Multiple Apps**: Configure and call multiple LinkAI apps/workflows
- ✅ **Dynamic Loading**: Apps are loaded from config.json at runtime
- ✅ **Model Override**: Optionally specify model per request
- ✅ **Streaming Support**: Enable streaming output
- ✅ **Knowledge Base**: Apps can use configured knowledge bases
- ✅ **Plugins**: Apps can use enabled plugins (image recognition, web search, etc.)
- ✅ **Workflows**: Execute complex multi-step workflows

## Notes

- Each app/workflow maintains its own configuration (prompt, model, temperature, etc.)
- Apps can have knowledge bases attached for domain-specific Q&A
- Workflows execute from start node to end node and return final output
- Token usage and costs depend on the model used
- See LinkAI documentation for pricing: https://link-ai.tech/console/funds
- The skill description is automatically generated from config.json when loaded

## Troubleshooting

**"LINKAI_API_KEY environment variable is not set"**
- Use env_config tool to set the API key

**"app_code is required"**
- Make sure you're passing the app_code as the first parameter

**"应用不存在" (App not found)**
- Check that the app_code is correct
- Ensure you have access to the app

**"账号积分额度不足" (Insufficient credits)**
- Top up your LinkAI account credits
