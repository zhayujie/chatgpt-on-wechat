---
name: image-generation
description: Generate or edit images from text prompts. Use when the user asks to create, draw, design, or edit an image, illustration, photo, icon, poster, or any visual content.
metadata:
  cowagent:
    requires:
      anyEnv:
        - OPENAI_API_KEY
        - LINKAI_API_KEY
---

# Image Generation

Generate and edit images using AI models (GPT-Image-2, GPT-Image-1, etc.).

## Usage

Run `scripts/generate.py` with a JSON argument. The path is relative to this skill's `base_dir`.

```bash
python <base_dir>/scripts/generate.py '<json_args>'
```

**Set bash timeout to at least 300 seconds**, as image generation can take 30–200s depending on quality/size.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | yes | — | Image description |
| `model` | string | no | `gpt-image-2` | Model name (`gpt-image-2`, `gpt-image-1`) |
| `image_url` | string / list | no | null | Input image(s) for editing: local file path or URL |
| `quality` | string | no | auto | `low` / `medium` / `high`; omit to let the model choose |
| `size` | string | no | auto | `1K`/`2K`/`4K`, pixel value (`1024x1024`), or omit to let the model choose |
| `aspect_ratio` | string | no | null | `1:1` / `3:2` / `2:3` / `16:9` / `9:16` |

### Example — generate

```bash
python <base_dir>/scripts/generate.py '{"prompt": "A corgi astronaut floating in space"}'
```

With explicit quality/size:

```bash
python <base_dir>/scripts/generate.py '{"prompt": "A corgi astronaut", "quality": "low", "size": "1K", "aspect_ratio": "1:1"}'
```

### Important: Editing vs Generating

When the user asks to **edit, modify, or improve an existing image**, you need to pass the original image via `image_url`. Prefer passing **local file paths** directly — the script handles file reading internally. Without `image_url`, the script generates a brand-new image instead of editing.

### Example — edit (image-to-image)

Local file (preferred):

```bash
python <base_dir>/scripts/generate.py '{"prompt": "Add a Santa hat to the dog", "image_url": "/path/to/dog.png"}'
```

URL:

```bash
python <base_dir>/scripts/generate.py '{"prompt": "Make the background blue", "image_url": "https://example.com/photo.png"}'
```

### Output

Prints JSON to stdout:

```json
{
  "images": [
    {"url": "/path/to/output.png"}
  ]
}
```

After success, display the image to the user. You can either embed it in markdown (`![description](/path/to/output.png)`) or use the `send` tool.

On error:

```json
{
  "error": "error message"
}
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | yes (unless using LinkAI) | OpenAI API key |
| `OPENAI_API_BASE` | no | Custom API base URL (default: `https://api.openai.com/v1`) |
| `LINKAI_API_KEY` | alt | LinkAI API key (used when `OPENAI_API_KEY` is absent) |
| `LINKAI_API_BASE` | no | LinkAI API base URL |

### Size + Aspect Ratio Resolution

`size` and `aspect_ratio` are combined to determine the actual pixel dimensions:

| size | aspect_ratio | pixels |
|------|-------------|--------|
| `1K` | `1:1` | 1024×1024 |
| `1K` | `3:2` | 1536×1024 |
| `1K` | `2:3` | 1024×1536 |
| `2K` | `1:1` | 2048×2048 |
| `2K` | `16:9` | 2048×1152 |
| `2K` | `9:16` | 1152×2048 |
| `4K` | `16:9` | 3840×2160 |
| `4K` | `9:16` | 2160×3840 |

When an exact match isn't found, the script tries: exact match → upgrade to higher tier with same ratio → cross-tier match by ratio → tier default.

### Error Handling

The script internally tries all available providers (OpenAI → LinkAI) in sequence. If it returns an error, **do NOT retry with the same or similar parameters** — the failure is a configuration issue (wrong API key, unsupported API base, etc.), not a transient error. Instead, inform the user about the configuration problem and ask them to fix it (e.g. set the correct `OPENAI_API_KEY` / `OPENAI_API_BASE` via `env_config`), then retry after the configuration is updated.

### Notes

- HTTP timeout is 300s — high-resolution + high-quality generation can take over 200s.
- When `quality` and `size` are omitted, the API uses `auto` — the model picks the best quality/size based on the prompt.
- `quality=low` + `size=1K` is the fastest combination (~20s). Use when speed matters more than fidelity.
- Input images for editing are auto-compressed to ≤ 4MB / longest edge ≤ 4096px.
