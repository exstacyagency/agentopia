#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from urllib import error, request

base_url = os.environ.get("PAPERCLIP_BASE_URL", "http://127.0.0.1:3102")
health_url = f"{base_url.rstrip('/')}/api/health"

try:
    with request.urlopen(health_url, timeout=5) as response:
        print(f"PASS: {health_url} -> {response.status}")
except error.URLError as exc:
    print(f"FAIL: could not reach live Paperclip dev server at {health_url}: {exc}")
    sys.exit(1)
