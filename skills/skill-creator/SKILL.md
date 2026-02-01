---
name: skill-creator
description: Create or update skills. Use when designing, structuring, or packaging skills with scripts, references, and assets. COW simplified version - skills are used locally in workspace.
license: Complete terms in LICENSE.txt
---

# Skill Creator

This skill provides guidance for creating effective skills using the existing tool system.

## About Skills

Skills are modular, self-contained packages that extend the agent's capabilities by providing specialized knowledge, workflows, and tools. They transform a general-purpose agent into a specialized agent equipped with procedural knowledge.

### What Skills Provide

1. **Specialized workflows** - Multi-step procedures for specific domains
2. **Tool integrations** - Instructions for working with specific file formats or APIs
3. **Domain expertise** - Company-specific knowledge, schemas, business logic
4. **Bundled resources** - Scripts, references, and assets for complex tasks

### Core Principle

**Concise is Key**: Only add context the agent doesn't already have. Challenge each piece of information: "Does this justify its token cost?" Prefer concise examples over verbose explanations.

## Skill Structure

Every skill consists of a required SKILL.md file and optional bundled resources:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed
    └── assets/           - Files used in output (templates, icons, fonts, etc.)
```

### SKILL.md Components

**Frontmatter (YAML)** - Required fields:

- **name**: Skill name in hyphen-case (e.g., `weather-api`, `pdf-editor`)
- **description**: **CRITICAL** - Primary triggering mechanism
  - Must clearly describe what the skill does
  - Must explicitly state when to use it
  - Include specific trigger scenarios and keywords
  - All "when to use" info goes here, NOT in body
  - Example: `"PDF document processing with rotation, merging, splitting, and text extraction. Use when user needs to: (1) Rotate PDF pages, (2) Merge multiple PDFs, (3) Split PDF files, (4) Extract text from PDFs."`

**Body (Markdown)** - Loaded after skill triggers:

- Detailed usage instructions
- How to call scripts and read references
- Examples and best practices
- Use imperative/infinitive form ("Use X to do Y")

### Bundled Resources

**scripts/** - When to include:
- Code is repeatedly rewritten
- Deterministic execution needed (avoid LLM randomness)
- Examples: PDF rotation, image processing
- Must test scripts before including

**references/** - When to include:
- **ONLY** when documentation is too large for SKILL.md (>500 lines)
- Database schemas, complex API specs that agent needs to reference
- Agent reads these files into context as needed
- **NOT for**: API reference docs, usage examples, tutorials (put in SKILL.md instead)
- **Rule of thumb**: If it fits in SKILL.md, don't create a separate reference file

**assets/** - When to include:
- Files used in output (not loaded to context)
- Templates, icons, boilerplate code
- Copied or modified in final output

**Important**: Most skills don't need all three. Choose based on actual needs.

### What NOT to Include

Do NOT create auxiliary documentation files:
- README.md - Instructions belong in SKILL.md
- INSTALLATION_GUIDE.md - Setup info belongs in SKILL.md
- CHANGELOG.md - Not needed for local skills
- API_REFERENCE.md - Put API docs directly in SKILL.md
- USAGE_EXAMPLES.md - Put examples directly in SKILL.md
- Any other documentation files - Everything goes in SKILL.md unless it's too large

**Critical Rule**: Only create files that the agent will actually execute (scripts) or that are too large for SKILL.md (references). Documentation, examples, and guides ALL belong in SKILL.md.

## Skill Creation Process

**COW Simplified Version** - Skills are used locally, no packaging/sharing needed.

1. **Understand** - Clarify use cases with concrete examples
2. **Plan** - Identify needed scripts, references, assets
3. **Initialize** - Run init_skill.py to create template
4. **Edit** - Implement SKILL.md and resources
5. **Validate** (optional) - Run quick_validate.py to check format
6. **Iterate** - Improve based on real usage

## Skill Naming

- Use lowercase letters, digits, and hyphens only; normalize user-provided titles to hyphen-case (e.g., "Plan Mode" -> `plan-mode`).
- When generating names, generate a name under 64 characters (letters, digits, hyphens).
- Prefer short, verb-led phrases that describe the action.
- Namespace by tool when it improves clarity or triggering (e.g., `gh-address-comments`, `linear-address-issue`).
- Name the skill folder exactly after the skill name.

## Step-by-Step Guide

### Step 1: Understanding the Skill with Concrete Examples

Skip this step only when the skill's usage patterns are already clearly understood. It remains valuable even when working with an existing skill.

To create an effective skill, clearly understand concrete examples of how the skill will be used. This understanding can come from either direct user examples or generated examples that are validated with user feedback.

For example, when building an image-editor skill, relevant questions include:

- "What functionality should the image-editor skill support? Editing, rotating, anything else?"
- "Can you give some examples of how this skill would be used?"
- "I can imagine users asking for things like 'Remove the red-eye from this image' or 'Rotate this image'. Are there other ways you imagine this skill being used?"
- "What would a user say that should trigger this skill?"

To avoid overwhelming users, avoid asking too many questions in a single message. Start with the most important questions and follow up as needed for better effectiveness.

Conclude this step when there is a clear sense of the functionality the skill should support.

### Step 2: Planning the Reusable Skill Contents

To turn concrete examples into an effective skill, analyze each example by:

1. Considering how to execute on the example from scratch
2. Identifying what scripts, references, and assets would be helpful when executing these workflows repeatedly

**Planning Checklist**:
- ✅ **Always needed**: SKILL.md with clear description and usage instructions
- ✅ **scripts/**: Only if code needs to be executed (not just shown as examples)
- ❌ **references/**: Rarely needed - only if documentation is >500 lines and can't fit in SKILL.md
- ✅ **assets/**: Only if files are used in output (templates, boilerplate, etc.)

Example: When building a `pdf-editor` skill to handle queries like "Help me rotate this PDF," the analysis shows:

1. Rotating a PDF requires re-writing the same code each time
2. A `scripts/rotate_pdf.py` script would be helpful to store in the skill
3. ❌ Don't create `references/api-docs.md` - put API info in SKILL.md instead

Example: When designing a `frontend-webapp-builder` skill for queries like "Build me a todo app" or "Build me a dashboard to track my steps," the analysis shows:

1. Writing a frontend webapp requires the same boilerplate HTML/React each time
2. An `assets/hello-world/` template containing the boilerplate HTML/React project files would be helpful to store in the skill
3. ❌ Don't create `references/usage-examples.md` - put examples in SKILL.md instead

Example: When building a `big-query` skill to handle queries like "How many users have logged in today?" the analysis shows:

1. Querying BigQuery requires re-discovering the table schemas and relationships each time
2. A `references/schema.md` file documenting the table schemas would be helpful to store in the skill (ONLY because schemas are very large)
3. ❌ Don't create separate `references/query-examples.md` - put examples in SKILL.md instead

To establish the skill's contents, analyze each concrete example to create a list of the reusable resources to include: scripts, references, and assets. **Default to putting everything in SKILL.md unless there's a compelling reason to separate it.**

### Step 3: Initialize the Skill

At this point, it is time to actually create the skill.

Skip this step only if the skill being developed already exists, and iteration is needed. In this case, continue to the next step.

When creating a new skill from scratch, always run the `init_skill.py` script. The script conveniently generates a new template skill directory that automatically includes everything a skill requires, making the skill creation process much more efficient and reliable.

Usage:

```bash
scripts/init_skill.py <skill-name> --path <output-directory> [--resources scripts,references,assets] [--examples]
```

Examples:

```bash
scripts/init_skill.py my-skill --path ~/cow/skills
scripts/init_skill.py my-skill --path ~/cow/skills --resources scripts,references
scripts/init_skill.py my-skill --path ~/cow/skills --resources scripts --examples
```

The script:

- Creates the skill directory at the specified path
- Generates a SKILL.md template with proper frontmatter and TODO placeholders
- Optionally creates resource directories based on `--resources`
- Optionally adds example files when `--examples` is set

After initialization, customize the SKILL.md and add resources as needed. If you used `--examples`, replace or delete placeholder files.

**Important**: Always create skills in workspace directory (`~/cow/skills`), NOT in project directory.

### Step 4: Edit the Skill

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of the agent to use. Include information that would be beneficial and non-obvious to the agent. Consider what procedural knowledge, domain-specific details, or reusable assets would help another agent instance execute these tasks more effectively.

#### Learn Proven Design Patterns

Consult these helpful guides based on your skill's needs:

- **Multi-step processes**: See references/workflows.md for sequential workflows and conditional logic
- **Specific output formats or quality standards**: See references/output-patterns.md for template and example patterns

These files contain established best practices for effective skill design.

#### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified above: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

**Available Base Tools**:

The agent has access to these core tools that you can leverage in your skill:
- **bash**: Execute shell commands (use for curl, ls, grep, sed, awk, bc for calculations, etc.)
- **read**: Read file contents
- **write**: Write files
- **edit**: Edit files with search/replace

**Minimize Dependencies**:
- ✅ **Prefer bash + curl** for HTTP API calls (no Python dependencies)
- ✅ **Use bash tools** (grep, sed, awk) for text processing
- ✅ **Keep scripts simple** - if bash can do it, no need for Python (document packages/versions if Python is used)

**Important Guidelines**:
- **scripts/**: Only create scripts that will be executed. Test all scripts before including.
- **references/**: ONLY create if documentation is too large for SKILL.md (>500 lines). Most skills don't need this.
- **assets/**: Only include files used in output (templates, icons, etc.)
- **Default approach**: Put everything in SKILL.md unless there's a specific reason not to.

Added scripts must be tested by actually running them to ensure there are no bugs and that the output matches what is expected. If there are many similar scripts, only a representative sample needs to be tested to ensure confidence that they all work while balancing time to completion.

If you used `--examples`, delete any placeholder files that are not needed for the skill. Only create resource directories that are actually required.

#### Update SKILL.md

**Writing Guidelines:** Always use imperative/infinitive form.

##### Frontmatter

Write the YAML frontmatter with `name`, `description`, and optional `metadata`:

- `name`: The skill name
- `description`: This is the primary triggering mechanism for your skill, and helps the agent understand when to use the skill.
  - Include both what the Skill does and specific triggers/contexts for when to use it.
  - Include all "when to use" information here - Not in the body. The body is only loaded after triggering, so "When to Use This Skill" sections in the body are not helpful to the agent.
  - Example description for a `docx` skill: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when the agent needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
- `metadata`: (Optional) Specify requirements and configuration
  - `requires.bins`: Required binaries (e.g., `["curl", "jq"]`)
  - `requires.env`: Required environment variables (e.g., `["OPENAI_API_KEY"]`)
  - `primaryEnv`: Primary environment variable name (for API keys)
  - `always`: Set to `true` to always load regardless of requirements
  - `emoji`: Skill icon (optional)

**API Key Requirements**:

If your skill needs an API key, declare it in metadata:

```yaml
---
name: my-search
description: Search using MyAPI
metadata:
  requires:
    bins: ["curl"]
    env: ["MYAPI_KEY"]
  primaryEnv: "MYAPI_KEY"
