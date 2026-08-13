#!/usr/bin/env python3
"""Test calibration script: behavioral + structural tests.

Tests:
- Metrics computation (MAE, Spearman with ties, classification)
- Sample loading with real fixtures (fails if missing)
- Architecture mode CLI
- Calibrated mode CLI with machine scores
- Missing machine scores failure
- ID overlap detection
- Blind set isolation with assertion
"""
from pathlib import Path
import json, sys, subprocess, tempfile

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from calibrate_scorer import (
    mean_absolute_error,
    spearman_rank_correlation,
    classification_accuracy,
    _classify,
    _rank_with_ties,
    check_id_overlap,
    load_samples,
    load_machine_scores,
    run_calibration,
    SCORING_DIMENSIONS,
    MAX_SCORE,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures'


# ── Unit tests for metrics ──

def test_mae():
    assert mean_absolute_error([80, 70, 90], [85, 65, 88]) == 4.0


def test_mae_empty():
    assert mean_absolute_error([], []) == float('inf')


def test_spearman_perfect():
    assert abs(spearman_rank_correlation([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1.0) < 0.001


def test_spearman_inverse():
    assert abs(spearman_rank_correlation([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) - (-1.0)) < 0.001


def test_spearman_with_ties():
    """Spearman must use average ranks for tied values."""
    # human: [80, 80, 70, 90] - two ties at 80
    # machine: [85, 85, 65, 88] - two ties at 85
    # With average ranks: human ranks = [2.5, 2.5, 1, 4], machine ranks = [2.5, 2.5, 1, 4]
    # Perfect correlation with proper tie handling
    result = spearman_rank_correlation([80, 80, 70, 90], [85, 85, 65, 88])
    assert abs(result - 1.0) < 0.001, f"Expected 1.0 for tied data with same ordering, got {result}"


def test_spearman_ties_different_order():
    """Ties in one list but not the other should give less than 1.0."""
    result = spearman_rank_correlation([80, 80, 70, 90], [85, 82, 65, 88])
    assert result < 1.0, f"Expected < 1.0 for asymmetric ties, got {result}"


def test_rank_with_ties():
    """_rank_with_ties assigns average ranks for tied values."""
    ranks = _rank_with_ties([30, 10, 20, 10])
    # sorted: 10, 10, 20, 30 -> ranks: 1.5, 1.5, 3, 4
    # original positions: 30->4, 10->1.5, 20->3, 10->1.5
    assert ranks == [4, 1.5, 3, 1.5]


def test_classification():
    assert _classify(95, {"reject": 70, "revise": 82}) == "publish"
    assert _classify(75, {"reject": 70, "revise": 82}) == "revise"
    assert _classify(60, {"reject": 70, "revise": 82}) == "reject"


def test_classification_accuracy():
    human = [95, 75, 60, 85, 65]
    machine = [90, 78, 55, 88, 68]
    acc = classification_accuracy(human, machine)
    assert acc == 1.0


def test_max_score():
    assert MAX_SCORE == 100


def test_dimensions_count():
    assert len(SCORING_DIMENSIONS) == 9


# ── ID overlap test ──

def test_id_overlap_detection():
    """ID overlap between calibration and blind sets must be detected."""
    cal_ids = ["sample-001", "sample-002", "sample-003"]
    blind_ids_ok = ["blind-001"]
    blind_ids_overlap = ["sample-001", "blind-001"]

    assert check_id_overlap(cal_ids, blind_ids_ok) == []
    overlap = check_id_overlap(cal_ids, blind_ids_overlap)
    assert "sample-001" in overlap


# ── Fixture-dependent tests (must fail if fixtures missing) ──

def test_sample_loading():
    """Test that sample loading works with real fixtures. Fails if missing."""
    samples_dir = FIXTURES / 'samples'
    labels_path = FIXTURES / 'labels.example.json'
    assert samples_dir.exists(), f"Samples directory missing: {samples_dir}"
    assert labels_path.exists(), f"Labels file missing: {labels_path}"

    samples = load_samples(str(samples_dir), str(labels_path))
    assert isinstance(samples, list)
    assert len(samples) == 3, f"Expected 3 samples, got {len(samples)}"
    assert samples[0]["article_id"] == "sample-001"
    assert "article_text" in samples[0]
    assert len(samples[0]["article_text"]) > 100, "Article text too short"


def test_machine_scores_loading():
    """Test that machine scores loading works with real fixtures. Fails if missing."""
    scores_path = FIXTURES / 'machine-scores.json'
    assert scores_path.exists(), f"Machine scores file missing: {scores_path}"

    scores = load_machine_scores(str(scores_path))
    assert len(scores) == 3
    assert "sample-001" in scores
    assert scores["sample-001"]["overall_score"] == 80
    assert "dimensions" in scores["sample-001"]


def test_calibration_architecture_mode():
    """Architecture mode works with placeholder scores."""
    samples_dir = FIXTURES / 'samples'
    labels_path = FIXTURES / 'labels.example.json'
    samples = load_samples(str(samples_dir), str(labels_path))
    assert len(samples) > 0, "No samples loaded"

    result = run_calibration(samples, mode="architecture")
    assert result["calibration_status"] == "architecture_only"
    assert result["mode"] == "architecture"
    assert "metrics" in result
    assert "mae" in result["metrics"]
    assert "spearman" in result["metrics"]
    assert "per_sample" in result


def test_calibration_calibrated_mode():
    """Calibrated mode works with real machine scores."""
    samples_dir = FIXTURES / 'samples'
    labels_path = FIXTURES / 'labels.example.json'
    scores_path = FIXTURES / 'machine-scores.json'

    samples = load_samples(str(samples_dir), str(labels_path))
    machine_scores = load_machine_scores(str(scores_path))

    result = run_calibration(samples, machine_scores, mode="calibrated")
    assert result["calibration_status"] == "calibrated"
    assert result["mode"] == "calibrated"
    # Machine scores should not be 0
    for ps in result["per_sample"]:
        assert ps["machine_score"] > 0, f"Machine score is 0 for {ps['article_id']}"


def test_calibration_calibrated_missing_scores_fails():
    """Calibrated mode must fail when machine scores are missing."""
    samples_dir = FIXTURES / 'samples'
    labels_path = FIXTURES / 'labels.example.json'
    samples = load_samples(str(samples_dir), str(labels_path))

    try:
        run_calibration(samples, mode="calibrated")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "machine_scores" in str(e).lower() or "calibrated" in str(e).lower()


# ── CLI tests ──

def test_cli_architecture_mode():
    """CLI architecture mode produces valid output."""
    output_path = FIXTURES / 'calibration-test-output.json'
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'calibrate_scorer.py'),
         '--mode', 'architecture',
         '--samples', str(FIXTURES / 'samples'),
         '--labels', str(FIXTURES / 'labels.example.json'),
         '--output', str(output_path)],
        capture_output=True, text=True
    )
    assert p.returncode == 0, p.stdout + p.stderr
    output = json.loads(output_path.read_text(encoding='utf-8'))
    assert 'calibration' in output
    assert output['calibration']['calibration_status'] == 'architecture_only'
    output_path.unlink()


def test_cli_calibrated_mode():
    """CLI calibrated mode with machine scores produces valid output."""
    output_path = FIXTURES / 'calibration-test-output.json'
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'calibrate_scorer.py'),
         '--mode', 'calibrated',
         '--samples', str(FIXTURES / 'samples'),
         '--labels', str(FIXTURES / 'labels.example.json'),
         '--machine-scores', str(FIXTURES / 'machine-scores.json'),
         '--output', str(output_path)],
        capture_output=True, text=True
    )
    assert p.returncode == 0, p.stdout + p.stderr
    output = json.loads(output_path.read_text(encoding='utf-8'))
    assert output['calibration']['calibration_status'] == 'calibrated'
    # Verify machine scores are not 0
    for ps in output['calibration']['per_sample']:
        assert ps['machine_score'] > 0
    output_path.unlink()


