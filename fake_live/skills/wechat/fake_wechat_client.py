#!/usr/bin/env python3
"""FAKE-LIVE WeChat client (dev2 tests only).

Simulates the audited draft-creation flow WITHOUT any real WeChat API call:
  batchget (before) -> add_material (cover) -> draft/add (single) -> batchget (after)
Emits desensitized before/after snapshots (media_id prefix + [REDACTED]) and a
draft_creation_result, proving AFTER = BEFORE + 1 with old drafts preserved.

This module implements ONLY draft creation. It has NO publish, mass-send,
scheduled-send, or delete capability — none exists to call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BEFORE_COUNT = 3  # synthetic pre-existing drafts


def _fp(seed: str) -> str:
    mid = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return mid[:8] + "[REDACTED]"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-dir", required=True)
    ap.add_argument("--html", required=True)
    a = ap.parse_args(argv)
    sd = Path(a.stage_dir)
    sd.mkdir(parents=True, exist_ok=True)

    old = [{"fingerprint": _fp(f"old-{i}")} for i in range(BEFORE_COUNT)]
    new_fp = _fp("new-draft-" + Path(a.html).name)
    before = {"endpoint": "cgi-bin/draft/batchget", "total_count": BEFORE_COUNT, "drafts": old}
    after = {"endpoint": "cgi-bin/draft/batchget", "total_count": BEFORE_COUNT + 1,
             "drafts": old + [{"fingerprint": new_fp}]}
    result = {"cover_material": {"endpoint": "cgi-bin/material/add_material",
                                 "media_id_fingerprint": _fp("cover")},
              "draft_add": {"endpoint": "cgi-bin/draft/add", "errcode": 0,
                            "media_id_fingerprint": new_fp},
              "draft_created": True, "formally_published": False,
              "real_api_call": False, "note": "FAKE-LIVE — no real WeChat call"}
    (sd / "draft_before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2),
                                          encoding="utf-8", newline="\n")
    (sd / "draft_after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2),
                                         encoding="utf-8", newline="\n")
    (sd / "draft_creation_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2),
                                                    encoding="utf-8", newline="\n")
    print(json.dumps({"WECHAT_FAKE_LIVE": "ok", "before": BEFORE_COUNT,
                      "after": BEFORE_COUNT + 1, "real_api_call": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
