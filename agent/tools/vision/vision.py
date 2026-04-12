"""
Vision tool - Analyze images using Vision API.
Supports local files (auto base64-encoded) and HTTP URLs.

Provider priority (default):
  1. Main model via bot.call_vision — zero extra cost
  2. Other models whose API key is configured — auto-discovered
  3. OpenAI / LinkAI raw HTTP — reliable fallback
  When use_linkai=true, LinkAI is promoted to #1.
  When tool.vision.model is set, that model is used exclusively first.
"""

import base64
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

from agent.tools.base_tool import BaseTool, ToolResult
from common import const
from common.log import logger
from config import conf

DEFAULT_MODEL = const.GPT_41_MINI
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

_MAIN_MODEL_PROVIDER_NAME = "MainModel"

# (config_key_for_api_key, bot_type, default_vision_model, provider_display_name)
# Auto-discovered as fallback vision providers when their API key is configured.
# OpenAI and LinkAI are handled separately (raw HTTP providers), so not listed here.
_DISCOVERABLE_MODELS = [
    ("moonshot_api_key", const.MOONSHOT, const.KIMI_K2_5, "Moonshot"),
    ("ark_api_key", const.DOUBAO, const.DOUBAO_SEED_2_PRO, "Doubao"),
    ("dashscope_api_key", const.QWEN_DASHSCOPE, const.QWEN36_PLUS, "DashScope"),
    ("claude_api_key", const.CLAUDEAPI, const.CLAUDE_4_6_SONNET, "Claude"),
    ("gemini_api_key", const.GEMINI, const.GEMINI_31_FLASH_LITE_PRE, "Gemini"),
    ("zhipu_ai_api_key", const.ZHIPU_AI, const.GLM_4_7, "ZhipuAI"),
    ("minimax_api_key", const.MiniMax, const.MINIMAX_M2_7, "MiniMax"),
]


@dataclass
class VisionProvider:
    """A single Vision API provider configuration."""
    name: str
    api_key: str
    api_base: str
    extra_headers: dict = field(default_factory=dict)
    model_override: Optional[str] = None
    use_bot: bool = False  # When True, call via bot.call_vision instead of raw HTTP
    fallback_bot: Any = None  # Bot instance for non-main-model providers


class VisionAPIError(Exception):
    """Raised when a Vision API call fails and should trigger fallback."""
    pass