def test_cli_calibrated_without_machine_scores_fails():
    """CLI calibrated mode without --machine-scores must fail."""
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'calibrate_scorer.py'),
         '--mode', 'calibrated',
         '--samples', str(FIXTURES / 'samples'),
         '--labels', str(FIXTURES / 'labels.example.json'),
         '--output', str(FIXTURES / 'calibration-test-output.json')],
        capture_output=True, text=True
    )
    assert p.returncode != 0, "Should have failed without --machine-scores"


def test_cli_with_blind_set():
    """CLI with blind set checks ID overlap and produces blind results."""
    output_path = FIXTURES / 'calibration-test-output.json'
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'calibrate_scorer.py'),
         '--mode', 'calibrated',
         '--samples', str(FIXTURES / 'samples'),
         '--labels', str(FIXTURES / 'labels.example.json'),
         '--machine-scores', str(FIXTURES / 'machine-scores.json'),
         '--blind', str(FIXTURES / 'blind'),
         '--blind-labels', str(FIXTURES / 'blind-labels.json'),
         '--blind-machine-scores', str(FIXTURES / 'blind-machine-scores.json'),
         '--output', str(output_path)],
        capture_output=True, text=True
    )
    assert p.returncode == 0, p.stdout + p.stderr
    output = json.loads(output_path.read_text(encoding='utf-8'))
    assert output['blind_test'] is not None
    assert output['blind_test']['calibration_status'] == 'calibrated'
    output_path.unlink()


