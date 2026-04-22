#!/usr/bin/env python3
"""
Unified image generation script.

Usage:
    python generate.py '<json_args>'

Supports GPT-Image-2 / GPT-Image-1 via the OpenAI-compatible Images API.
Designed for easy extension to other providers (Gemini, etc.).

Dependencies: requests (stdlib: json, sys, os, base64, io, abc, uuid, pathlib, urllib)
"""

import json
import sys
import os
import base64
import io
import uuid
import re
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlparse
from urllib.error import URLError

try:
    import requests

    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ---------------------------------------------------------------------------
# Size / aspect-ratio resolution
# ---------------------------------------------------------------------------

_SIZE_TABLE = {
    # (tier, ratio) -> "WxH"
    ("1K", "1:1"): "1024x1024",
    ("1K", "3:2"): "1536x1024",
    ("1K", "2:3"): "1024x1536",
    ("2K", "1:1"): "2048x2048",
    ("2K", "16:9"): "2048x1152",
    ("2K", "9:16"): "1152x2048",
    ("4K", "16:9"): "3840x2160",
    ("4K", "9:16"): "2160x3840",
}

_TIER_ORDER = ["1K", "2K", "4K"]
_RATIO_DEFAULT = {"1K": "1:1", "2K": "1:1", "4K": "16:9"}

_PIXEL_RE = re.compile(r"^\d+x\d+$")


def resolve_size(size: str | None, aspect_ratio: str | None) -> str | None:
    """Resolve (size, aspect_ratio) to a concrete 'WxH' string or None."""
    if size and _PIXEL_RE.match(size):
        return size
    if size and size.lower() == "auto":
        size = None
    if not size and not aspect_ratio:
        return None

    tier = size.upper() if size else None
    ratio = aspect_ratio

    if tier and ratio:
        key = (tier, ratio)
        if key in _SIZE_TABLE:
            return _SIZE_TABLE[key]
        # Upgrade: try higher tiers with same ratio
        start = _TIER_ORDER.index(tier) + 1 if tier in _TIER_ORDER else 0
        for t in _TIER_ORDER[start:]:
            if (t, ratio) in _SIZE_TABLE:
                return _SIZE_TABLE[(t, ratio)]
        # Cross-tier: any tier with this ratio
        for t in _TIER_ORDER:
            if (t, ratio) in _SIZE_TABLE:
                return _SIZE_TABLE[(t, ratio)]
        # Tier default
        if tier in _RATIO_DEFAULT:
            return _SIZE_TABLE.get((tier, _RATIO_DEFAULT[tier]))

    if tier and not ratio:
        default_ratio = _RATIO_DEFAULT.get(tier)
        if default_ratio:
            return _SIZE_TABLE.get((tier, default_ratio))

    if ratio and not tier:
        for t in _TIER_ORDER:
            if (t, ratio) in _SIZE_TABLE:
                return _SIZE_TABLE[(t, ratio)]

    return None


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _load_image(source: str) -> bytes:
    """Load image from a local file path or URL."""
    if os.path.isfile(source):
        with open(source, "rb") as f:
            return f.read()
    if _HAS_REQUESTS:
        resp = requests.get(source, timeout=60)
        resp.raise_for_status()
        return resp.content
    req = Request(source)
    with urlopen(req, timeout=60) as resp:
        return resp.read()


def _compress_image(data: bytes, max_bytes: int = 4 * 1024 * 1024, max_edge: int = 4096) -> bytes:
    """Compress image to fit size/dimension limits. Requires Pillow only when needed."""
    if len(data) <= max_bytes:
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(data))
            w, h = img.size
            if max(w, h) <= max_edge:
                return data
        except ImportError:
            return data
        except Exception:
            return data

    try:
        from PIL import Image
    except ImportError:
        return data

    img = Image.open(io.BytesIO(data))
    w, h = img.size

    if max(w, h) > max_edge:
        ratio = max_edge / max(w, h)
        w, h = int(w * ratio), int(h * ratio)
        img = img.resize((w, h), Image.LANCZOS)

    buf = io.BytesIO()
    fmt = img.format or "PNG"
    if fmt.upper() == "JPEG":
        quality = 85
        while True:
            buf.seek(0)
            buf.truncate()
            img.save(buf, format="JPEG", quality=quality)
            if buf.tell() <= max_bytes or quality <= 20:
                break
            quality -= 10
    else:
        img.save(buf, format=fmt)
        if buf.tell() > max_bytes:
            buf.seek(0)
            buf.truncate()
            img.save(buf, format="JPEG", quality=75)
    return buf.getvalue()


