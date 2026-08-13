#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring gzh-design `scripts/publish_wechat_draft.py` audit mode.

EXACT real CLI subset: --html / --title / --audit-dir / --dry-run
(+ tolerated: --thumb-media-id / --cover / --expect-sha256). In fake_live it runs
the audit path with --dry-run semantics: snapshots a simulated draft list before,
"creates" one draft, snapshots after — proving AFTER=BEFORE+1. Writes
draft_before.json / draft_after.json / draft_creation_result.json. SIMULATED —
NO network, NO real draft, NO publish/mass-send/delete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="publish_wechat_draft (fake-live shim, audit)")
    ap.add_argument("--html", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--audit-dir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--thumb-media-id", default=None)
    ap.add_argument("--cover", default=None)
    ap.add_argument("--expect-sha256", default=None)
    a = ap.parse_args(argv)

    html = Path(a.html).read_text(encoding="utf-8") if Path(a.html).is_file() else ""
    if "<section" not in html:
        print("[fake publish] ERROR: html not a rendered section"); return 1
    content_sha = hashlib.sha256(html.encode("utf-8")).hexdigest()

    audit = Path(a.audit_dir)
    audit.mkdir(parents=True, exist_ok=True)
    seed = [{"media_id": f"seed{i:04d}[REDACTED]", "update_time": 1000 + i} for i in range(1, 4)]
    before = {"total_count": 3, "item_count": 3, "items": seed,
              "simulated": True, "real_api_call": False}
    new_media = hashlib.sha256((a.title + content_sha).encode()).hexdigest()[:8] + "[REDACTED]"
    after = {"total_count": 4, "item_count": 4,
             "items": seed + [{"media_id": new_media, "update_time": 2000}],
             "simulated": True, "real_api_call": False}
    result = {"media_id": new_media, "title": a.title,
              "before_total": 3, "after_total": 4, "delta": 1,
              "draft_only": True, "formally_published": False, "mass_send": False,
              "scheduled": False, "deleted_any": False,
              "real_api_call": False, "simulated": True, "content_sha256": content_sha}
    for name, obj in (("draft_before.json", before), ("draft_after.json", after),
                      ("draft_creation_result.json", result)):
        (audit / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True),
                                  encoding="utf-8")
    print(f"[fake publish_wechat_draft] simulated audit before=3 after=4 delta=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
