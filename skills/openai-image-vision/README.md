# OpenAI Image Vision Skill

This skill enables image analysis using OpenAI's Vision API (GPT-4 Vision models).

## Features

- ✅ Analyze images from local files or URLs
- ✅ Support for multiple image formats (JPEG, PNG, GIF, WebP)
- ✅ Automatic base64 encoding for local files
- ✅ Direct URL passing for remote images
- ✅ Configurable model selection
- ✅ Custom API base URL support
- ✅ Pure bash/curl implementation (no Python dependencies)

## Quick Start

1. **Set up API credentials using env_config:**
   ```bash
   env_config(action="set", key="OPENAI_API_KEY", value="sk-your-api-key-here")
   # Optional: custom API base
   env_config(action="set", key="OPENAI_API_BASE", value="https://api.openai.com/v1")
   ```

2. **Analyze an image:**
   ```bash
   bash scripts/vision.sh "/path/to/photo.jpg" "What's in this image?"
   ```

3. **Analyze from URL:**
   ```bash
   bash scripts/vision.sh "https://example.com/image.jpg" "Describe this image"
   ```
   ```bash
   bash scripts/vision.sh "/path/to/image.jpg" "What's in this image?"
   ```

3. **Analyze from URL:**
   ```bash
   bash scripts/vision.sh "https://example.com/image.jpg" "Describe this image"
   ```

## Usage Examples

### Basic image analysis
```bash
bash scripts/vision.sh "photo.jpg" "What objects can you see?"
```

### Text extraction (OCR)
```bash
bash scripts/vision.sh "document.png" "Extract all text from this image"
```

### Detailed description
```bash
bash scripts/vision.sh "scene.jpg" "Describe this scene in detail, including colors, mood, and composition"
```

### Using different models
```bash
# Use gpt-4.1-mini (default, latest mini model)
bash scripts/vision.sh "image.jpg" "Analyze this" "gpt-4.1-mini"

# Use gpt-4.1 (most capable, latest model)
bash scripts/vision.sh "image.jpg" "Analyze this" "gpt-4.1"

# Use gpt-4o-mini (previous mini model)
bash scripts/vision.sh "image.jpg" "Analyze this" "gpt-4o-mini"
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | Your OpenAI API key |
| `OPENAI_API_BASE` | No | `https://api.openai.com/v1` | Custom API base URL |

## Response Format

Success response:
```json
{
  "model": "gpt-4.1-mini",
  "content": "The image shows a beautiful sunset over mountains...",
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 567,
    "total_tokens": 1801
  }
}
```

Error response:
```json
{
  "error": "Error description",
  "details": "Additional information"
}
```

## Supported Models

- `gpt-4.1-mini` (default) - Latest mini model, fast and cost-effective
- `gpt-4.1` - Latest GPT-4 variant, most capable
- `gpt-4o-mini` - Previous generation mini model
- `gpt-4-turbo` - Previous generation turbo model

## Supported Image Formats

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- GIF (`.gif`)
- WebP (`.webp`)

## Technical Details

- **Implementation**: Pure bash script using curl and base64
- **Timeout**: 60 seconds for API calls
- **Max tokens**: 1000 tokens for responses
- **Image handling**: 
  - Local files are automatically base64-encoded
  - URLs are passed directly to the API
  - MIME types are auto-detected from file extensions

## Error Handling

The script handles various error cases:
- Missing required parameters
- Missing API key
- File not found
- Unsupported image formats
- API errors
- Network timeouts
- Invalid JSON responses

## Integration with Agent System

When loaded by the agent system, this skill will appear in `<available_skills>` with a `<base_dir>` path. Use it like:

```bash
bash "<base_dir>/scripts/vision.sh" "image.jpg" "What's in this image?"
```

The agent will automatically:
- Load environment variables from `~/.cow/.env`
- Provide the correct `<base_dir>` path
- Handle skill discovery and registration

## Notes

- Images are sent to OpenAI's servers for processing
- Large images may be automatically resized by the API
- Rate limits depend on your OpenAI API plan
- Token usage includes both the image and text in the prompt
- Base64 encoding increases the size of local images by ~33%

## Troubleshooting

**"OPENAI_API_KEY environment variable is not set"**
- Set the environment variable using env_config tool
- Or use the agent's env_config tool

**"Image file not found"**
- Check the file path is correct
- Use absolute paths or paths relative to current directory

**"Unsupported image format"**
- Only JPEG, PNG, GIF, and WebP are supported
- Check the file extension matches the actual format

**"Failed to call OpenAI API"**
- Check your internet connection
- Verify the API key is valid
- Check if custom API base URL is correct

## License

Part of the chatgpt-on-wechat project.
