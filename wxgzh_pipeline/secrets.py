"""Credential-form secrets scan. The bare word 'token' is NOT a secret; only
real credential shapes (access_token=<...>, app_secret=<...>, Bearer <...>,
gh*_ oauth, and literal .env values) are flagged.
"""
from __future__ import annotations

import re
from pathlib import Path

CRED_PATTERNS = {
    "access_token_kv": re.compile(r"access_token\s*[=:]\s*[A-Za-z0-9._\-]{20,}"),
    "app_secret_kv": re.compile(r"app[_-]?secret\s*[=:]\s*[A-Za-z0-9]{16,}", re.I),
    "appsecret_kv": re.compile(r"appsecret\s*[=:]\s*[A-Za-z0-9]{16,}", re.I),
    "bearer": re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"),
    "github_oauth": re.compile(r"gh[opsu]_[A-Za-z0-9]{20,}"),
    "secret_json": re.compile(r'"secret"\s*:\s*"[A-Za-z0-9]{16,}"', re.I),
}
_BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".zip", ".ico"}


def load_env_values(env_path: Path) -> list[str]:
    vals: list[str] = []
    if not env_path or not Path(env_path).is_file():
        return vals
    for line in Path(env_path).read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if len(v) >= 6 and "your_" not in v:  # ignore example placeholders
                vals.append(v)
    return vals


def scan_tree(root: Path, env_values: list[str] | None = None) -> dict:
    env_values = env_values or []
    hits = []
    for f in Path(root).rglob("*"):
        if not f.is_file() or f.suffix.lower() in _BINARY_SUFFIXES:
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for name, pat in CRED_PATTERNS.items():
            if pat.search(txt):
                hits.append({"file": str(f), "pattern": name})
        for v in env_values:
            if v in txt:
                hits.append({"file": str(f), "pattern": "literal_env_value"})
    return {"scanned_root": str(root), "hits": hits, "secrets_detected": bool(hits),
            "note": "credential-form only; bare 'token' is not treated as a secret"}
