# OpenAI Image Vision - Usage Examples

## Setup

Set up your API credentials using the agent's env_config tool:

```bash
# Set your OpenAI API key
env_config(action="set", key="OPENAI_API_KEY", value="sk-your-api-key-here")

# Optional: Set custom API base URL (for proxy or compatible services)
env_config(action="set", key="OPENAI_API_BASE", value="https://api.openai.com/v1")
```

## Example 1: Analyze a Local Image

```bash
bash scripts/vision.sh "/path/to/photo.jpg" "What's in this image?"
```

**Expected Output:**
```json
{
  "model": "gpt-4.1-mini",
  "content": "The image shows a beautiful landscape with mountains in the background and a lake in the foreground. The sky is clear with some clouds, and there are trees along the shoreline.",
  "usage": {
    "prompt_tokens": 1234,
    "completion_tokens": 45,
    "total_tokens": 1279
  }
}
```

## Example 2: Analyze an Image from URL

```bash
bash scripts/vision.sh "https://example.com/image.jpg" "Describe this image in detail"
```

## Example 3: Extract Text (OCR)

```bash
bash scripts/vision.sh "document.png" "Extract all text from this image"
```

**Use Case:** Extract text from screenshots, scanned documents, or photos of text.

## Example 4: Identify Objects

```bash
bash scripts/vision.sh "scene.jpg" "List all objects you can identify in this image"
```

## Example 5: Analyze Colors and Composition

```bash
bash scripts/vision.sh "artwork.jpg" "Describe the color palette and composition of this image"
```

## Example 6: Count Items

```bash
bash scripts/vision.sh "crowd.jpg" "How many people are in this image?"
```

## Example 7: Use Different Models

```bash
# Use gpt-4.1-mini (default, latest mini model)
bash scripts/vision.sh "image.jpg" "Analyze this" "gpt-4.1-mini"

# Use gpt-4.1 (most capable, best for complex analysis)
bash scripts/vision.sh "image.jpg" "Analyze this" "gpt-4.1"

# Use gpt-4o-mini (previous mini model)
bash scripts/vision.sh "image.jpg" "Analyze this" "gpt-4o-mini"
```

## Example 8: Complex Analysis

```bash
bash scripts/vision.sh "product.jpg" "Analyze this product image. Describe the product, its features, colors, and suggest what kind of marketing copy would work well for it."
```

## Example 9: Safety and Content Moderation

```bash
bash scripts/vision.sh "content.jpg" "Is there any inappropriate or unsafe content in this image?"
```

## Example 10: Technical Analysis

```bash
bash scripts/vision.sh "diagram.png" "Explain what this technical diagram represents and how it works"
```

## Integration with Agent

When the agent loads this skill, it will be available in the `<available_skills>` section. The agent can use it like:

```bash
bash "<base_dir>/scripts/vision.sh" "user_uploaded_image.jpg" "What's in this image?"
```

The `<base_dir>` will be automatically provided by the skill system.

## Error Handling Examples

### Missing API Key
```bash
$ bash scripts/vision.sh "image.jpg" "What is this?"
{"error": "OPENAI_API_KEY environment variable is not set", "help": "Visit https://platform.openai.com/api-keys to get an API key"}
```

### File Not Found
```bash
$ bash scripts/vision.sh "nonexistent.jpg" "What is this?"
{"error": "Image file not found", "path": "nonexistent.jpg"}
```

### Unsupported Format
```bash
$ bash scripts/vision.sh "file.bmp" "What is this?"
{"error": "Unsupported image format", "extension": "bmp", "supported": ["jpg", "jpeg", "png", "gif", "webp"]}
```

### Missing Parameters
```bash
$ bash scripts/vision.sh
{"error": "Image path or URL is required", "usage": "bash vision.sh <image_path_or_url> <question> [model]"}
```

## Tips for Best Results

1. **Be Specific**: Ask clear, specific questions about what you want to know
2. **Image Quality**: Higher quality images generally produce better results
3. **Model Selection**: 
   - Use `gpt-4.1` for complex analysis requiring highest accuracy
   - Use `gpt-4.1-mini` (default) for most tasks - latest mini model with good balance
4. **Text Extraction**: For OCR tasks, ensure text is clearly visible and not too small
5. **Multiple Aspects**: You can ask about multiple things in one question
6. **Context**: Provide context in your question if needed (e.g., "This is a medical scan, what do you see?")

## Performance Notes

- **Local Files**: Automatically base64-encoded, adds ~33% size overhead
- **URLs**: Passed directly to API, no encoding overhead
- **Timeout**: 60 seconds for API calls
- **Max Tokens**: 1000 tokens for responses (configurable in script)
- **Rate Limits**: Subject to your OpenAI API plan

## Supported Image Formats

✅ JPEG (`.jpg`, `.jpeg`)  
✅ PNG (`.png`)  
✅ GIF (`.gif`)  
✅ WebP (`.webp`)  

❌ BMP, TIFF, SVG, and other formats are not supported

## Cost Considerations

Vision API calls cost more than text-only calls because they include image tokens. Costs vary by:
- Model used (gpt-4.1 vs gpt-4.1-mini)
- Image size and resolution
- Length of response

Check OpenAI's pricing page for current rates: https://openai.com/pricing
