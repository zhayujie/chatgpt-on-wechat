#!/usr/bin/env bash
# Bocha Web Search API wrapper
# API Docs: https://open.bocha.cn/

set -euo pipefail

query="${1:-}"
count="${2:-10}"
freshness="${3:-noLimit}"
summary="${4:-false}"

if [ -z "$query" ]; then
    echo '{"error": "Query is required", "usage": "bash search.sh <query> [count] [freshness] [summary]"}'
    exit 1
fi

if [ -z "${BOCHA_API_KEY:-}" ]; then
    echo '{"error": "BOCHA_API_KEY environment variable is not set", "help": "Visit https://open.bocha.cn to get an API key"}'
    exit 1
fi

# Validate count (1-50)
if ! [[ "$count" =~ ^[0-9]+$ ]] || [ "$count" -lt 1 ] || [ "$count" -gt 50 ]; then
    count=10
fi

# Build JSON request body
request_body=$(cat <<EOF
{
  "query": "$query",
  "count": $count,
  "freshness": "$freshness",
  "summary": $summary
}
EOF
)

# Call Bocha API
response=$(curl -sS --max-time 30 \
    -X POST \
    -H "Authorization: Bearer $BOCHA_API_KEY" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "$request_body" \
    "https://api.bocha.cn/v1/web-search" 2>&1)

curl_exit_code=$?

if [ $curl_exit_code -ne 0 ]; then
    echo "{\"error\": \"Failed to call Bocha API\", \"details\": \"$response\"}"
    exit 1
fi

# Simple JSON validation - check if response starts with { or [
if [[ ! "$response" =~ ^[[:space:]]*[\{\[] ]]; then
    echo "{\"error\": \"Invalid JSON response from API\", \"response\": \"$response\"}"
    exit 1
fi

# Extract API code using grep and sed (basic JSON parsing)
api_code=$(echo "$response" | grep -o '"code"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' | head -1)

# If code extraction failed or code is not 200, check for error
if [ -n "$api_code" ] && [ "$api_code" != "200" ]; then
    # Try to extract error message
    api_msg=$(echo "$response" | grep -o '"msg"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"msg"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' | head -1)
    if [ -z "$api_msg" ]; then
        api_msg="Unknown error"
    fi
    echo "{\"error\": \"API returned error\", \"code\": $api_code, \"message\": \"$api_msg\"}"
    exit 1
fi

# Return the full response
echo "$response"
