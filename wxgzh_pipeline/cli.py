"""Natural-language CLI. Fixes 发文/续发/进度/验收编排Skill to orchestrator calls.

  发文：<选题>      -> run (fast_publish, create draft, no formal publish)
  续发 / 续发：<ID>  -> resume newest-incomplete / specific run
  进度              -> progress
  验收编排Skill      -> release_audit (dev only; no article/upload/draft)
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from .orchestrator import Orchestrator

# accept full-width ： and half-width :, with optional spaces
_FABU = re.compile(r"^\s*发文\s*[:：]\s*(?P<topic>.+?)\s*$")
_RESUME_ID = re.compile(r"^\s*续发\s*[:：]\s*(?P<run_id>.+?)\s*$")


def parse_command(text: str) -> dict:
    t = (text or "").strip()
    m = _FABU.match(t)
    if m:
        return {"command": "fabu", "topic": m.group("topic").strip()}
    m = _RESUME_ID.match(t)
    if m:
        return {"command": "resume", "run_id": m.group("run_id").strip()}
    if t == "续发":
        return {"command": "resume", "run_id": None}
    if t == "进度":
        return {"command": "progress"}
    if t == "验收编排Skill":
        return {"command": "release_audit"}
    return {"command": "unknown", "raw": t}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(prog="wxgzh-pipeline", add_help=True)
    ap.add_argument("phrase", nargs="?", help='e.g. "发文：Claude Opus 5" / "续发" / "进度" / "验收编排Skill"')
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--offline", action="store_true", help="use offline fixtures (dev/tests; no side effects)")
    ap.add_argument("--fixture-dir", default=None)
    a = ap.parse_args(argv)

    if not a.phrase:
        ap.print_help()
        return 2
    cmd = parse_command(a.phrase)
    if cmd["command"] == "unknown":
        print(json.dumps({"status": "UNKNOWN_COMMAND",
                          "hint": '用 "发文：<选题>" / "续发" / "进度" / "验收编排Skill"',
                          "raw": cmd.get("raw")}, ensure_ascii=False))
        return 2

    net = "offline_fixture" if a.offline else "live"
    orch = Orchestrator(project_root=a.project_root, network_mode=net, fixture_dir=a.fixture_dir)

    if cmd["command"] == "fabu":
        out = orch.run(cmd["topic"], profile="fast_publish", create_wechat_draft=True)
    elif cmd["command"] == "resume":
        rid = cmd.get("run_id")
        if rid is None:
            inc = orch.list_incomplete()
            if len(inc) > 1:
                print(json.dumps({"status": "MULTIPLE_INCOMPLETE", "choose_one": inc,
                                  "hint": "用 续发：<RUN_ID> 指定"}, ensure_ascii=False))
                return 0
        out = orch.resume(rid)
    elif cmd["command"] == "progress":
        out = orch.progress()
    elif cmd["command"] == "release_audit":
        out = orch.release_audit()
    else:
        out = {"status": "UNKNOWN_COMMAND"}

    print(json.dumps(out, ensure_ascii=False, indent=2))
    status = str(out.get("status", out.get("RELEASE_AUDIT", "")))
    return 0 if status in ("COMPLETE", "ALREADY_COMPLETE", "PASS", "MULTIPLE_INCOMPLETE",
                           "") or out.get("RELEASE_AUDIT") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
