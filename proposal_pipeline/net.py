"""Small HTTP helper on top of urllib, with retries for rate limits."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "proposal-pipeline/0.1 (+https://github.com/ansgomez/ki-agenten-forschungsantraege)"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class HttpError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def fetch(
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: float = 30,
    retries: int = 3,
    backoff: float = 5,
) -> tuple[bytes, str]:
    """GET `url`; return (body, content type). Retries on 429 and 5xx."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as error:
            if error.code in RETRY_STATUSES and attempt < retries:
                wait = backoff * (attempt + 1)
                print(f"  HTTP {error.code}, retrying in {wait:.0f}s ...")
                time.sleep(wait)
                continue
            raise HttpError(f"HTTP {error.code}", status=error.code) from error
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            if attempt < retries:
                time.sleep(backoff)
                continue
            raise HttpError(f"network error: {error}") from error
    raise HttpError("unreachable")


def fetch_json(url: str, params: dict | None = None, headers: dict | None = None, **kwargs) -> dict:
    body, _ = fetch(url, params=params, headers=headers, **kwargs)
    return json.loads(body)
