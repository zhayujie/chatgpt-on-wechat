#!/usr/bin/env bash
# OpenAI Vision API wrapper
# API Docs: https://platform.openai.com/docs/guides/vision

set -euo pipefail

image_input="${1:-}"
question="${2:-}"
model="${3:-gpt-4.1-mini}"

if [ -z "$image_input" ]; then
    echo '{"error": "Image path or URL is required", "usage": "bash vision.sh <image_path_or_url> <question> [model]"}'
    exit 1
fi

if [ -z "$question" ]; then
    echo '{"error": "Question is required", "usage": "bash vision.sh <image_path_or_url> <question> [model]"}'
    exit 1
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo '{"error": "OPENAI_API_KEY environment variable is not set", "help": "Visit https://platform.openai.com/api-keys to get an API key"}'
    exit 1
fi

# Set API base URL (default to OpenAI's official endpoint)
api_base="${OPENAI_API_BASE:-https://api.openai.com/v1}"
# Remove trailing slash if present
api_base="${api_base%/}"

# Determine if input is a URL or local file
if [[ "$image_input" =~ ^https?:// ]]; then
    # It's a URL - use it directly
    image_url="$image_input"
    
    # Build JSON request body with URL
    request_body=$(cat <<EOF
{
  "model": "$model",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "$question"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "$image_url"
          }
        }
      ]
    }
  ],
  "max_tokens": 1000
}
EOF
)
else
    # It's a local file - need to encode as base64
    if [ ! -f "$image_input" ]; then
        echo "{\"error\": \"Image file not found\", \"path\": \"$image_input\"}"
        exit 1
    fi
    
    # Check file size and compress if needed to avoid "Argument list too long" error
    # Files larger than 1MB should be compressed
    file_size=$(wc -c < "$image_input" | tr -d ' ')
    max_size=1048576  # 1MB
    
    image_to_encode="$image_input"
    temp_compressed=""
    
    if [ "$file_size" -gt "$max_size" ]; then
        # File is too large, compress it
        temp_compressed=$(mktemp "${TMPDIR:-/tmp}/vision_compressed_XXXXXX.jpg")
        
        # Use sips (macOS) or convert (ImageMagick) to compress
        if command -v sips &> /dev/null; then
            # macOS: resize to max 800px on longest side
            $(command -v sips) -Z 800 "$image_input" --out "$temp_compressed" &> /dev/null
            if [ $? -eq 0 ]; then
                image_to_encode="$temp_compressed"
                >&2 echo "[vision.sh] Compressed large image ($(($file_size / 1024))KB) to avoid parameter limit"
            fi
        elif command -v convert &> /dev/null; then
            # Linux: use ImageMagick
            convert "$image_input" -resize 800x800\> "$temp_compressed" 2>/dev/null
            if [ $? -eq 0 ]; then
                image_to_encode="$temp_compressed"
                >&2 echo "[vision.sh] Compressed large image ($(($file_size / 1024))KB) to avoid parameter limit"
            fi
        fi
    fi
    
    # Detect image format from file extension
    extension="${image_to_encode##*.}"
    extension_lower=$(echo "$extension" | tr '[:upper:]' '[:lower:]')
    
    case "$extension_lower" in
        jpg|jpeg)
            mime_type="image/jpeg"
            ;;
        png)
            mime_type="image/png"
            ;;
        gif)
            mime_type="image/gif"
            ;;
        webp)
            mime_type="image/webp"
            ;;
        *)
            echo "{\"error\": \"Unsupported image format\", \"extension\": \"$extension\", \"supported\": [\"jpg\", \"jpeg\", \"png\", \"gif\", \"webp\"]}"
            # Clean up temp file if exists
            [ -n "$temp_compressed" ] && rm -f "$temp_compressed"
            exit 1
            ;;
    esac
    
    # Encode image to base64
    if command -v base64 &> /dev/null; then
        # macOS and most Linux systems
        base64_cmd=$(command -v base64)
        base64_image=$($base64_cmd -i "$image_to_encode" 2>/dev/null || $base64_cmd "$image_to_encode" 2>/dev/null)
    else
        echo '{"error": "base64 command not found", "help": "Please install base64 utility"}'
        # Clean up temp file if exists
        [ -n "$temp_compressed" ] && rm -f "$temp_compressed"
        exit 1
    fi
    
    # Clean up temp compressed file
    [ -n "$temp_compressed" ] && rm -f "$temp_compressed"
    
    if [ -z "$base64_image" ]; then
        echo "{\"error\": \"Failed to encode image to base64\", \"path\": \"$image_input\"}"
        exit 1
    fi
    
    # Escape question for JSON (replace " with \")
    escaped_question=$(echo "$question" | sed 's/"/\\"/g')
    
    # Build JSON request body with base64 image
    # Note: Using printf to avoid issues with special characters
    request_body=$(cat <<EOF
{
  "model": "$model",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "$escaped_question"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:$mime_type;base64,$base64_image"
          }
        }
      ]
    }
  ],
  "max_tokens": 1000
}
EOF
)
fi

# Call OpenAI API
curl_cmd=$(command -v curl)
response=$($curl_cmd -sS --max-time 60 \
    -X POST \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$request_body" \
    "$api_base/chat/completions" 2>&1)

curl_exit_code=$?

if [ $curl_exit_code -ne 0 ]; then
    echo "{\"error\": \"Failed to call OpenAI API\", \"details\": \"$response\"}"
    exit 1
fi

# Simple JSON validation - check if response starts with { or [
if [[ ! "$response" =~ ^[[:space:]]*[\{\[] ]]; then
    echo "{\"error\": \"Invalid JSON response from API\", \"response\": \"$response\"}"
    exit 1
fi

# Check for API error (look for "error" field in response)
if echo "$response" | grep -q '"error"[[:space:]]*:[[:space:]]*{'; then
    # Extract error message if possible
    error_msg=$(echo "$response" | grep -o '"message"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"message"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' | head -1)
    if [ -z "$error_msg" ]; then
        error_msg="Unknown API error"
    fi
    echo "{\"error\": \"OpenAI API error\", \"message\": \"$error_msg\", \"response\": $response}"
    exit 1
fi

# Extract the content from the response
# The response structure is: choices[0].message.content
content=$(echo "$response" | grep -o '"content"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/"content"[[:space:]]*:[[:space:]]*"\(.*\)"/\1/' | head -1)

# Extract usage information
prompt_tokens=$(echo "$response" | grep -o '"prompt_tokens"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' | head -1)
completion_tokens=$(echo "$response" | grep -o '"completion_tokens"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' | head -1)
total_tokens=$(echo "$response" | grep -o '"total_tokens"[[:space:]]*:[[:space:]]*[0-9]*' | grep -o '[0-9]*' | head -1)

# Build simplified response
if [ -n "$content" ]; then
    # Unescape JSON content (basic unescaping)
    content=$(echo "$content" | sed 's/\\n/\n/g' | sed 's/\\"/"/g')
    
    cat <<EOF
{
  "model": "$model",
  "content": "$content",
  "usage": {
    "prompt_tokens": ${prompt_tokens:-0},
    "completion_tokens": ${completion_tokens:-0},
    "total_tokens": ${total_tokens:-0}
  }
}
EOF
else
    # If we can't extract content, return the full response
    echo "$response"
fi
