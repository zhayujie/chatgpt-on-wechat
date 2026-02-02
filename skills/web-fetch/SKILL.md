---
name: web-fetch
description: Fetch and extract readable content from web pages. Use for lightweight page access without browser automation.
homepage: https://github.com/zhayujie/chatgpt-on-wechat
metadata:
  emoji: 🌐
  requires:
    bins: ["curl"]
  always: true
---

# Web Fetch

Fetch and extract readable content from web pages using curl and basic text processing.

## Usage

**Important**: Scripts are located relative to this skill's base directory.

When you see this skill in `<available_skills>`, note the `<base_dir>` path.

```bash
# General pattern:
bash "<base_dir>/scripts/fetch.sh" <url> [output_file]

# Example (replace <base_dir> with actual path from skill listing):
bash "~/chatgpt-on-wechat/skills/web-fetch/scripts/fetch.sh" "https://example.com"
```

**Parameters:**
- `url`: The HTTP/HTTPS URL to fetch (required)
- `output_file`: Optional file to save the output (default: stdout)

**Returns:**
- Extracted page content with title and text

## Examples

### Fetch a web page
```bash
bash "<base_dir>/scripts/fetch.sh" "https://example.com"
```

### Save to file
```bash
bash "<base_dir>/scripts/fetch.sh" "https://example.com" output.txt
cat output.txt
```

## Notes

- Uses curl for HTTP requests (timeout: 10s)
- Extracts title and basic text content
- Removes HTML tags and scripts
- Works with any standard web page
- No external dependencies beyond curl
