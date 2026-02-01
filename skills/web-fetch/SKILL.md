---
name: web-fetch
description: Fetch and extract readable content from web pages
homepage: https://github.com/zhayujie/chatgpt-on-wechat
metadata:
  emoji: 🌐
  requires:
    bins: ["curl"]
---

# Web Fetch

Fetch and extract readable content from web pages using curl and basic text processing.

## Usage

Use the provided script to fetch a URL and extract its content:

```bash
bash scripts/fetch.sh <url> [output_file]
```

**Parameters:**
- `url`: The HTTP/HTTPS URL to fetch (required)
- `output_file`: Optional file to save the output (default: stdout)

**Returns:**
- Extracted page content with title and text

## Examples

### Fetch a web page
```bash
bash scripts/fetch.sh "https://example.com"
```

### Save to file
```bash
bash scripts/fetch.sh "https://example.com" output.txt
cat output.txt
```

## Notes

- Uses curl for HTTP requests (timeout: 20s)
- Extracts title and basic text content
- Removes HTML tags and scripts
- Works with any standard web page
- No external dependencies beyond curl
