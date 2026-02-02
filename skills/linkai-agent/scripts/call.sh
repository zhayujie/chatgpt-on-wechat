#!/usr/bin/env bash
# LinkAI Agent Caller
# API Docs: https://api.link-ai.tech/v1/chat/completions

set -euo pipefail

app_code="${1:-}"
question="${2:-}"
model="${3:-}"
stream="${4:-false}"
timeout="${5:-120}"  # Default 120 seconds for video/image generation

if [ -z "$app_code" ]; then
    echo '{"error": "app_code is required", "usage": "bash call.sh <app_code> <question> [model] [stream] [timeout]"}'
    exit 1
fi

if [ -z "$question" ]; then
    echo '{"error": "question is required", "usage": "bash call.sh <app_code> <question> [model] [stream] [timeout]"}'
    exit 1
fi

if [ -z "${LINKAI_API_KEY:-}" ]; then
    echo '{"error": "LINKAI_API_KEY environment variable is not set", "help": "Use env_config to set LINKAI_API_KEY"}'
    exit 1
fi

# API endpoint
api_url="https://api.link-ai.tech/v1/chat/completions"

# Build JSON request body
if [ -n "$model" ]; then
    request_body=$(cat <<EOF
{
  "app_code": "$app_code",
  "model": "$model",
  "messages": [
    {
      "role": "user",
      "content": "$question"
    }
  ],
  "stream": $stream
}
EOF
)
else
    request_body=$(cat <<EOF
{
  "app_code": "$app_code",
  "messages": [
    {
      "role": "user",
      "content": "$question"
    }
  ],
  "stream": $stream
}
EOF
)
fi

# Call LinkAI API
response=$(curl -sS --max-time "$timeout" \
    -X POST \
    -H "Authorization: Bearer $LINKAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$request_body" \
    "$api_url" 2>&1)

curl_exit_code=$?

if [ $curl_exit_code -ne 0 ]; then
    echo "{\"error\": \"Failed to call LinkAI API\", \"details\": \"$response\"}"
    exit 1
fi

# Simple JSON validation
if [[ ! "$response" =~ ^[[:space:]]*[\{\[] ]]; then
    echo "{\"error\": \"Invalid JSON response from API\", \"response\": \"$response\"}"
    exit 1
fi

# Check for API error (top-level error only, not content_filter_result)
if echo "$response" | grep -q '^[[:space:]]*{[[:space:]]*"error"[[:space:]]*:' || echo "$response" | grep -q '"error"[[:space:]]*:[[:space:]]*{[^}]*"code"[[:space:]]*:[[:space:]]*"[^"]*"[^}]*"message"'; then
    # Make sure it's not just content_filter_result inside choices
    if ! echo "$response" | grep -q '"choices"[[:space:]]*:[[:space:]]*\['; then
        # Extract error message
        error_msg=$(echo "$response" | grep -o '"message"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"message"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' | head -1)
        error_code=$(echo "$response" | grep -o '"code"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"code"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' | head -1)
        
        if [ -z "$error_msg" ]; then
            error_msg="Unknown API error"
        fi
        
        # Provide friendly error message for content filter
        if [ "$error_code" = "content_filter_error" ] || echo "$error_msg" | grep -qi "content.*filter"; then
            echo "{\"error\": \"内容安全审核\", \"message\": \"您的问题或应用返回的内容触发了LinkAI的安全审核机制，请换一种方式提问或检查应用配置\", \"details\": \"$error_msg\"}"
        else
            echo "{\"error\": \"LinkAI API error\", \"message\": \"$error_msg\", \"code\": \"$error_code\"}"
        fi
        exit 1
    fi
fi

# For non-stream mode, extract and format the response
if [ "$stream" = "false" ]; then
    # Extract content from response
    content=$(echo "$response" | grep -o '"content"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"content"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' | head -1)
    
    # Extract usage information
    prompt_tokens=$(echo "$response" | grep -o '"prompt_tokens"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' | head -1)
    completion_tokens=$(echo "$response" | grep -o '"completion_tokens"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' | head -1)
    total_tokens=$(echo "$response" | grep -o '"total_tokens"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' | head -1)
    
    if [ -n "$content" ]; then
        # Unescape JSON content
        content=$(echo "$content" | sed 's/\\n/\n/g' | sed 's/\\"/"/g')
        
        cat <<EOF
{
  "app_code": "$app_code",
  "content": "$content",
  "usage": {
    "prompt_tokens": ${prompt_tokens:-0},
    "completion_tokens": ${completion_tokens:-0},
    "total_tokens": ${total_tokens:-0}
  }
}
EOF
    else
        # Return full response if we can't extract content
        echo "$response"
    fi
else
    # For stream mode, return raw response (caller needs to handle streaming)
    echo "$response"
fi
