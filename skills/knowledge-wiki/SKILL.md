---
name: knowledge-wiki
description: Manage the personal knowledge wiki. Use when the user shares articles, documents, or asks to organize knowledge; when a conversation produces insights worth preserving as structured knowledge; or when the user asks about the knowledge base.
metadata:
  cowagent:
    always: true
---

# Knowledge Wiki

Maintain a persistent, structured knowledge base in the `knowledge/` directory.

## Core Operations

### 1. Ingest — User shares an article, document, or resource

1. Read and understand the source material
2. Extract key facts, entities, concepts, and insights
3. Create or update relevant pages:
   - `knowledge/sources/<slug>.md` — source summary
   - `knowledge/entities/<name>.md` — people, companies, projects mentioned
   - `knowledge/concepts/<topic>.md` — new concepts or topics discussed
4. Update `knowledge/index.md` — add one-line entry per new/updated page
5. Append to `knowledge/log.md`

### 2. Synthesize — Conversation produces valuable structured knowledge

1. Create `knowledge/analysis/<slug>.md` with the structured analysis
2. Update related entity/concept pages with cross-references
3. Update `knowledge/index.md` and `knowledge/log.md`

### 3. Query — User asks about accumulated knowledge

1. Check `knowledge/index.md` (already in your context) for relevant pages
2. Read specific pages with the `read` tool
3. Supplement with `memory_search` if needed

## Page Format

```markdown
# Page Title

Content here. Reference other pages with markdown links:
[Related Entity](../entities/related-entity.md)

## Key Points

- ...

## Sources

- [Source Title](../sources/source-slug.md)
```

## Index Format (`knowledge/index.md`)

Flat list, one line per page: `[Title](path) — one-line summary`. No tables, no emoji, no template headers.

```markdown
# Knowledge Index

## Concepts
- [Topic Name](concepts/topic-name.md) — one-line description

## Sources
- [Article Title](sources/article-slug.md) — one-line summary

## Entities
- [Entity Name](entities/entity-name.md) — one-line description

## Analysis
- [Analysis Title](analysis/analysis-slug.md) — one-line summary
```

## Log Format (`knowledge/log.md`)

Append-only, newest at bottom:

```markdown
## [2026-04-09] ingest | DeepSeek-R1 Deploy Guide
## [2026-04-09] synthesize | Memory System Design Analysis
```

## Guidelines

- **File naming**: lowercase kebab-case (e.g. `machine-learning.md`)
- **One topic per page**: link between pages rather than duplicating
- **Update, don't duplicate**: if a page exists, update it
- **Index is mandatory**: always update `knowledge/index.md` after any change
- **Be concise**: capture essence, not copy entire sources
