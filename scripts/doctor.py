#!/usr/bin/env python3
"""doctor — fail-closed environment check before 发文.

Verifies: sub-skills exist + version + root hash match skills.lock.json,
documented entrypoints/validators present, WeChat config present, project
writable. Exit 0 = healthy; non-zero = FAIL_CLOSED (do not bypass).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wxgzh_pipeline.orchestrator import Orchestrator  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--require-wechat", action="store_true")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args(argv)
    orch = Orchestrator(project_root=a.project_root,
                        network_mode="offline_fixture" if a.offline else "live")
    ok, report = orch.doctor(require_wechat=a.require_wechat or None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
