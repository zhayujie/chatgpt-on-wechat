---
name: bocha-search
description: High-quality web search with AI-optimized results. Use when user needs to search the internet for current information, news, or research topics.
homepage: https://open.bocha.cn/
metadata:
  emoji: 🔍
  requires:
    bins: ["curl"]
    env: ["BOCHA_API_KEY"]
  primaryEnv: "BOCHA_API_KEY"
---

# Bocha Search

High-quality web search powered by Bocha AI, optimized for AI consumption. Returns web pages, images, and detailed metadata.

## Setup

This skill requires a Bocha API key. If not configured:

1. Visit https://open.bocha.cn to get an API key
2. Set the key using: `env_config(action="set", key="BOCHA_API_KEY", value="your-key")`
3. Or manually add to `~/cow/.env`: `BOCHA_API_KEY=your-key`

## Usage

**Important**: Scripts are located relative to this skill's base directory.

When you see this skill in `<available_skills>`, note the `<base_dir>` path.

```bash
# General pattern:
bash "<base_dir>/scripts/search.sh" "<query>" [count] [freshness] [summary]

# Parameters:
# - query: Search query (required)
# - count: Number of results (1-50, default: 10)
# - freshness: Time range filter (default: noLimit)
#   Options: noLimit, oneDay, oneWeek, oneMonth, oneYear, YYYY-MM-DD..YYYY-MM-DD
# - summary: Include text summary (true/false, default: false)
```

## Examples

### Basic search
```bash
bash "<base_dir>/scripts/search.sh" "latest AI news"
```

### Search with more results
```bash
bash "<base_dir>/scripts/search.sh" "Python tutorials" 20
```

### Search recent content with summary
```bash
bash "<base_dir>/scripts/search.sh" "阿里巴巴ESG报告" 10 oneWeek true
```

### Search specific date range
```bash
bash "<base_dir>/scripts/search.sh" "tech news" 15 "2025-01-01..2025-02-01"
```

## Response Format

The API returns structured data compatible with Bing Search API:

**Web Pages** (in `data.webPages.value`):
- `name`: Page title
- `url`: Page URL
- `snippet`: Short description
- `summary`: Full text summary (if requested)
- `siteName`: Website name
- `siteIcon`: Website icon URL
- `datePublished`: Publication date (UTC+8)
- `language`: Page language

**Images** (in `data.images.value`):
- `contentUrl`: Image URL
- `hostPageUrl`: Source page URL
- `width`, `height`: Image dimensions
- `thumbnailUrl`: Thumbnail URL

## Notes

- **Optimized for AI**: Results include summaries and structured metadata
- **Time range**: Use `noLimit` for best results (algorithm auto-optimizes time range)
- **Timeout**: 30 seconds
- **Rate limits**: Check your API plan at https://open.bocha.cn
- **Response format**: Compatible with Bing Search API for easy integration
