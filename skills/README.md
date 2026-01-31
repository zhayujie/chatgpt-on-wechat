# Skills Directory

This directory contains skills for the COW agent system. Skills are markdown files that provide specialized instructions for specific tasks.

## What are Skills?

Skills are reusable instruction sets that help the agent perform specific tasks more effectively. Each skill:

- Provides context-specific guidance
- Documents best practices
- Includes examples and usage patterns
- Can have requirements (binaries, environment variables, etc.)

## Skill Structure

Each skill is a markdown file (`SKILL.md`) in its own directory with frontmatter:

```markdown
---
name: skill-name
description: Brief description of what the skill does
metadata: {"cow":{"emoji":"🎯","requires":{"bins":["tool"]}}}
---

# Skill Name

Detailed instructions and examples...
```

## Available Skills

- **calculator**: Mathematical calculations and expressions
- **web-search**: Search the web for current information
- **file-operations**: Read, write, and manage files

## Creating Custom Skills

To create a new skill:

1. Create a directory: `skills/my-skill/`
2. Create `SKILL.md` with frontmatter and content
3. Restart the agent to load the new skill

### Frontmatter Fields

- `name`: Skill name (must match directory name)
- `description`: Brief description (required)
- `metadata`: JSON object with additional configuration
  - `emoji`: Display emoji
  - `always`: Always include this skill (default: false)
  - `primaryEnv`: Primary environment variable needed
  - `os`: Supported operating systems (e.g., ["darwin", "linux"])
  - `requires`: Requirements object
    - `bins`: Required binaries
    - `env`: Required environment variables
    - `config`: Required config paths
- `disable-model-invocation`: If true, skill won't be shown to model (default: false)
- `user-invocable`: If false, users can't invoke directly (default: true)

### Example Skill

```markdown
---
name: my-tool
description: Use my-tool to process data
metadata: {"cow":{"emoji":"🔧","requires":{"bins":["my-tool"],"env":["MY_TOOL_API_KEY"]}}}
---

# My Tool Skill

Use this skill when you need to process data with my-tool.

## Prerequisites

- Install my-tool: `pip install my-tool`
- Set `MY_TOOL_API_KEY` environment variable

## Usage

\`\`\`python
# Example usage
my_tool_command("input data")
\`\`\`
```

## Skill Loading

Skills are loaded from multiple locations with precedence:

1. **Workspace skills** (highest): `workspace/skills/` - Project-specific skills
2. **Managed skills**: `~/.cow/skills/` - User-installed skills
3. **Bundled skills** (lowest): Built-in skills

Skills with the same name in higher-precedence locations override lower ones.

## Skill Requirements

Skills can specify requirements that determine when they're available:

- **OS requirements**: Only load on specific operating systems
- **Binary requirements**: Only load if required binaries are installed
- **Environment variables**: Only load if required env vars are set
- **Config requirements**: Only load if config values are set

## Best Practices

1. **Clear descriptions**: Write clear, concise skill descriptions
2. **Include examples**: Provide practical usage examples
3. **Document prerequisites**: List all requirements clearly
4. **Use appropriate metadata**: Set correct requirements and flags
5. **Keep skills focused**: Each skill should have a single, clear purpose

## Workspace Skills

You can create workspace-specific skills in your agent's workspace:

```
workspace/
  skills/
    custom-skill/
      SKILL.md
```

These skills are only available when working in that specific workspace.
