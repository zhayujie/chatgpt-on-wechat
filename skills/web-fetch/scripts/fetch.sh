#!/usr/bin/env bash
# Fetch and extract readable content from a web page

set -euo pipefail

url="${1:-}"
output_file="${2:-}"

if [ -z "$url" ]; then
    echo "Error: URL is required"
    echo "Usage: bash fetch.sh <url> [output_file]"
    exit 1
fi

# Validate URL
if [[ ! "$url" =~ ^https?:// ]]; then
    echo "Error: Invalid URL (must start with http:// or https://)"
    exit 1
fi

# Fetch the page with curl
html=$(curl -sS -L --max-time 10 \
    -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
    -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
    "$url" 2>&1) || {
    echo "Error: Failed to fetch URL: $url"
    exit 1
}

# Extract title
title=$(echo "$html" | grep -oP '(?<=<title>).*?(?=</title>)' | head -1 || echo "Untitled")

# Remove script and style tags
text=$(echo "$html" | sed 's/<script[^>]*>.*<\/script>//gI' | sed 's/<style[^>]*>.*<\/style>//gI')

# Remove HTML tags
text=$(echo "$text" | sed 's/<[^>]*>//g')

# Clean up whitespace
text=$(echo "$text" | tr -s ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

# Format output
result="Title: $title

Content:
$text"

# Output to file or stdout
if [ -n "$output_file" ]; then
    echo "$result" > "$output_file"
    echo "Content saved to: $output_file"
else
    echo "$result"
fi