---
```

**Auto-enable rule**: Skills are automatically enabled when required environment variables are set, and automatically disabled when missing. No manual configuration needed.

##### Body

Write instructions for using the skill and its bundled resources.

**If your skill requires an API key**, include setup instructions in the body:

```markdown
## Setup

This skill requires an API key from [Service Name].

1. Visit https://service.com to get an API key
2. Configure it using: `env_config(action="set", key="SERVICE_API_KEY", value="your-key")`
3. Or manually add to `~/cow/.env`: `SERVICE_API_KEY=your-key`
4. Restart the agent for changes to take effect

## Usage
...
```

The bash script should check for the key and provide helpful error messages:

```bash
#!/usr/bin/env bash
if [ -z "${SERVICE_API_KEY:-}" ]; then
    echo "Error: SERVICE_API_KEY not set"
    echo "Please configure your API key first (see SKILL.md)"
    exit 1
fi

curl -H "Authorization: Bearer $SERVICE_API_KEY" ...
```

**Script Path Convention**:

When writing SKILL.md instructions, remember that:
- Skills are listed in `<available_skills>` with a `<base_dir>` path
- Scripts should be referenced as: `<base_dir>/scripts/script_name.sh`
- The AI will see the base_dir and can construct the full path

Example instruction in SKILL.md:
```markdown
## Usage