class Vision(BaseTool):
    """Analyze images using Vision API"""

    name: str = "vision"
    description: str = (
        "Analyze a local image or image URL (jpg/jpeg/png) using Vision API. "
        "Can describe content, extract text, identify objects, colors, etc. "
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
        },
        "required": ["image", "question"],
    }

    def __init__(self, config: dict = None):
        self.config = config or {}

    @staticmethod
    def is_available() -> bool:
        return True

    def execute(self, args: Dict[str, Any]) -> ToolResult:
        image = args.get("image", "").strip()
        question = args.get("question", "").strip()

        if not image:
            return ToolResult.fail("Error: 'image' parameter is required")
        if not question:
            return ToolResult.fail("Error: 'question' parameter is required")

        providers = self._resolve_providers()
        if not providers:
            return ToolResult.fail(
                "Error: No model available for Vision.\n"
                "The main model does not support vision and no other API keys are configured.\n"
                "Options:\n"
                "  1. Switch to a multimodal model (e.g. qwen3.6-plus, claude-sonnet-4-6, gemini-2.0-flash)\n"
                "  2. Configure OPENAI_API_KEY: env_config(action=\"set\", key=\"OPENAI_API_KEY\", value=\"your-key\")\n"
                "  3. Configure LINKAI_API_KEY: env_config(action=\"set\", key=\"LINKAI_API_KEY\", value=\"your-key\")"
            )

        try:
            image_content = self._build_image_content(image)
        except Exception as e:
            return ToolResult.fail(f"Error: {e}")

        return self._call_with_fallback(providers, DEFAULT_MODEL, question, image_content)

    def _call_with_fallback(self, providers: List[VisionProvider], model: str,
                            question: str, image_content: dict) -> ToolResult:
        """Try each provider in order; fall back to the next one on failure."""
        errors: List[str] = []
        for i, provider in enumerate(providers):
            use_model = provider.model_override or model
            try:
                logger.info(f"[Vision] Trying provider '{provider.name}' "
                            f"with model '{use_model}' ({i + 1}/{len(providers)})")
                if provider.use_bot:
                    result = self._call_via_bot(use_model, question, image_content, provider)
                else:
                    result = self._call_api(provider, use_model, question, image_content)
                logger.info(f"[Vision] ✅ Success via {provider.name} (model={use_model})")
                return result
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

        Priority:
          - use_linkai=true  → [LinkAI, MainModel, OtherModels…, OpenAI]
          - default          → [MainModel, OtherModels…, OpenAI, LinkAI]

        "OtherModels" are auto-discovered from configured API keys.
        The main model's bot_type is excluded from OtherModels to avoid
        duplicating the MainModel provider.
        """
        use_linkai = conf().get("use_linkai", False) and conf().get("linkai_api_key")
        providers: List[VisionProvider] = []

        if use_linkai:
            self._append_provider(providers, self._build_linkai_provider)
            self._append_provider(providers, self._build_main_model_provider)
            self._append_other_model_providers(providers)
            self._append_provider(providers, self._build_openai_provider)
        else:
            self._append_provider(providers, self._build_main_model_provider)
            self._append_other_model_providers(providers)
            self._append_provider(providers, self._build_openai_provider)
            self._append_provider(providers, self._build_linkai_provider)

        return providers

    @staticmethod
    def _append_provider(providers: List[VisionProvider], builder) -> None:
        p = builder()
        if p:
            providers.append(p)

    def _append_other_model_providers(self, providers: List[VisionProvider]) -> None:
        """
        Auto-discover other models whose API key is configured.
        Skip the main model's own bot_type (already covered by MainModel provider).
        Skip bot_types that already have a provider in the list (e.g. OpenAI).
        """
        # Determine main model's bot_type so we can skip it
        main_bot_type = None
        if self.model and hasattr(self.model, '_resolve_bot_type'):
            main_bot_type = self.model._resolve_bot_type(conf().get("model", ""))

        existing_names = {p.name for p in providers}

        for config_key, bot_type, default_model, display_name in _DISCOVERABLE_MODELS:
            if display_name in existing_names:
                continue
            if bot_type == main_bot_type:
                continue
            api_key = conf().get(config_key, "")
            if not api_key or not api_key.strip():
                continue

            # Create a bot instance and check if it supports call_vision
            try:
                from models.bot_factory import create_bot
                bot = create_bot(bot_type)
                if not hasattr(bot, 'call_vision'):
                    continue
            except Exception:
                continue

            providers.append(VisionProvider(
                name=display_name,
                api_key="",
                api_base="",
                model_override=default_model,
                use_bot=True,
                fallback_bot=bot,
            ))

    def _resolve_vision_model(self) -> Optional[str]:
        """
        Determine which model to use for vision.

        1. User explicit config: tool.vision.model in config.json
        2. Fallback to the main configured model name
        """
        tool_conf = conf().get("tool", {})
        user_vision_model = tool_conf.get("vision", {}).get("model") if isinstance(tool_conf, dict) else None
        if user_vision_model:
            return user_vision_model
        model_name = conf().get("model", "")
        return model_name or None

    def _build_main_model_provider(self) -> Optional[VisionProvider]:
        """
        Use the vendor's own model for vision via bot.call_vision.
        Only available when the bot class has call_vision.
        """
        if not (self.model and hasattr(self.model, 'bot')):
            return None
        try:
            bot = self.model.bot
            if not hasattr(bot, 'call_vision'):
                return None
        except Exception:
            return None

        vision_model = self._resolve_vision_model()

        return VisionProvider(
            name=_MAIN_MODEL_PROVIDER_NAME,
            api_key="",
            api_base="",
            model_override=vision_model,
            use_bot=True,
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

    def _call_via_bot(self, model: str, question: str, image_content: dict,
                      provider: Optional[VisionProvider] = None) -> ToolResult:
        """
        Call a model's call_vision with vendor-native API format.
        Uses the provider's _fallback_bot if set, otherwise the main model bot.
        Raises VisionAPIError on failure so fallback can proceed.
        """
        try:
            bot = (provider and provider.fallback_bot) or self.model.bot
        except Exception as e:
            raise VisionAPIError(f"Cannot access bot: {e}")

        # Extract the raw image URL from the OpenAI-format image_content block
        image_url = image_content.get("image_url", {}).get("url", "")
        if not image_url:
            raise VisionAPIError("No image URL in content block")

        try:
            response = bot.call_vision(
                image_url=image_url,
                question=question,
                model=model,
                max_tokens=MAX_TOKENS,
            )
        except Exception as e:
            raise VisionAPIError(f"call_vision failed: {e}")

        if response is NotImplemented:
            raise VisionAPIError("Bot does not support vision")

        if isinstance(response, dict) and response.get("error"):
            raise VisionAPIError(f"API error - {response.get('message', 'Unknown')}")

        content = response.get("content", "") if isinstance(response, dict) else ""
        if not content:
            raise VisionAPIError("Empty response from main model")

        usage_info = response.get("usage", {}) if isinstance(response, dict) else {}

        # Use the actual model name from the bot response if available
        actual_model = response.get("model", model) if isinstance(response, dict) else model
        provider_name = provider.name if provider else _MAIN_MODEL_PROVIDER_NAME
        return ToolResult.success({
            "model": actual_model,
            "provider": provider_name,
            "content": content,
            "usage": usage_info,
        })

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
        """
        Build the image_url content block.
        Both remote URLs and local files are converted to base64 data URLs
        so every bot backend can consume them without extra downloads.
        """
        if image.startswith(("http://", "https://")):
            return self._download_to_data_url(image)

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
    def _download_to_data_url(url: str) -> dict:
        """Download a remote image and return it as a base64 data URL."""
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise VisionAPIError(f"Failed to download image: HTTP {resp.status_code}")
        content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        if not content_type.startswith("image/"):
            content_type = "image/jpeg"
        b64 = base64.b64encode(resp.content).decode("ascii")
        data_url = f"data:{content_type};base64,{b64}"
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
