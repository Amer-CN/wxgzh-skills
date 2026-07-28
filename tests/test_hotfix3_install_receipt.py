"""hotfix3 P0#1: EXTERNAL install receipt (<skills_home>/.install-receipts/<skill>.json).

The receipt is generated at install time from the REAL checkout, records the
recomputed installed runtime root/manifest hashes, verifies the checked-out HEAD
equals skills.lock.full_commit_sha (else FAIL_CLOSED), and NEVER counts toward
the skill runtime root hash (avoids commit/hash self-reference inside the repo).
"""
import json
from pathlib import Path

import pytest

from wxgzh_pipeline import skill_discovery as SD
from wxgzh_pipeline.skill_discovery import (InstallReceiptError, install_receipt_path,
                                            read_install_receipt, write_install_receipt)

COMMIT = "0007d7e6a4493aab59070d9c31dcde83830302fd"


def _mk_gzh(home: Path):
    root = home / "gzh-design"
    (root / "scripts").mkdir(parents=True)
    (root / "VERSION").write_text("version: v2026.07.18-hammer.1\n", encoding="utf-8")
    (root / "scripts" / "render_article.py").write_text("# render entry\n", encoding="utf-8")
    (root / "scripts" / "generate_hammer_upgrade_samples.py").write_text(
        "# components\n", encoding="utf-8")
    return root


def test_receipt_matches_recompute_and_lives_outside_skill(tmp_path):
    home = tmp_path / "skills"; _mk_gzh(home)
    root_sha, _ = SD.compute_root_sha(home / "gzh-design")
    man_sha, _ = SD.compute_runtime_manifest_sha(home / "gzh-design")
    rec = write_install_receipt(home, "gzh-design", repository_url="https://x/gzh-design",
                                actual_commit=COMMIT, expected_commit=COMMIT,
                                source_tree_sha="t" * 40)
    assert rec["full_commit_sha"] == COMMIT
    assert rec["installed_runtime_root_sha256"] == root_sha
    assert rec["installed_runtime_manifest_sha256"] == man_sha
    # the receipt is OUTSIDE the skill tree, under skills_home/.install-receipts
    p = install_receipt_path(home, "gzh-design")
    assert p.is_file() and p.parent.name == ".install-receipts"
    assert "gzh-design" not in p.relative_to(home).parts[:-1]
    assert read_install_receipt(home, "gzh-design")["full_commit_sha"] == COMMIT


def test_head_mismatch_fails_closed_and_writes_nothing(tmp_path):
    home = tmp_path / "skills"; _mk_gzh(home)
    with pytest.raises(InstallReceiptError):
        write_install_receipt(home, "gzh-design", repository_url="r",
                              actual_commit="a" * 40, expected_commit=COMMIT)
    # a mismatched checkout must NOT leave a receipt behind
    assert read_install_receipt(home, "gzh-design") is None


def test_receipt_never_counts_toward_root_hash(tmp_path):
    home = tmp_path / "skills"; _mk_gzh(home)
    before, nfiles = SD.compute_root_sha(home / "gzh-design")
    write_install_receipt(home, "gzh-design", repository_url="r",
                          actual_commit=COMMIT, expected_commit=COMMIT)
    after, nfiles_after = SD.compute_root_sha(home / "gzh-design")
    assert after == before and nfiles_after == nfiles
    # even a stray .install-receipts INSIDE the skill tree is excluded
    stray = home / "gzh-design" / ".install-receipts"; stray.mkdir()
    (stray / "gzh-design.json").write_text("{}", encoding="utf-8")
    after2, _ = SD.compute_root_sha(home / "gzh-design")
    assert after2 == before


def test_read_missing_or_malformed_returns_none(tmp_path):
    home = tmp_path / "skills"; _mk_gzh(home)
    assert read_install_receipt(home, "gzh-design") is None
    p = install_receipt_path(home, "gzh-design"); p.parent.mkdir(parents=True)
    p.write_text("{not json", encoding="utf-8")
    assert read_install_receipt(home, "gzh-design") is None


def test_missing_expected_commit_is_forbidden(tmp_path):
    # hotfix4 P0#1: expected_commit=None is FORBIDDEN — the receipt can only be
    # written against a real 40-hex locked commit.
    home = tmp_path / "skills"; _mk_gzh(home)
    with pytest.raises(InstallReceiptError):
        write_install_receipt(home, "gzh-design", repository_url="r",
                              actual_commit=COMMIT, expected_commit=None)
    with pytest.raises(InstallReceiptError):
        write_install_receipt(home, "gzh-design", repository_url="r",
                              actual_commit=COMMIT, expected_commit="not-a-sha")
    assert read_install_receipt(home, "gzh-design") is None


def test_lock_bound_fields_enforced(tmp_path):
    """hotfix4 P0#1: repository_url and root/manifest must equal the lock."""
    home = tmp_path / "skills"; _mk_gzh(home)
    import wxgzh_pipeline.skill_discovery as SD2
    root_sha, _ = SD2.compute_root_sha(home / "gzh-design")
    man_sha, _ = SD2.compute_runtime_manifest_sha(home / "gzh-design")
    # wrong repository_url => FAIL, nothing written
    with pytest.raises(InstallReceiptError):
        write_install_receipt(home, "gzh-design", repository_url="https://evil.example/x",
                              actual_commit=COMMIT, expected_commit=COMMIT,
                              expected_repository_url="https://github.com/Amer-CN/gzh-design-skill")
    # wrong root hash vs lock => FAIL
    with pytest.raises(InstallReceiptError):
        write_install_receipt(home, "gzh-design", repository_url="r",
                              actual_commit=COMMIT, expected_commit=COMMIT,
                              expected_root_sha256="0" * 64)
    # wrong manifest hash vs lock => FAIL
    with pytest.raises(InstallReceiptError):
        write_install_receipt(home, "gzh-design", repository_url="r",
                              actual_commit=COMMIT, expected_commit=COMMIT,
                              expected_manifest_sha256="0" * 64)
    assert read_install_receipt(home, "gzh-design") is None
    # everything matching => receipt written
    rec = write_install_receipt(home, "gzh-design",
                                repository_url="https://github.com/Amer-CN/gzh-design-skill",
                                actual_commit=COMMIT, expected_commit=COMMIT,
                                expected_repository_url="https://github.com/Amer-CN/gzh-design-skill",
                                expected_root_sha256=root_sha,
                                expected_manifest_sha256=man_sha)
    assert rec["installed_runtime_root_sha256"] == root_sha
