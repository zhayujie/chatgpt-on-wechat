"""
Vision tool - Analyze images using OpenAI-compatible Vision API.
Supports local files (auto base64-encoded) and HTTP URLs.
Providers: OpenAI (preferred) > LinkAI (fallback).
"""

import base64
import os
import subprocess
import tempfile
from typing import Any, Dict, Optional, Tuple

import requests

from agent.tools.base_tool import BaseTool, ToolResult
from common.log import logger
from config import conf

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_TIMEOUT = 60
MAX_TOKENS = 1000
COMPRESS_THRESHOLD = 1_048_576  # 1 MB

SUPPORTED_EXTENSIONS = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


class Vision(BaseTool):
    """Analyze images using OpenAI-compatible Vision API"""

    name: str = "vision"
    description: str = (
        "Analyze an image (local file or URL) using Vision API. "
        "Can describe content, extract text, identify objects, colors, etc. "
        "Requires OPENAI_API_KEY or LINKAI_API_KEY."
    )

    params: dict = {
        "type": "object",
        "properties": {
            "image": {
                "type": "string",
                "description": "Local file path or HTTP(S) URL of the image to analyze",
            },
            "question": {
                "type": "string",
                "description": "Question to ask about the image",
            },
            "model": {
                "type": "string",
                "description": (
                    f"Vision model to use (default: {DEFAULT_MODEL}). "
                    "Options: gpt-4.1-mini, gpt-4.1, gpt-4o-mini, gpt-4o"
                ),
            },
        },
        "required": ["image", "question"],
    }

    def __init__(self, config: dict = None):
        self.config = config or {}

    @staticmethod
    def is_available() -> bool:
        return bool(
            conf().get("open_ai_api_key") or os.environ.get("OPENAI_API_KEY")
            or conf().get("linkai_api_key") or os.environ.get("LINKAI_API_KEY")
        )

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        image = args.get("image", "").strip()
        question = args.get("question", "").strip()
        model = args.get("model", DEFAULT_MODEL).strip() or DEFAULT_MODEL

        if not image:
            return ToolResult.fail("Error: 'image' parameter is required")
        if not question:
            return ToolResult.fail("Error: 'question' parameter is required")

        api_key, api_base = self._resolve_provider()
        if not api_key:
            return ToolResult.fail(
                "Error: No API key configured for Vision.\n"
                "Please configure one of the following using env_config tool:\n"
                "  1. OPENAI_API_KEY (preferred): env_config(action=\"set\", key=\"OPENAI_API_KEY\", value=\"your-key\")\n"
                "  2. LINKAI_API_KEY (fallback): env_config(action=\"set\", key=\"LINKAI_API_KEY\", value=\"your-key\")\n\n"
                "Get your key at: https://platform.openai.com/api-keys or https://link-ai.tech"
            )

        try:
            image_content = self._build_image_content(image)
        except Exception as e:
            return ToolResult.fail(f"Error: {e}")

        try:
            return self._call_api(api_key, api_base, model, question, image_content)
        except requests.Timeout:
            return ToolResult.fail(f"Error: Vision API request timed out after {DEFAULT_TIMEOUT}s")
        except requests.ConnectionError:
            return ToolResult.fail("Error: Failed to connect to Vision API")
        except Exception as e:
            logger.error(f"[Vision] Unexpected error: {e}", exc_info=True)
            return ToolResult.fail(f"Error: Vision API call failed - {e}")

    def _resolve_provider(self) -> Tuple[Optional[str], str]:
        """Resolve API key and base URL. Priority: conf() > env vars."""
        api_key = conf().get("open_ai_api_key") or os.environ.get("OPENAI_API_KEY")
        if api_key:
            api_base = (conf().get("open_ai_api_base") or os.environ.get("OPENAI_API_BASE", "")).rstrip("/") \
                or "https://api.openai.com/v1"
            return api_key, self._ensure_v1(api_base)

        api_key = conf().get("linkai_api_key") or os.environ.get("LINKAI_API_KEY")
        if api_key:
            api_base = (conf().get("linkai_api_base") or os.environ.get("LINKAI_API_BASE", "")).rstrip("/") \
                or "https://api.link-ai.tech"
            logger.debug("[Vision] Using LinkAI API (OPENAI_API_KEY not set)")
            return api_key, self._ensure_v1(api_base)

        return None, ""

    @staticmethod
    def _ensure_v1(api_base: str) -> str:
        """Append /v1 if the base URL doesn't already end with a versioned path."""
        if not api_base:
            return api_base
        # Already has /v1 or similar version suffix
        if api_base.rstrip("/").split("/")[-1].startswith("v"):
            return api_base
        return api_base.rstrip("/") + "/v1"

    def _build_image_content(self, image: str) -> dict:
        """Build the image_url content block for the API request."""
        if image.startswith(("http://", "https://")):
            return {"type": "image_url", "image_url": {"url": image}}

        if not os.path.isfile(image):
            raise FileNotFoundError(f"Image file not found: {image}")

        ext = image.rsplit(".", 1)[-1].lower() if "." in image else ""
        mime_type = SUPPORTED_EXTENSIONS.get(ext)
        if not mime_type:
            raise ValueError(
                f"Unsupported image format '.{ext}'. "
                f"Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
            )

        file_path = self._maybe_compress(image)
        try:
            with open(file_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
        finally:
            if file_path != image and os.path.exists(file_path):
                os.remove(file_path)

        data_url = f"data:{mime_type};base64,{b64}"
        return {"type": "image_url", "image_url": {"url": data_url}}

    @staticmethod
    def _maybe_compress(path: str) -> str:
        """Compress image if larger than threshold; return path to use."""
        file_size = os.path.getsize(path)
        if file_size <= COMPRESS_THRESHOLD:
            return path

        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.close()

        try:
            # macOS: use sips
            subprocess.run(
                ["sips", "-Z", "800", path, "--out", tmp.name],
                capture_output=True, check=True,
            )
            logger.debug(f"[Vision] Compressed image ({file_size // 1024}KB -> {os.path.getsize(tmp.name) // 1024}KB)")
            return tmp.name
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        try:
            # Linux: use ImageMagick convert
            subprocess.run(
                ["convert", path, "-resize", "800x800>", tmp.name],
                capture_output=True, check=True,
            )
            logger.debug(f"[Vision] Compressed image ({file_size // 1024}KB -> {os.path.getsize(tmp.name) // 1024}KB)")
            return tmp.name
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        os.remove(tmp.name)
        return path

    def _call_api(self, api_key: str, api_base: str, model: str,
                  question: str, image_content: dict) -> ToolResult:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        image_content,
                    ],
                }
            ],
            "max_tokens": MAX_TOKENS,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )

        if resp.status_code == 401:
            return ToolResult.fail("Error: Invalid API key. Please check your configuration.")
        if resp.status_code == 429:
            return ToolResult.fail("Error: API rate limit reached. Please try again later.")
        if resp.status_code != 200:
            return ToolResult.fail(f"Error: Vision API returned HTTP {resp.status_code}: {resp.text[:200]}")

        data = resp.json()

        if "error" in data:
            msg = data["error"].get("message", "Unknown API error")
            return ToolResult.fail(f"Error: Vision API error - {msg}")

        content = ""
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")

        usage = data.get("usage", {})
        result = {
            "model": model,
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }
        return ToolResult.success(result)