def test_cli_blind_id_overlap_fails():
    """CLI must fail when calibration and blind sets have overlapping IDs."""
    # Use the same labels for both calibration and blind (same IDs = overlap)
    output_path = FIXTURES / 'calibration-test-output.json'
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'calibrate_scorer.py'),
         '--mode', 'calibrated',
         '--samples', str(FIXTURES / 'samples'),
         '--labels', str(FIXTURES / 'labels.example.json'),
         '--machine-scores', str(FIXTURES / 'machine-scores.json'),
         '--blind', str(FIXTURES / 'samples'),
         '--blind-labels', str(FIXTURES / 'labels.example.json'),
         '--blind-machine-scores', str(FIXTURES / 'machine-scores.json'),
         '--output', str(output_path)],
        capture_output=True, text=True
    )
    assert p.returncode != 0, "Should have failed due to ID overlap"
    assert 'overlap' in p.stdout.lower() or 'overlap' in p.stderr.lower()


# ── Label schema test ──

def test_label_schema():
    """Test that labels.example.json has the correct schema."""
    labels_path = FIXTURES / 'labels.example.json'
    assert labels_path.exists(), "Labels file missing"
    labels = json.loads(labels_path.read_text(encoding='utf-8'))
    assert isinstance(labels, list)
    assert len(labels) == 3
    label = labels[0]
    assert "article_id" in label
    assert "human_verdict" in label
    assert "score" in label
    assert "strengths" in label
    assert "p0" in label
    assert "p1" in label
    assert "p2" in label
    assert "reasoning_summary" in label


# ── R1: Spearman with ties uses Pearson on rank vectors ──

def test_spearman_asymmetric_ties_exact():
    """R1: Spearman with asymmetric ties must match Pearson-on-ranks.

    Input [1,1,2,2,3] vs [1,2,2,3,3]:
    - human ranks:  [1.5, 1.5, 3.5, 3.5, 5.0]
    - machine ranks: [1.0, 2.5, 2.5, 4.5, 4.5]
    - Pearson on these rank vectors = 0.80556 (approx)
    """
    result = spearman_rank_correlation([1, 1, 2, 2, 3], [1, 2, 2, 3, 3])
    expected = 0.80556
    assert abs(result - expected) < 0.001, f"Expected ~{expected}, got {result}"


def test_spearman_zero_variance():
    """R1: If one vector has zero variance (all same), return 0.0."""
    result = spearman_rank_correlation([5, 5, 5, 5], [1, 2, 3, 4])
    assert result == 0.0, f"Expected 0.0 for zero variance, got {result}"


def test_spearman_both_zero_variance():
    """R1: If both vectors have zero variance, return 0.0."""
    result = spearman_rank_correlation([5, 5, 5], [3, 3, 3])
    assert result == 0.0


def test_pearson_basic():
    """R1: Pearson helper works correctly."""
    from calibrate_scorer import _pearson
    # Perfect positive correlation
    assert abs(_pearson([1, 2, 3, 4, 5], [2, 4, 6, 8, 10]) - 1.0) < 0.001
    # Perfect negative
    assert abs(_pearson([1, 2, 3, 4, 5], [10, 8, 6, 4, 2]) - (-1.0)) < 0.001


# ── R2: load_samples fails on missing articles ──

def test_load_samples_missing_article_fails():
    """R2: load_samples must fail when article files are missing."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        labels = [{"article_id": "nonexistent-001", "score": 80}]
        labels_path = Path(tmpdir) / "labels.json"
        labels_path.write_text(_json.dumps(labels), encoding='utf-8')
        samples_dir = Path(tmpdir) / "samples"
        samples_dir.mkdir()
        try:
            load_samples(str(samples_dir), str(labels_path))
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "nonexistent-001" in str(e) or "Missing" in str(e)


def test_load_samples_duplicate_id_fails():
    """R2: load_samples must fail when labels have duplicate article_ids."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        labels = [
            {"article_id": "dup-001", "score": 80},
            {"article_id": "dup-001", "score": 90},
        ]
        labels_path = Path(tmpdir) / "labels.json"
        labels_path.write_text(_json.dumps(labels), encoding='utf-8')
        samples_dir = Path(tmpdir) / "samples"
        samples_dir.mkdir()
        # Create the file so it's not a "missing" error
        (samples_dir / "dup-001.md").write_text("A" * 100, encoding='utf-8')
        try:
            load_samples(str(samples_dir), str(labels_path))
            assert False, "Should have raised ValueError for duplicate"
        except ValueError as e:
            assert "Duplicate" in str(e) or "dup" in str(e).lower()