def _save_image(data: bytes, output_dir: str) -> str:
    """Save image bytes to output_dir and return the path."""
    os.makedirs(output_dir, exist_ok=True)
    ext = "png"
    if data[:3] == b"\xff\xd8\xff":
        ext = "jpg"
    elif data[:4] == b"RIFF":
        ext = "webp"
    filename = f"{uuid.uuid4().hex[:12]}.{ext}"
    path = os.path.join(output_dir, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------

class ImageProvider(ABC):
    """Abstract base class for image generation providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        image_url: str | list | None = None,
        quality: str | None = None,
        size: str | None = None,
        output_dir: str = ".",
    ) -> list[str]:
        """Generate image(s) and return list of local file paths."""
        ...


# ---------------------------------------------------------------------------
# OpenAI-compatible provider (gpt-image-2, gpt-image-1)
# ---------------------------------------------------------------------------

class OpenAIProvider(ImageProvider):
    """Provider for OpenAI Image API (generations + edits)."""

    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
        }

    @staticmethod
    def _raise_for_api_error(resp):
        """Raise with server error details instead of bare HTTP status."""
        if resp.status_code >= 400:
            try:
                body = resp.json()
                msg = body.get("error", {}).get("message") or body.get("message") or resp.text
            except Exception:
                msg = resp.text or resp.reason
            raise RuntimeError(f"API {resp.status_code}: {msg} (url: {resp.url})")

    def _post_json(self, url: str, payload: dict) -> dict:
        headers = {**self._headers(), "Content-Type": "application/json"}
        if _HAS_REQUESTS:
            resp = requests.post(url, headers=headers, json=payload, timeout=300)
            self._raise_for_api_error(resp)
            return resp.json()
        data = json.dumps(payload).encode()
        req = Request(url, data=data, headers=headers, method="POST")
        with urlopen(req, timeout=300) as r:
            return json.loads(r.read())

    def _post_multipart(self, url: str, fields: dict, files: list[tuple]) -> dict:
        """POST multipart/form-data using requests (or fall back to urllib)."""
        headers = self._headers()
        if _HAS_REQUESTS:
            resp = requests.post(url, headers=headers, data=fields, files=files, timeout=300)
            self._raise_for_api_error(resp)
            return resp.json()
        boundary = uuid.uuid4().hex
        body = b""
        for key, val in fields.items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{val}\r\n".encode()
        for field_name, (filename, filedata, content_type) in files:
            body += (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode() + filedata + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        req = Request(url, data=body, headers=headers, method="POST")
        with urlopen(req, timeout=300) as r:
            return json.loads(r.read())

    def generate(
        self,
        prompt: str,
        *,
        image_url=None,
        quality: str | None = None,
        size: str | None = None,
        output_dir: str = ".",
    ) -> list[str]:
        if image_url:
            return self._edit(prompt, image_url=image_url, quality=quality, size=size, output_dir=output_dir)
        return self._create(prompt, quality=quality, size=size, output_dir=output_dir)

    def _create(self, prompt: str, *, quality: str | None, size: str | None, output_dir: str) -> list[str]:
        url = f"{self.api_base}/images/generations"
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
        }
        if quality:
            payload["quality"] = quality
        if size:
            payload["size"] = size
        result = self._post_json(url, payload)
        return self._save_results(result, output_dir)

    def _edit(
        self,
        prompt: str,
        *,
        image_url,
        quality: str | None,
        size: str | None,
        output_dir: str,
    ) -> list[str]:
        urls = image_url if isinstance(image_url, list) else [image_url]
        image_data_list = [_compress_image(_load_image(u)) for u in urls]

        url = f"{self.api_base}/images/edits"

        fields = {"model": self.model, "prompt": prompt}
        if quality:
            fields["quality"] = quality
        if size:
            fields["size"] = size

        files = []
        for i, img_bytes in enumerate(image_data_list):
            ext = "png"
            if img_bytes[:3] == b"\xff\xd8\xff":
                ext = "jpg"
            field_name = "image[]" if len(image_data_list) > 1 else "image"
            files.append((field_name, (f"image_{i}.{ext}", img_bytes, f"image/{ext}")))

        result = self._post_multipart(url, fields, files)
        return self._save_results(result, output_dir)

    @staticmethod
    def _save_results(result: dict, output_dir: str) -> list[str]:
        paths = []
        for item in result.get("data", []):
            if "b64_json" in item:
                raw = base64.b64decode(item["b64_json"])
                paths.append(_save_image(raw, output_dir))
            elif "url" in item:
                raw = _load_image(item["url"])
                paths.append(_save_image(raw, output_dir))
        return paths


# ---------------------------------------------------------------------------
# LinkAI provider (uses unified /v1/images/generations)
# ---------------------------------------------------------------------------

class LinkAIProvider(ImageProvider):
    """Provider for LinkAI unified image generation API."""

    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model

    def generate(
        self,
        prompt: str,
        *,
        image_url=None,
        quality: str | None = None,
        size: str | None = None,
        output_dir: str = ".",
    ) -> list[str]:
        url = f"{self.api_base}/v1/images/generations"
        payload: dict = {
            "model": self.model,
            "prompt": prompt,
        }
        if quality:
            payload["quality"] = quality
        if size:
            payload["size"] = size
        if image_url:
            urls = image_url if isinstance(image_url, list) else [image_url]
            resolved = []
            for u in urls:
                if os.path.isfile(u):
                    data = _load_image(u)
                    ext = u.rsplit(".", 1)[-1].lower() if "." in u else "png"
                    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext, "image/png")
                    resolved.append(f"data:{mime};base64,{base64.b64encode(data).decode()}")
                else:
                    resolved.append(u)
            payload["image_url"] = resolved if len(resolved) > 1 else resolved[0]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if _HAS_REQUESTS:
            resp = requests.post(url, headers=headers, json=payload, timeout=300)
            if resp.status_code >= 400:
                try:
                    body = resp.json()
                    msg = body.get("error", {}).get("message") or body.get("message") or resp.text
                except Exception:
                    msg = resp.text or resp.reason
                raise RuntimeError(f"API {resp.status_code}: {msg}")
            result = resp.json()
        else:
            data = json.dumps(payload).encode()
            req = Request(url, data=data, headers=headers, method="POST")
            with urlopen(req, timeout=300) as r:
                result = json.loads(r.read())

        if "error" in result:
            raise RuntimeError(result["error"].get("message", str(result["error"])))

        paths = []
        for item in result.get("data", []):
            if "url" in item:
                raw = _load_image(item["url"])
                paths.append(_save_image(raw, output_dir))
            elif "b64_json" in item:
                raw = base64.b64decode(item["b64_json"])
                paths.append(_save_image(raw, output_dir))
        return paths


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

def _build_providers(model: str) -> list[tuple[str, ImageProvider]]:
    """Build an ordered list of (label, provider) to try."""
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    openai_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
    linkai_key = os.environ.get("LINKAI_API_KEY", "")
    linkai_base = os.environ.get("LINKAI_API_BASE", "https://api.link-ai.tech")

    providers = []
    if openai_key:
        providers.append(("OpenAI", OpenAIProvider(api_key=openai_key, api_base=openai_base, model=model)))
    if linkai_key:
        providers.append(("LinkAI", LinkAIProvider(api_key=linkai_key, api_base=linkai_base, model=model)))
    return providers


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python generate.py '<json_args>'"}))
        sys.exit(1)

    try:
        args = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    prompt = args.get("prompt")
    if not prompt:
        print(json.dumps({"error": "Missing required parameter: prompt"}))
        sys.exit(1)

    model = args.get("model", "gpt-image-2")
    quality = args.get("quality")
    raw_size = args.get("size")
    aspect_ratio = args.get("aspect_ratio")
    image_url = args.get("image_url")

    resolved_size = resolve_size(raw_size, aspect_ratio)

    output_dir = os.environ.get("IMAGE_OUTPUT_DIR", os.path.join(os.getcwd(), "images"))

    providers = _build_providers(model)
    if not providers:
        print(json.dumps({
            "error": "No API key configured. Please set OPENAI_API_KEY or LINKAI_API_KEY via env_config tool, then try again."
        }, ensure_ascii=False))
        sys.exit(1)

    import time

    errors = []
    for label, provider in providers:
        try:
            print(f"[image-generation] Trying {label} (model={model})...", file=sys.stderr)
            t0 = time.time()
            paths = provider.generate(
                prompt,
                image_url=image_url,
                quality=quality,
                size=resolved_size,
                output_dir=output_dir,
            )
            elapsed = time.time() - t0
            print(f"[image-generation] ✅ {label} succeeded in {elapsed:.1f}s", file=sys.stderr)
            result = {"images": [{"url": p} for p in paths]}
            print(json.dumps(result, ensure_ascii=False))
            return
        except Exception as e:
            elapsed = time.time() - t0
            print(f"[image-generation] ❌ {label} failed in {elapsed:.1f}s: {e}", file=sys.stderr)
            errors.append(f"{label}: {e}")

    hint = " | ".join(errors)
    print(json.dumps({
        "error": f"All providers failed — {hint}. "
                 "This is likely an API key or base URL configuration issue. "
                 "Do NOT retry with the same parameters. "
                 "Ask the user to verify their OPENAI_API_KEY / OPENAI_API_BASE "
                 "(or LINKAI_API_KEY / LINKAI_API_BASE) settings via env_config."
    }, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
