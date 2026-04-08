"""
Vision tool - Analyze images using OpenAI-compatible Vision API.
Supports local files (auto base64-encoded) and HTTP URLs.
Providers are tried in priority order with automatic fallback on failure.
"""

import base64
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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


OPENAI_COMPATIBLE_BOT_TYPES = {"openai", "openAI", "chatGPT"}


@dataclass
class VisionProvider:
    """A single Vision API provider configuration."""
    name: str
    api_key: str
    api_base: str
    extra_headers: dict = field(default_factory=dict)
    model_override: Optional[str] = None


class VisionAPIError(Exception):
    """Raised when a Vision API call fails and should trigger fallback."""
    pass


class Vision(BaseTool):
    """Analyze images using OpenAI-compatible Vision API"""

    name: str = "vision"
    description: str = (
        "Analyze a local image or image URL (jpg/jpeg/png) using Vision API. "
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

        providers = self._resolve_providers()
        if not providers:
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

        return self._call_with_fallback(providers, model, question, image_content)

    def _call_with_fallback(self, providers: List[VisionProvider], model: str,
                            question: str, image_content: dict) -> ToolResult:
        """Try each provider in order; fall back to the next one on failure."""
        errors: List[str] = []
        for i, provider in enumerate(providers):
            use_model = provider.model_override or model
            try:
                logger.debug(f"[Vision] Trying provider '{provider.name}' "
                             f"with model '{use_model}' ({i + 1}/{len(providers)})")
                return self._call_api(provider, use_model, question, image_content)
            except VisionAPIError as e:
                errors.append(f"[{provider.name}/{use_model}] {e}")
                logger.warning(f"[Vision] Provider '{provider.name}' failed: {e}")
            except requests.Timeout:
                errors.append(f"[{provider.name}/{use_model}] Request timed out after {DEFAULT_TIMEOUT}s")
                logger.warning(f"[Vision] Provider '{provider.name}' timed out")
            except requests.ConnectionError:
                errors.append(f"[{provider.name}/{use_model}] Connection failed")
                logger.warning(f"[Vision] Provider '{provider.name}' connection failed")
            except Exception as e:
                errors.append(f"[{provider.name}/{use_model}] {e}")
                logger.error(f"[Vision] Provider '{provider.name}' unexpected error: {e}", exc_info=True)

        return ToolResult.fail(
            "Error: All Vision API providers failed.\n" + "\n".join(f"  - {err}" for err in errors)
        )

    def _resolve_providers(self) -> List[VisionProvider]:
        """
        Build an ordered list of available providers.
        Each provider builder returns a VisionProvider or None.
        To add a new provider, append a builder method to _PROVIDER_BUILDERS.
        """
        providers: List[VisionProvider] = []
        for builder in self._PROVIDER_BUILDERS:
            provider = builder(self)
            if provider:
                providers.append(provider)
        return providers

    def _build_custom_model_provider(self) -> Optional[VisionProvider]:
        """
        When bot_type is openai-compatible and a custom model is configured,
        try the user's own model first — it may already support multimodal input.
        """
        bot_type = conf().get("bot_type", "")
        if bot_type not in OPENAI_COMPATIBLE_BOT_TYPES:
            return None
        custom_model = conf().get("model", "")
        if not custom_model or custom_model == DEFAULT_MODEL:
            return None
        api_key = conf().get("open_ai_api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        api_base = (conf().get("open_ai_api_base") or os.environ.get("OPENAI_API_BASE", "")).rstrip("/") \
            or "https://api.openai.com/v1"
        return VisionProvider(
            name="CustomModel", api_key=api_key, api_base=self._ensure_v1(api_base),
            model_override=custom_model,
        )

    def _build_openai_provider(self) -> Optional[VisionProvider]:
        api_key = conf().get("open_ai_api_key") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        api_base = (conf().get("open_ai_api_base") or os.environ.get("OPENAI_API_BASE", "")).rstrip("/") \
            or "https://api.openai.com/v1"
        return VisionProvider(name="OpenAI", api_key=api_key, api_base=self._ensure_v1(api_base))

    def _build_linkai_provider(self) -> Optional[VisionProvider]:
        api_key = conf().get("linkai_api_key") or os.environ.get("LINKAI_API_KEY")
        if not api_key:
            return None
        api_base = (conf().get("linkai_api_base") or os.environ.get("LINKAI_API_BASE", "")).rstrip("/") \
            or "https://api.link-ai.tech"
        from common.utils import get_cloud_headers
        extra = get_cloud_headers(api_key)
        extra.pop("Authorization", None)
        extra.pop("Content-Type", None)
        return VisionProvider(name="LinkAI", api_key=api_key, api_base=self._ensure_v1(api_base),
                              extra_headers=extra)

    _PROVIDER_BUILDERS = [_build_custom_model_provider, _build_openai_provider, _build_linkai_provider]

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
        """Compress image to under COMPRESS_THRESHOLD with max long-edge 1536px."""
        file_size = os.path.getsize(path)
        if file_size <= COMPRESS_THRESHOLD:
            return path

        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.close()

        def _try_sips(max_dim: str, quality: str) -> bool:
            try:
                subprocess.run(
                    ["sips", "-Z", max_dim, "-s", "formatOptions", quality,
                     path, "--out", tmp.name],
                    capture_output=True, check=True,
                )
                return True
            except (FileNotFoundError, subprocess.CalledProcessError):
                return False

        def _try_convert(max_dim: str, quality: str) -> bool:
            try:
                subprocess.run(
                    ["convert", path, "-resize", f"{max_dim}x{max_dim}>",
                     "-quality", quality, tmp.name],
                    capture_output=True, check=True,
                )
                return True
            except (FileNotFoundError, subprocess.CalledProcessError):
                return False

        attempts = [
            ("1536", "85"),
            ("1536", "70"),
            ("1536", "50"),
        ]

        for max_dim, quality in attempts:
            ok = _try_sips(max_dim, quality) or _try_convert(max_dim, quality)
            if not ok:
                continue
            new_size = os.path.getsize(tmp.name)
            logger.debug(f"[Vision] Compressed image "
                         f"({file_size // 1024}KB -> {new_size // 1024}KB, "
                         f"max_dim={max_dim}, q={quality})")
            if new_size <= COMPRESS_THRESHOLD:
                return tmp.name

        if os.path.exists(tmp.name) and os.path.getsize(tmp.name) > 0:
            return tmp.name

        os.remove(tmp.name)
        return path

    def _call_api(self, provider: VisionProvider, model: str,
                  question: str, image_content: dict) -> ToolResult:
        """
        Call a single provider's Vision API.
        Raises VisionAPIError on recoverable failures so the caller can try
        the next provider.
        """
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
            "max_completion_tokens": MAX_TOKENS,
        }

        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
            **provider.extra_headers,
        }

        resp = requests.post(
            f"{provider.api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )

        if resp.status_code != 200:
            raise VisionAPIError(f"HTTP {resp.status_code}: {resp.text[:200]}")

        data = resp.json()

        if "error" in data:
            msg = data["error"].get("message", "Unknown API error")
            raise VisionAPIError(f"API error - {msg}")

        content = ""
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")

        usage = data.get("usage", {})
        result = {
            "model": model,
            "provider": provider.name,
            "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }
        return ToolResult.success(result)
