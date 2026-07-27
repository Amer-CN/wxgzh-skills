"""Real subprocess invocation for executable sub-skills and their official
validators. Captures exit code, stdout/stderr, wall time, and the invoked
script's sha256. dev1 stubbed live execution with NotImplementedError; this is
the real execution machinery. No network here — callers pass fake-live shim
scripts in fake_live mode and the audited installed scripts in live mode.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path


def sha256_file(p) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def run_script(script_path, args=None, cwd=None, timeout=120, env=None, python=None) -> dict:
    """Run `python script_path <args>` for real and capture the result."""
    script_path = Path(script_path)
    python = python or sys.executable
    cmd = [python, "-X", "utf8", str(script_path)] + [str(a) for a in (args or [])]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env=env)
        rc, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc = 124
        out = e.stdout or ""
        err = (e.stderr or "") + f"\nTIMEOUT after {timeout}s"
    except FileNotFoundError as e:
        rc, out, err = 127, "", f"script not found: {e}"
    return {
        "command": cmd, "exit_code": rc, "stdout": out, "stderr": err,
        "elapsed_seconds": round(time.time() - t0, 3),
        "script_path": str(script_path), "script_sha256": sha256_file(script_path),
    }
