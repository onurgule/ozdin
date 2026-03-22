"""Minimal smoke: GET /health. Optional POST /v1/chat/ask if RUN_SMOKE_ASK=1."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _get(url: str, headers: dict[str, str]) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def _post(url: str, body: dict, headers: dict[str, str]) -> tuple[int, str]:
    data = json.dumps(body).encode("utf-8")
    h = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def main() -> int:
    base = os.environ.get("SMOKE_API_BASE", "http://127.0.0.1:8000").rstrip("/")
    key = os.environ.get("SMOKE_API_KEY", "")
    headers: dict[str, str] = {}
    if key:
        headers["X-API-Key"] = key
    code, text = _get(f"{base}/health", headers)
    print("health", code, text[:500])
    if code != 200:
        return 1
    if os.environ.get("RUN_SMOKE_ASK") == "1":
        q = {"question": "örnek", "answer_language": "tr"}
        acode, atext = _post(f"{base}/v1/chat/ask", q, headers)
        print("ask", acode, atext[:500])
        if acode != 200:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
