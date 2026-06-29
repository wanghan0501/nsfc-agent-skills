#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["httpx"]
# ///
"""Generate NSFC figures via the Grsai image-generation API.

Wraps POST /v1/api/generate (models: nano-banana-pro, gpt-image-2) and the
async result endpoint GET /v1/api/result, handling sync replies, async
polling, and image download in one call.

Set GRSAI_API_KEY env var (or pass --api-key) before running:
    export GRSAI_API_KEY=sk-xxxxxxxx

Usage:
    # Prompt body = the full corresponding NSFC proposal paragraph,
    # then visual directives appended at the end.
    uv run generate_image.py \
        --prompt "本项目拟以钙钛矿吸光层为核心构建叠层太阳能电池……（整段原文）
                  Key terms: perovskite, transport layer, tandem cell.
                  isometric 3D cross-section, blue-purple palette, no text, no Chinese characters" \
        --aspect-ratio 1536x1024 --output concept.png

    uv run generate_image.py \
        --prompt "edit: make it three stacked layers" \
        --model gpt-image-2 --images https://host/ref.png -o edited.png

    uv run generate_image.py --prompt "..." --variants 4    # 4 images to pick from
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Run with: uv run generate_image.py", file=sys.stderr)
    sys.exit(1)

# Default to the China node (much faster from mainland China).
# Use GLOBAL_BASE if calling from outside China.
DEFAULT_BASE = "https://grsai.dakka.com.cn"
GLOBAL_BASE = "https://grsaiapi.com"
GENERATE_PATH = "/v1/api/generate"
RESULT_PATH = "/v1/api/result"

# Per-model defaults
MODEL_DEFAULTS = {
    "nano-banana-pro": {"aspect_ratio": "1:1", "image_size": "1K", "uses_pixels": False},
    "gpt-image-2": {"aspect_ratio": "1024x1024", "image_size": None, "uses_pixels": True},
}
DEFAULT_MODEL = "gpt-image-2"  # nano-banana-pro may hang/be unavailable on some accounts
POLL_INTERVAL = 3  # seconds
DEFAULT_TIMEOUT = 300  # seconds

# Provide your Grsai API key via the GRSAI_API_KEY environment variable or the
# --api-key flag. Do NOT hard-code a real key here — this skill is public.
BUILTIN_API_KEY = os.environ.get("GRSAI_API_KEY", "")


def build_body(model: str, prompt: str, images: list[str],
               aspect_ratio: str | None, image_size: str | None,
               reply_type: str) -> dict:
    """Build request body per model. nano-banana-pro takes imageSize + ratio
    like '16:9'; gpt-image-2 takes pixel ratios like '1536x1024' and no
    imageSize."""
    cfg = MODEL_DEFAULTS.get(model)
    if cfg is None:
        # Unknown model: send a best-effort body and let the API decide.
        body = {
            "model": model,
            "prompt": prompt,
            "images": images,
            "aspectRatio": aspect_ratio or "1:1",
            "replyType": reply_type,
        }
        if image_size:
            body["imageSize"] = image_size
        return body

    ar = aspect_ratio or cfg["aspect_ratio"]
    body = {
        "model": model,
        "prompt": prompt,
        "images": images,
        "aspectRatio": ar,
        "replyType": reply_type,
    }
    if not cfg["uses_pixels"]:
        body["imageSize"] = image_size or cfg["image_size"]
    return body


def request_generate(client: httpx.Client, base: str, api_key: str,
                     body: dict) -> dict:
    """POST /v1/api/generate, return parsed JSON."""
    url = base.rstrip("/") + GENERATE_PATH
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = client.post(url, json=body, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Generate failed HTTP {resp.status_code}: {resp.text[:500]}"
        )
    return resp.json()


def poll_result(client: httpx.Client, base: str, api_key: str,
                task_id: str, timeout: int) -> dict:
    """Poll GET /v1/api/result?id=... until succeeded/failed or timeout."""
    url = base.rstrip("/") + RESULT_PATH
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        resp = client.get(url, params={"id": task_id}, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Result poll failed HTTP {resp.status_code}: {resp.text[:500]}"
            )
        last = resp.json()
        status = last.get("status", "")
        if status == "succeeded":
            return last
        if status in ("failed", "error", "canceled"):
            raise RuntimeError(f"Task {task_id} status={status}: {last}")
        print(f"  ...status={status or 'pending'}, waiting {POLL_INTERVAL}s",
              file=sys.stderr)
        time.sleep(POLL_INTERVAL)
    raise RuntimeError(f"Task {task_id} timed out after {timeout}s. Last: {last}")


def resolve_task(client: httpx.Client, base: str, api_key: str,
                 gen_resp: dict, timeout: int) -> dict:
    """If generate returned a finished result, use it; otherwise poll."""
    status = gen_resp.get("status")
    results = gen_resp.get("results") or []
    if status == "succeeded" and results:
        return gen_resp
    task_id = gen_resp.get("id")
    if not task_id:
        raise RuntimeError(f"No id and no results in response: {gen_resp}")
    return poll_result(client, base, api_key, task_id, timeout)


def download_image(client: httpx.Client, url: str, out_path: Path) -> None:
    """Stream-download an image URL to out_path."""
    with client.stream("GET", url, follow_redirects=True) as r:
        if r.status_code != 200:
            raise RuntimeError(
                f"Download failed HTTP {r.status_code} for {url}"
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)


def run_once(client: httpx.Client, base: str, api_key: str, body: dict,
             timeout: int, out_path: Path) -> str:
    """One generate -> resolve -> download cycle. Returns the image URL."""
    gen = request_generate(client, base, api_key, body)
    done = resolve_task(client, base, api_key, gen, timeout)
    results = done.get("results") or []
    if not results:
        raise RuntimeError(f"No results in completed task: {done}")
    url = results[0].get("url")
    if not url:
        raise RuntimeError(f"No url in result: {results[0]}")
    download_image(client, url, out_path)
    return url


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate NSFC figures via Grsai API (nano-banana-pro / gpt-image-2)"
    )
    ap.add_argument("--prompt", required=True,
                    help="Prompt: paste the full corresponding NSFC proposal paragraph "
                         "as the body, then append visual directives "
                         "(view/style/palette + no-text). Key English terms help accuracy.")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    choices=list(MODEL_DEFAULTS.keys()),
                    help=f"Model (default: {DEFAULT_MODEL})")
    ap.add_argument("--aspect-ratio", default=None,
                    help="nano-banana-pro: 1:1 16:9 9:16 4:3 3:4 | gpt-image-2: 1024x1024 1536x1024 1024x1536 1792x1024 1024x1792")
    ap.add_argument("--image-size", default=None,
                    help="nano-banana-pro only, e.g. 1K (default 1K)")
    ap.add_argument("--images", nargs="*", default=[],
                    help="Input image URLs for image-to-image (gpt-image-2)")
    ap.add_argument("-o", "--output", default="output.png",
                    help="Output PNG path (default: output.png)")
    ap.add_argument("--base", default=DEFAULT_BASE,
                    help=f"API base URL (default {DEFAULT_BASE}; global: {GLOBAL_BASE})")
    ap.add_argument("--api-key", default=None,
                    help="API key (overrides GRSAI_API_KEY env)")
    ap.add_argument("--reply-type", default="json", choices=["json", "url"],
                    help="Response format (default json)")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help=f"Async poll timeout in seconds (default {DEFAULT_TIMEOUT})")
    ap.add_argument("--variants", type=int, default=1,
                    help="Generate N images (suffix _1..N added to output)")
    args = ap.parse_args()

    api_key = args.api_key or os.environ.get("GRSAI_API_KEY") or BUILTIN_API_KEY
    if not api_key:
        print("Error: no API key. Set the GRSAI_API_KEY environment variable "
              "or pass --api-key sk-xxxx", file=sys.stderr)
        return 2

    if args.variants < 1:
        print("Error: --variants must be >= 1", file=sys.stderr)
        return 2

    body = build_body(
        args.model, args.prompt, args.images,
        args.aspect_ratio, args.image_size, args.reply_type,
    )

    out_path = Path(args.output)
    suffix = out_path.suffix or ".png"

    # Read timeout must cover slow generate calls (can exceed 60s),
    # so tie it to --timeout rather than a fixed 60s.
    client_timeout = httpx.Timeout(max(120, args.timeout + 30), connect=15.0)
    with httpx.Client(timeout=client_timeout) as client:
        if args.variants == 1:
            url = run_once(client, args.base, api_key, body, args.timeout, out_path)
            print(f"Saved {out_path}  ({args.model}, {body.get('aspectRatio')})")
            print(f"Source: {url}")
        else:
            stem = out_path.with_suffix("")
            for i in range(1, args.variants + 1):
                vp = stem.with_name(f"{stem.name}_{i}{suffix}")
                url = run_once(client, args.base, api_key, body, args.timeout, vp)
                print(f"Saved {vp}  ({i}/{args.variants})  {url}")
            print(f"Done: {args.variants} variants written with base '{out_path}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
