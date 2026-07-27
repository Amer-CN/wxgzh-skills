"""dev5 regression tests from the real kimi-k3-visual-acceptance-v1 failure.

Fixtures are the actual images downloaded during the failed integration run:
- a001-aisi-logo-pattern.png  (rejected: logo URL pattern)
- a006-substack-ad-url.png    (rejected: ad/banner URL pattern)
- a010-ithome-1193x296.jpg    (rejected: below minimum dimensions)

Expected: every decision == "rejected", manifest passes schema,
summary.rejected_assets == 3, formal validator logic accepts the enum.
"""

import json
import sys
from pathlib import Path

import jsonschema
import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.image_classifier import classify_image
from media_enrichment.image_inspector import inspect_image
from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord

FIXDIR = SKILL_ROOT / "fixtures" / "images" / "regression"

# These regression fixtures are real third-party images captured from a live
# run and are intentionally NOT shipped in the open-source repository. When
# absent, the whole regression module is skipped; run it in the full internal
# tree (which contains fixtures/images/regression/) to exercise these cases.
pytestmark = pytest.mark.skipif(
    not FIXDIR.exists(),
    reason="third-party regression image fixtures not shipped in OSS repo",
)

# (fixture file, real URL from the failed run, asset id)
CASES = [
    ("a001-aisi-logo-pattern.png",
     "https://the-decoder.com/wp-content/uploads/2026/07/aisi_logo_pattern.png",
     "A-001"),
    ("a006-substack-ad-url.png",
     "https://substackcdn.com/image/fetch/$s_!Nx9b!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/"
     "https://substack-post-media.s3.amazonaws.com/public/images/82e1199f-6328-4f15-b648-2f6cb0b984ad_906x440.png",
     "A-006"),
    ("a010-ithome-1193x296.jpg",
     "https://img.ithome.com/newsuploadfiles/2026/7/3d42bc66-7584-4c54-a327-1431b329606e.jpg?x-bce-process=image/quality,q_75/format,f_webp",
     "A-010"),
]


@pytest.fixture(scope="module")
def classified():
    results = {}
    for fname, url, aid in CASES:
        path = FIXDIR / fname
        assert path.exists(), f"regression fixture missing: {fname}"
        inspection = inspect_image(path)
        results[aid] = (classify_image(url, inspection), inspection, url, path)
    return results


class TestRealFailureAssetsRejected:
    @pytest.mark.parametrize("aid", ["A-001", "A-006", "A-010"])
    def test_decision_is_rejected(self, classified, aid):
        result, _, _, _ = classified[aid]
        assert result.decision == "rejected", f"{aid}: got {result.decision!r}"

    def test_a010_reason_is_dimensions(self, classified):
        result, inspection, _, _ = classified["A-010"]
        assert inspection.width == 1193 and inspection.height == 296
        assert any("below minimum" in r for r in result.rejection_reasons)


class TestRealFailureManifestRegression:
    def _build_manifest(self, classified):
        builder = ManifestBuilder(run_id="regression-visual-acceptance-v1",
                                  request_sha256="f" * 64, article_sha256="e" * 64,
                                  claims_total=106, materials_total=47)
        for fname, url, aid in CASES:
            result, inspection, _, path = classified[aid]
            builder.add_asset(AssetRecord(
                asset_id=aid, asset_origin="source",
                material_ids=["M-001"], claim_ids=["C-01-a"],
                aihot_permalink="https://aihot.virxact.com/items/x",
                source_page_url="https://aihot.virxact.com/items/x",
                discovered_url=url, resolved_original_url=url,
                extraction_method="img_src", decode_method="none",
                local_path=str(path), sha256=inspection.sha256,
                perceptual_hash=inspection.perceptual_hash,
                mime_type=inspection.mime_type,
                width=inspection.width, height=inspection.height,
                file_size=inspection.file_size,
                quality_status="pass" if inspection.is_valid else "fail",
                relevance_status="irrelevant",
                copyright_status="unknown", copyright_risk="high",
                decision=result.decision,
                reasons=result.rejection_reasons,
            ))
        return builder.build()

    def test_manifest_schema_valid_and_summary(self, classified):
        manifest = self._build_manifest(classified)
        schema = json.loads((SKILL_ROOT / "schemas" / "media_manifest.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(instance=manifest, schema=schema)  # INPUT_SCHEMA_VALID=PASS
        assert manifest["summary"]["rejected_assets"] == 3
        assert manifest["summary"]["eligible_assets"] == 0
        assert manifest["summary"]["uploaded_assets"] == 0
        assert manifest["gate"]["publish_allowed"] is False

    def test_formal_validator_accepts_enum(self, classified, tmp_path):
        """Run the formal validator's schema+asset checks on the regression manifest."""
        sys.path.insert(0, str(SKILL_ROOT / "scripts"))
        from validate_media_manifest import validate_manifest
        manifest = self._build_manifest(classified)
        mpath = tmp_path / "media_manifest.json"
        mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        report = validate_manifest(str(mpath), None)  # no request: request checks fail by design
        by_name = {c["check"]: c["status"] for c in report["checks"]}
        # the dev4 defect check must now PASS
        assert by_name["INPUT_SCHEMA_VALID"] == "PASS"
        assert by_name["MANIFEST_ERRORS_EMPTY"] == "PASS"
        assert by_name["NO_REJECTED_ASSET_MARKED_ELIGIBLE"] == "PASS"
        assert by_name["NO_UNKNOWN_LICENSE_AUTO_APPROVED"] == "PASS"