Scripts are in this skill's base directory (shown in skill listing).

bash "<base_dir>/scripts/my_script.sh" <args>
```

### Step 5: Validate (Optional)

Validate skill format:

```bash
scripts/quick_validate.py <path/to/skill-folder>
```

Example:

```bash
scripts/quick_validate.py ~/cow/skills/weather-api
```

Validation checks:
- YAML frontmatter format and required fields
- Skill naming conventions (hyphen-case, lowercase)
- Description completeness and quality
- File organization

**Note**: Validation is optional in COW. Mainly useful for troubleshooting format issues.

### Step 6: Iterate

Improve based on real usage:

1. Use skill on real tasks
2. Notice struggles or inefficiencies
3. Identify needed updates to SKILL.md or resources
4. Implement changes and test again

## Progressive Disclosure

Skills use three-level loading:

1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - Loaded when skill triggers (<5k words)
3. **Resources** - Loaded as needed by agent

**Best practices**:
- Keep SKILL.md under 500 lines
- Split complex content into `references/` files
- Reference these files clearly in SKILL.md

**Pattern**: For skills with multiple variants/frameworks:
- Keep core workflow in SKILL.md
- Move variant-specific details to separate reference files
- Agent loads only relevant files

Example:
```
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

When user chooses AWS, agent only reads aws.md.
