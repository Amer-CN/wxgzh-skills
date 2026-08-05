"""档71B OBS-102:语法门禁桥接 —— gzh_design 内容校验前置。

职责:
- 定位安装侧 gzh-design 渲染器(与 skills.lock 锁定版本一致,经 skill_discovery);
- probe 目录与缓存放在 RUN 目录内(.obs102-probe / .obs102-probe-cache.json),
  禁止跨 RUN 复用、禁止写入安装侧;
- 以生产调用方式(CLI 子进程)运行 validators/validate_syntax_gate.py;
- 返回 {"exit_code", "report"};任何异常 -> FAIL_CLOSED(不静默放行)。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _renderer_path(skills_home: Path, network_mode: str | None = None) -> Path:
    """定位 gzh-design 渲染器。

    - live / integration:安装侧被锁渲染器(skills.lock 锁定版本);
    - fake_live / offline_fixture:fake shim(fake_live/skills/gzh-design),它是
      该模式下真实被调用的渲染路径;probe 判据必须与实际执行路径一致。
    """
    if network_mode in ("fake_live", "offline_fixture"):
        shim = Path(__file__).resolve().parents[1] / "fake_live" / "skills" \
            / "gzh-design" / "render_article.py"
        if shim.is_file():
            return shim
    p = Path(skills_home) / "gzh-design" / "scripts" / "render_article.py"
    if not p.is_file():
        raise FileNotFoundError(f"gzh-design renderer missing: {p}")
    return p


def run_syntax_gate(ctx, sd: Path, state) -> dict | None:
    """在 gzh_design 内容校验中调用。返回 None 表示跳过(非实时/无冻结文章),
    否则返回 {"exit_code", "report"}。"""
    network_mode = getattr(ctx, "network_mode", None)
    # 门禁语义只在真实渲染路径(live/integration)生效;fake_live/offline 用 shim
    # 渲染,probe 判据会失真(两套真理),且这些模式不产生产物 -> 跳过。
    if network_mode not in ("live", "integration"):
        return None
    run_dir = Path(ctx.run_dir)
    article = run_dir / "zh_human_writing" / "final_article.md"
    if not article.is_file():
        return None
    try:
        renderer = _renderer_path(Path(ctx.skills_home), network_mode)
    except FileNotFoundError:
        return {"exit_code": 1,
                "report": {"OBS102_SYNTAX_GATE": "FAIL",
                           "reason": "gzh-design renderer missing"}}
    probe_dir = run_dir / ".obs102-probe"
    cache_path = run_dir / ".obs102-probe-cache.json"
    validator = (Path(__file__).resolve().parents[1] / "validators"
                 / "validate_syntax_gate.py")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(validator),
         "--article", str(article), "--renderer", str(renderer),
         "--probe-dir", str(probe_dir), "--cache", str(cache_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300)
    try:
        report = json.loads(proc.stdout or "{}")
    except ValueError:
        report = {"OBS102_SYNTAX_GATE": "FAIL",
                  "reason": f"validator output unparseable: {proc.stderr[-300:]}"}
        proc = type("P", (), {"returncode": 1})()
    return {"exit_code": proc.returncode, "report": report}
