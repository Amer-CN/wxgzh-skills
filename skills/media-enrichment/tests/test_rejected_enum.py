"""dev5 P0-1 tests: canonical rejected enum across all 15 rejection paths.

Covers:
- every classifier rejection path asserts decision == "rejected"
- manifests containing rejected assets pass the manifest schema
- summary.rejected_assets counts correctly
- rejected assets are never uploaded
- rejected assets never enter the final selection (eligible set)
- rejected assets do not participate in provenance-eligible computation
- REJECT_LITERAL_IN_RUNTIME_SOURCE == 0
"""

import json
import re
import sys
from pathlib import Path

import jsonschema
import pytest
from PIL import Image

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.image_classifier import classify_image
from media_enrichment.image_inspector import ImageInspection, inspect_image
from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord
from media_enrichment.uploader import MockUploader

CANONICAL_DECISIONS = {"eligible", "review_required", "rejected"}


def _inspection(width=800, height=600, valid=True, bomb=False):
    return ImageInspection(
        sha256="a" * 64, perceptual_hash="b" * 16, width=width, height=height,
        mime_type="image/png", file_size=1000, is_valid=valid,
        decompression_bomb=bomb, error="" if valid else "cannot decode",
    )


REJECTION_CASES = [
    # (case_id, url, inspection kwargs, classify kwargs)
    ("01_tracking_pixel_1x1", "https://example.com/img.png", dict(width=1, height=1), {}),
    ("02_extremely_small", "https://example.com/img.png", dict(width=4, height=4), {}),
    ("03_tracking_url", "https://analytics.example.com/pixel-tracker.png", {}, {}),
    ("04_favicon_url", "https://example.com/favicon.ico.png", {}, {}),
    ("05_avatar_url", "https://example.com/avatar/user9.jpg", {}, {}),
    ("06_logo_url", "https://example.com/assets/logo.png", {}, {}),
    ("07_ad_banner_url", "https://example.com/img/banner-728x90.png", {}, {}),
    ("08_placeholder_url", "https://example.com/no-image.png", {}, {}),
    ("09_avatar_context", "https://example.com/p.png", {}, {"context": "author avatar photo"}),
    ("10_logo_context", "https://example.com/p.png", {}, {"context": "company logo shown"}),
    ("11_ad_context", "https://example.com/p.png", {}, {"context": "sponsored advertisement block"}),
    ("12_undecodable", "https://example.com/p.png", dict(valid=False), {}),
    ("13_decompression_bomb", "https://example.com/p.png", dict(bomb=True), {}),
    ("14_below_min_dimensions", "https://example.com/p.png", dict(width=100, height=100), {}),
    ("15_restricted_copyright", "https://example.com/p.png", {}, {"copyright_status": "restricted"}),
    # dev6: social share cards / link preview images
    # 档HF-4/OBS-247:og:image/twitter:image 通道本身不再是拒绝路径(正常 URL
    # 放行),从 rejection 枚举移除;仅 URL 命中动态伪卡片端点仍拒绝(18)。
    ("18_opengraph_card_url", "https://example.com/items/abc/opengraph-image-1az256?x", {}, {}),
]


class TestAllRejectionPathsUseCanonicalEnum:
    @pytest.mark.parametrize("case_id,url,insp_kwargs,cls_kwargs",
                             REJECTION_CASES, ids=[c[0] for c in REJECTION_CASES])
    def test_rejection_path_decision_is_rejected(self, case_id, url, insp_kwargs, cls_kwargs):
        result = classify_image(url, _inspection(**insp_kwargs), **cls_kwargs)
        assert result.decision == "rejected", f"{case_id}: got {result.decision!r}"
        assert result.decision in CANONICAL_DECISIONS
        assert result.rejection_reasons, f"{case_id}: rejection must carry reasons"

    def test_rejected_paths_tested_at_least_15(self):
        assert len(REJECTION_CASES) >= 15


def _rejected_asset(i):
    return AssetRecord(
        asset_id=f"A-{i:03d}", asset_origin="source",
        material_ids=["M-001"], claim_ids=["C-01-a"],
        aihot_permalink="https://aihot.virxact.com/items/x",
        source_page_url="https://aihot.virxact.com/items/x",
        discovered_url="https://example.com/logo.png",
        resolved_original_url="https://example.com/logo.png",
        extraction_method="img_src", decode_method="none",
        sha256="c" * 64, quality_status="pass", relevance_status="irrelevant",
        copyright_status="unknown", copyright_risk="high",
        decision="rejected", reasons=["URL matches logo/brandmark pattern"],
    )