def test_load_samples_empty_article_fails():
    """R2: load_samples must fail when article file is empty."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        labels = [{"article_id": "empty-001", "score": 80}]
        labels_path = Path(tmpdir) / "labels.json"
        labels_path.write_text(_json.dumps(labels), encoding='utf-8')
        samples_dir = Path(tmpdir) / "samples"
        samples_dir.mkdir()
        (samples_dir / "empty-001.md").write_text("", encoding='utf-8')
        try:
            load_samples(str(samples_dir), str(labels_path))
            assert False, "Should have raised ValueError for empty file"
        except ValueError as e:
            assert "empty" in str(e).lower()


def test_load_samples_short_article_fails():
    """R2: load_samples must fail when article file is too short (<50 chars)."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        labels = [{"article_id": "short-001", "score": 80}]
        labels_path = Path(tmpdir) / "labels.json"
        labels_path.write_text(_json.dumps(labels), encoding='utf-8')
        samples_dir = Path(tmpdir) / "samples"
        samples_dir.mkdir()
        (samples_dir / "short-001.md").write_text("Too short.", encoding='utf-8')
        try:
            load_samples(str(samples_dir), str(labels_path))
            assert False, "Should have raised ValueError for short file"
        except ValueError as e:
            assert "short" in str(e).lower()


# ── H3: Machine scores defensive checks ──

def test_h3_duplicate_article_id_fails():
    """H3: load_machine_scores must fail on duplicate article_id."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        scores = [
            {"article_id": "dup-001", "overall_score": 80},
            {"article_id": "dup-001", "overall_score": 90},
        ]
        path = Path(tmpdir) / "scores.json"
        path.write_text(_json.dumps(scores), encoding='utf-8')
        try:
            load_machine_scores(str(path))
            assert False, "Should have raised ValueError for duplicate ID"
        except ValueError as e:
            assert "dup-001" in str(e) or "duplicate" in str(e).lower()


def test_h3_overall_score_above_100_fails():
    """H3: load_machine_scores must fail when overall_score > 100."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        scores = [{"article_id": "s1", "overall_score": 999}]
        path = Path(tmpdir) / "scores.json"
        path.write_text(_json.dumps(scores), encoding='utf-8')
        try:
            load_machine_scores(str(path))
            assert False, "Should have raised ValueError for score > 100"
        except ValueError as e:
            assert "0-100" in str(e) or "999" in str(e)


def test_h3_overall_score_negative_fails():
    """H3: load_machine_scores must fail when overall_score < 0."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        scores = [{"article_id": "s1", "overall_score": -5}]
        path = Path(tmpdir) / "scores.json"
        path.write_text(_json.dumps(scores), encoding='utf-8')
        try:
            load_machine_scores(str(path))
            assert False, "Should have raised ValueError for negative score"
        except ValueError as e:
            assert "0-100" in str(e) or "-5" in str(e)


def test_h3_dimension_out_of_range_fails():
    """H3: load_machine_scores must fail when a dimension score exceeds its max."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        scores = [{
            "article_id": "s1",
            "overall_score": 80,
            "dimensions": {
                "core_strength": 999,  # max is 15
                "uniqueness": 13,
                "argument_evidence": 11,
                "structure": 13,
                "specificity": 8,
                "reader_value": 9,
                "author_judgment": 8,
                "voice_consistency": 4,
                "completeness": 2,
            }
        }]
        path = Path(tmpdir) / "scores.json"
        path.write_text(_json.dumps(scores), encoding='utf-8')
        try:
            load_machine_scores(str(path))
            assert False, "Should have raised ValueError for dimension out of range"
        except ValueError as e:
            assert "core_strength" in str(e) or "0-15" in str(e)


def test_h3_dimension_sum_mismatch_fails():
    """H3: load_machine_scores must fail when dimension sum != overall_score."""
    import tempfile, json as _json
    with tempfile.TemporaryDirectory() as tmpdir:
        scores = [{
            "article_id": "s1",
            "overall_score": 50,  # actual sum of dimensions below is 80
            "dimensions": {
                "core_strength": 12,
                "uniqueness": 13,
                "argument_evidence": 11,
                "structure": 13,
                "specificity": 8,
                "reader_value": 9,
                "author_judgment": 8,
                "voice_consistency": 4,
                "completeness": 2,
            }
        }]
        path = Path(tmpdir) / "scores.json"
        path.write_text(_json.dumps(scores), encoding='utf-8')
        try:
            load_machine_scores(str(path))
            assert False, "Should have raised ValueError for dimension sum mismatch"
        except ValueError as e:
            assert "dimension sum" in str(e).lower() or "does not match" in str(e).lower()
