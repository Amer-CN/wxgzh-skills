"""Pipeline state + atomic disk persistence (temp -> fsync -> atomic rename).

State survives interruption; the agent never relies on chat context alone.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from . import STAGES


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path):
    """76F/OBS-279:读 JSON 容忍 BOM —— agent 侧工具若以 utf-8-sig 写文件,
    首字节 BOM 会让 json.loads(utf-8 文本) 直接失败;先按字节读并剥离 BOM。
    写 JSON 一律走 atomic_write_json(encoding="utf-8",无 BOM)。"""
    p = Path(path)
    raw = p.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return json.loads(raw.decode("utf-8"))


def atomic_write_json(path: Path, obj) -> None:
    """Write JSON atomically: temp file in same dir -> fsync -> os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        # Windows antivirus/indexers can briefly hold the destination open.
        # Retry the SAME atomic replace; never fall back to a non-atomic write.
        for attempt in range(5):
            try:
                os.replace(tmp, path)  # atomic on Windows and POSIX
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.01 * (attempt + 1))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


@dataclass
class PipelineState:
    run_id: str
    topic: str
    profile: str = "fast_publish"
    current_stage: str | None = None
    completed_stages: list = field(default_factory=list)
    failed_stage: str | None = None
    input_hashes: dict = field(default_factory=dict)
    output_hashes: dict = field(default_factory=dict)
    side_effects: list = field(default_factory=list)
    uploaded_image_count: int = 0
    image_shortfall: int = 0  # 76C:少图交付留痕(目标值-实际图数;0=无短少)
    cover_source: str = ""  # 77H:approved_body_image / placeholder_zero_image
    draft_created: bool = False
    formally_published: bool = False  # hard-fixed False; no code path sets True
    started_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    theme: str = "smartisan"
    final_article_sha256: str | None = None
    # OBS-64(档64):自有素材注入入口(--items-file);None = 正常 aihot 检索
    items_file: str | None = None
    # 77V:版本新鲜度检查留痕(unknown 或 behind+--allow-stale 时写入;
    # None = 本地版本 current 或未触发)。旧 state 无此键反序列化不崩。
    version_check: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineState":
        known = {k: d[k] for k in d if k in cls.__dataclass_fields__}
        return cls(**known)

    def is_complete(self) -> bool:
        return self.completed_stages == STAGES

    def next_stage(self) -> str | None:
        for s in STAGES:
            if s not in self.completed_stages:
                return s
        return None

    def mark_complete(self, stage: str) -> None:
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)
        self.failed_stage = None
        self.updated_at = _now()

    def mark_failed(self, stage: str) -> None:
        self.failed_stage = stage
        self.updated_at = _now()


def state_path(run_dir: Path) -> Path:
    return Path(run_dir) / "pipeline_state.json"


def save_state(run_dir: Path, st: PipelineState) -> None:
    st.updated_at = _now()
    atomic_write_json(state_path(run_dir), st.to_dict())


def load_state(run_dir: Path) -> PipelineState:
    return PipelineState.from_dict(json.loads(state_path(run_dir).read_text(encoding="utf-8")))
