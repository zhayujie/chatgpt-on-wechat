---
name: openai-image-vision
description: Analyze images using OpenAI's Vision API. Use bash command to execute the vision script like 'bash <base_dir>/scripts/vision.sh <image> <question>'. Can understand image content, objects, text, colors, and answer questions about images.
homepage: https://platform.openai.com/docs/guides/vision
metadata:
  emoji: 👁️
  requires:
    bins: ["curl", "base64"]
    env: ["OPENAI_API_KEY"]
  primaryEnv: "OPENAI_API_KEY"
---

# OpenAI Image Vision

Analyze images using OpenAI's GPT-4 Vision API. The model can understand visual elements including objects, shapes, colors, textures, and text within images.

## Setup

This skill requires an OpenAI API key. If not configured:

1. Get your API key from https://platform.openai.com/api-keys
2. Set the key using: `env_config(action="set", key="OPENAI_API_KEY", value="your-key")`

Optional: Set custom API base URL (default: https://api.openai.com/v1):
```bash
env_config(action="set", key="OPENAI_API_BASE", value="your-base-url")
```

## Usage

**Important**: Scripts are located relative to this skill's base directory.

When you see this skill in `<available_skills>`, note the `<base_dir>` path.

**CRITICAL**: Always use `bash` command to execute the script:

```bash
# General pattern (MUST start with bash):
bash "<base_dir>/scripts/vision.sh" "<image_path_or_url>" "<question>" [model]

# DO NOT execute the script directly like this (WRONG):
# "<base_dir>/scripts/vision.sh" ...

# Parameters:
# - image_path_or_url: Local image file path or HTTP(S) URL (required)
# - question: Question to ask about the image (required)
# - model: OpenAI model to use (default: gpt-4.1-mini)
#   Options: gpt-4.1-mini, gpt-4.1, gpt-4o-mini, gpt-4-turbo
```

## Examples

### Analyze a local image
```bash
bash "<base_dir>/scripts/vision.sh" "/path/to/image.jpg" "What's in this image?"
```

### Analyze an image from URL
```bash
bash "<base_dir>/scripts/vision.sh" "https://example.com/image.jpg" "Describe this image in detail"
```

### Use specific model
```bash
bash "<base_dir>/scripts/vision.sh" "/path/to/photo.png" "What colors are prominent?" "gpt-4o-mini"
```

### Extract text from image
```bash
bash "<base_dir>/scripts/vision.sh" "/path/to/document.jpg" "Extract all text from this image"
```

### Analyze multiple aspects
```bash
bash "<base_dir>/scripts/vision.sh" "image.jpg" "List all objects you can see and describe the overall scene"
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

**Performance Optimization**: Files larger than 1MB are automatically compressed to 800px (longest side) to avoid command-line parameter limits. This happens transparently without affecting analysis quality.

## Response Format

The script returns a JSON response:

```json
{
  "model": "gpt-4.1-mini",
  "content": "The image shows...",
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567,
    "total_tokens": 1801
  }
}
```

Or in case of error:

```json
{
  "error": "Error description",
  "details": "Additional error information"
}
```

## Notes

- **Image size**: Images are automatically resized if too large
- **Timeout**: 60 seconds for API calls
- **Rate limits**: Subject to your OpenAI API plan limits
- **Privacy**: Images are sent to OpenAI's servers for processing
- **Local files**: Automatically converted to base64 for API submission
- **URLs**: Can be passed directly to the API without downloading
