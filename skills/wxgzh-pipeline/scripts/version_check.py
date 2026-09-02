#!/usr/bin/env python3
"""scripts/version_check.py — 77V 版本新鲜度检查（建议性工具，永远 exit 0）。

比对本地构建基线日期与远端最新发版 tag，供编排器第 0 步调用（77V）：
  远端面：`git ls-remote --tags <origin>`（固定 origin URL 常量，不依赖本地
        .git；装机侧拷贝没有 .git 也能跑）。只认 `v` 前缀 tag，格式
        `vYYYY.MM.DD-<suffix>`：日期为主序、同日取字典序最大。
  本地面：skills.lock.json 的四个锁技能 skill_version + pipeline VERSION 文件
        version 行 + 锁文件 sha256。
  基线：本地自报构建基线日期——优先 skills.lock.history.json 最后一条
        recorded_at 的 ISO 日期部分（装机侧 lock 旁若有 history 拷贝即用之）；
        否则 fallback 读 VERSION 的 release_date；pipeline version 的 hotfix
        后缀（如 9R25）与 tag 日期不可比，一律不猜。
  判定：远端最新 tag 日期 > 本地基线日期 → behind；相等或更小 → current；
        不可比（基线缺失 / ls-remote 失败 / 远端无可识别 tag）→ unknown。

stdout 输出单行 JSON（stdout 单行，永不抛错退出）：
  {"status": "current|behind|unknown", "current": {...本地快照},
   "latest": "<tag 或 null>", "detail": "<原因/指引>"}

CLI：python -X utf8 scripts/version_check.py
     [--skills-home <path>] [--repo-root <path>] [--remote <url>]
默认 skills-home / repo-root 从脚本位置推（scripts/../../ = skills home，
再上一层 = 仓库根）。纯 stdlib。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ORIGIN_URL = "https://github.com/Amer-CN/wxgzh-skills.git"
LOCKED_SKILLS = ["super-writer", "zh-human-writing", "media-enrichment", "gzh-design"]
TAG_RE = re.compile(r"^v(\d{4})\.(\d{2})\.(\d{2})(?:-(.+))?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LS_REMOTE_TIMEOUT = 15

_SCRIPT = Path(__file__).resolve()


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_kv(text: str, key: str) -> str | None:
    """VERSION 文件 `key: value` 行解析（如 version: / release_date:）。"""
    for line in text.splitlines():
        m = re.match(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", line)
        if m:
            return m.group(1)
    return None


def _resolve_lock(skills_home: Path | None, repo_root: Path | None) -> Path | None:
    here_root = _SCRIPT.parents[1]  # …/wxgzh-pipeline
    cands = []
    if skills_home:
        cands.append(Path(skills_home) / "wxgzh-pipeline" / "skills.lock.json")
    if repo_root:
        cands.append(Path(repo_root) / "skills" / "wxgzh-pipeline" / "skills.lock.json")
        cands.append(Path(repo_root) / "skills.lock.json")
    cands.append(here_root / "skills.lock.json")
    for c in cands:
        if c.is_file():
            return c
    return None


def _baseline_from_history(lock_path: Path) -> str | None:
    """skills.lock.history.json 最后一条 recorded_at 的 ISO 日期部分。"""
    hp = lock_path.parent / "skills.lock.history.json"
    if not hp.is_file():
        return None
    try:
        h = json.loads(hp.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    records = h if isinstance(h, list) else (h.get("records") or h.get("history") or [])
    if not records:
        return None
    last = records[-1] if isinstance(records[-1], dict) else {}
    ra = str(last.get("recorded_at") or "")
    return ra[:10] if DATE_RE.match(ra[:10]) else None


def _baseline_from_version(version_file: Path) -> str | None:
    """fallback：VERSION 文件 release_date（YYYY-MM-DD）。"""
    if not version_file.is_file():
        return None
    try:
        rd = _read_kv(version_file.read_text(encoding="utf-8"), "release_date")
    except OSError:
        return None
    return rd if rd and DATE_RE.match(rd) else None


def _ls_remote_tags(remote: str) -> tuple[list[str], str | None]:
    """git ls-remote --tags；返回 (v 前缀 tag 名列表, 错误或 None)。"""
    try:
        proc = subprocess.run(["git", "ls-remote", "--tags", remote],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=LS_REMOTE_TIMEOUT)
    except Exception as e:  # noqa: BLE001 — git 缺失/超时等一律降级 unknown
        return [], f"git ls-remote 不可用: {e}"
    if proc.returncode != 0:
        return [], (f"git ls-remote 失败 rc={proc.returncode}: "
                    f"{((proc.stderr or proc.stdout or '').strip())[-200:]}")
    tags = []
    for line in (proc.stdout or "").splitlines():
        ref = line.split("\t", 1)[-1].strip() if "\t" in line else ""
        if ref.startswith("refs/tags/"):
            name = ref[len("refs/tags/"):]
            if name.endswith("^{}"):  # peeled annotated tag：与本体同名，去重
                name = name[:-3]
            tags.append(name)
    return sorted(set(tags)), None


def _latest_vtag(tags: list[str]) -> tuple[str | None, tuple | None]:
    """v 前缀 tag 里按（日期主序、同日字典序最大 suffix）取最新。"""
    best, best_key = None, None
    for t in tags:
        m = TAG_RE.match(t)
        if not m:
            continue
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        key = ((y, mo, d), m.group(4) or "")
        if best_key is None or key > best_key:
            best, best_key = t, key
    return best, (best_key[0] if best_key else None)


def check(skills_home: str | Path | None = None,
          repo_root: str | Path | None = None,
          remote: str = ORIGIN_URL) -> dict:
    """核心判定；返回结果 dict（不打印、不退出）。"""
    skills_home = Path(skills_home) if skills_home else _SCRIPT.parents[2]
    repo_root = Path(repo_root) if repo_root else _SCRIPT.parents[3]

    lock = _resolve_lock(skills_home, repo_root)
    snapshot: dict = {"skills": {}, "pipeline_version": None,
                      "lock_sha256": None, "lock_path": None,
                      "baseline_date": None, "baseline_source": None}
    if lock is None:
        detail = "skills.lock.json 未找到（skills-home/repo-root 下均无）"
        baseline = None
    else:
        try:
            lk = json.loads(lock.read_text(encoding="utf-8"))
            snapshot["skills"] = {name: (lk.get("skills", {}).get(name) or {}).get("skill_version")
                                  for name in LOCKED_SKILLS}
        except (ValueError, OSError) as e:
            detail = f"skills.lock.json 不可解析: {e}"
            lk = None
        snapshot["lock_sha256"] = _sha256_file(lock)
        snapshot["lock_path"] = str(lock)
        version_file = lock.parent / "VERSION"
        try:
            snapshot["pipeline_version"] = _read_kv(
                version_file.read_text(encoding="utf-8"), "version")
        except OSError:
            snapshot["pipeline_version"] = None
        baseline = _baseline_from_history(lock)
        if baseline:
            snapshot["baseline_source"] = "skills.lock.history.json"
            detail = ""
        else:
            baseline = _baseline_from_version(version_file)
            if baseline:
                snapshot["baseline_source"] = "VERSION release_date"
                detail = ""
            else:
                baseline = None
                snapshot["baseline_source"] = None
                detail = ("本地构建基线日期不可得（history 缺失且 VERSION 无 "
                          "release_date），不可比即 unknown")
        snapshot["baseline_date"] = baseline
    if lock is None:
        return {"status": "unknown", "current": snapshot, "latest": None,
                "detail": detail}

    tags, err = _ls_remote_tags(remote)
    if err:
        return {"status": "unknown", "current": snapshot, "latest": None,
                "detail": err}
    latest, tag_date = _latest_vtag(tags)
    if latest is None:
        return {"status": "unknown", "current": snapshot, "latest": None,
                "detail": f"远端无 v 前缀 tag（vYYYY.MM.DD-<suffix>）可识别：{remote}"}
    if baseline is None:
        return {"status": "unknown", "current": snapshot, "latest": latest,
                "detail": detail}
    snapshot["baseline_date"] = baseline
    if tag_date > tuple(int(x) for x in baseline.split("-")):
        return {"status": "behind", "current": snapshot, "latest": latest,
                "detail": (f"远端最新 tag {latest}（{'.'.join(map(str, tag_date))}）"
                           f"晚于本地构建基线 {baseline}——更新（拉取+installer+"
                           "SECURITY.md §8/§9 基线对账）或 --allow-stale 继续")}
    return {"status": "current", "current": snapshot, "latest": latest,
            "detail": (f"本地构建基线 {baseline} 不早于远端最新 tag "
                       f"{latest}（{'.'.join(map(str, tag_date))}）——无需更新")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="version_check")
    ap.add_argument("--skills-home", default=None)
    ap.add_argument("--repo-root", default=None)
    ap.add_argument("--remote", default=ORIGIN_URL)
    a = ap.parse_args(argv)
    print(json.dumps(check(a.skills_home, a.repo_root, a.remote),
                     ensure_ascii=False))
    return 0  # 建议性工具：永远 exit 0


if __name__ == "__main__":
    sys.exit(main())