class TestRejectedAssetsInManifest:
    def _manifest_with_rejected(self, n=3):
        builder = ManifestBuilder(run_id="t", request_sha256="d" * 64,
                                  article_sha256="e" * 64, claims_total=1, materials_total=1)
        for i in range(1, n + 1):
            builder.add_asset(_rejected_asset(i))
        return builder, builder.build()

    def test_manifest_with_rejected_passes_schema(self):
        _, manifest = self._manifest_with_rejected()
        schema = json.loads((SKILL_ROOT / "schemas" / "media_manifest.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(instance=manifest, schema=schema)  # must not raise

    def test_summary_rejected_count(self):
        _, manifest = self._manifest_with_rejected(3)
        assert manifest["summary"]["rejected_assets"] == 3
        assert manifest["summary"]["eligible_assets"] == 0

    def test_rejected_never_uploaded(self):
        builder, manifest = self._manifest_with_rejected()
        # runner-side upload gate condition replicated: only eligible+known_allowed
        uploader = MockUploader()
        for asset in builder.assets:
            allowed = (asset.decision == "eligible"
                       and asset.copyright_status == "known_allowed"
                       and asset.quality_status == "pass"
                       and asset.relevance_status == "relevant"
                       and asset.duplicate_of is None)
            assert not allowed, "rejected asset must never satisfy the upload gate"
        assert uploader.upload_count == 0
        for a in manifest["assets"]:
            assert a["upload"]["status"] == "not_uploaded"
            assert a["upload"]["remote_url"] is None

    def test_rejected_never_in_final_selection(self):
        _, manifest = self._manifest_with_rejected()
        final_selection = [a for a in manifest["assets"] if a["decision"] == "eligible"]
        assert final_selection == []

    def test_rejected_excluded_from_provenance_gate(self):
        # a rejected asset without source_page_url must not break provenance_complete
        builder = ManifestBuilder(run_id="t", request_sha256="d" * 64,
                                  article_sha256="e" * 64, claims_total=1, materials_total=1)
        bad = _rejected_asset(1)
        bad.source_page_url = None
        bad.sha256 = None
        builder.add_asset(bad)
        good = _rejected_asset(2)
        good.decision = "eligible"
        good.copyright_status = "known_allowed"
        good.relevance_status = "relevant"
        builder.add_asset(good)
        manifest = builder.build()
        assert manifest["gate"]["provenance_complete"] is True


class TestNoRejectLiteralInRuntimeSource:
    RUNTIME_FILES = [
        "src/media_enrichment/image_classifier.py",
        "src/media_enrichment/manifest_builder.py",
        "src/media_enrichment/image_deduplicator.py",
        "src/media_enrichment/uploader.py",
        "src/media_enrichment/chart_generator.py",
        "scripts/run_media_enrichment.py",
        "scripts/validate_media_manifest.py",
    ]

    def test_reject_literal_in_runtime_source_is_zero(self):
        pattern = re.compile(r"""["']reject["']""")
        hits = []
        for rel in self.RUNTIME_FILES:
            text = (SKILL_ROOT / rel).read_text(encoding="utf-8")
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"{rel}:{i}: {line.strip()}")
        assert hits == [], f"REJECT_LITERAL_IN_RUNTIME_SOURCE must be 0, found: {hits}"

    def test_schema_enum_not_polluted(self):
        schema = json.loads((SKILL_ROOT / "schemas" / "media_manifest.schema.json").read_text(encoding="utf-8"))
        text = json.dumps(schema)
        assert '"rejected"' in text
        assert re.search(r'"reject"', text) is None, "'reject' must NOT be added to the schema enum"


class TestRealImageRejectionEndToEnd:
    def test_real_small_image_rejected_with_canonical_enum(self, tmp_path):
        img = Image.new("RGB", (200, 100), color=(1, 2, 3))
        p = tmp_path / "small.png"
        img.save(str(p), "PNG")
        insp = inspect_image(p)
        result = classify_image("https://example.com/content/small.png", insp)
        assert result.decision == "rejected"
