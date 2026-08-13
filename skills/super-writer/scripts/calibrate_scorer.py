#!/usr/bin/env python3
"""Scorer calibration script.

Supports two explicit modes:
  --mode architecture: placeholder machine scores, for structural validation.
  --mode calibrated:   requires --machine-scores file with real Reviewer scores.

Usage:
    # Architecture mode (no real scores needed)
    python calibrate_scorer.py --mode architecture \
        --samples tests/fixtures/samples --labels tests/fixtures/labels.example.json

    # Calibrated mode (requires machine scores)
    python calibrate_scorer.py --mode calibrated \
        --samples tests/fixtures/samples --labels tests/fixtures/labels.example.json \
        --machine-scores tests/fixtures/machine-scores.json

    # With blind test set
    python calibrate_scorer.py --mode calibrated \
        --samples tests/fixtures/samples --labels tests/fixtures/labels.example.json \
        --machine-scores tests/fixtures/machine-scores.json \
        --blind tests/fixtures/blind --blind-labels tests/fixtures/blind-labels.json \
        --blind-machine-scores tests/fixtures/blind-machine-scores.json
"""
from pathlib import Path
import argparse, json, sys
from datetime import datetime

# ── Scoring configuration ──

SCORER_VERSION = "0.2.0"
SCORING_DIMENSIONS = {
    "core_strength": {"max": 15, "weight": 1.0},
    "uniqueness": {"max": 15, "weight": 1.0},
    "argument_evidence": {"max": 15, "weight": 1.0},
    "structure": {"max": 15, "weight": 1.0},
    "specificity": {"max": 10, "weight": 1.0},
    "reader_value": {"max": 10, "weight": 1.0},
    "author_judgment": {"max": 10, "weight": 1.0},
    "voice_consistency": {"max": 5, "weight": 1.0},
    "completeness": {"max": 5, "weight": 1.0},
}
MAX_SCORE = sum(d["max"] for d in SCORING_DIMENSIONS.values())  # 100

# ── Metrics ──

def mean_absolute_error(human: list, machine: list) -> float:
    """Compute MAE between human and machine scores."""
    if not human or not machine or len(human) != len(machine):
        return float('inf')
    return sum(abs(h - m) for h, m in zip(human, machine)) / len(human)


def _rank_with_ties(values: list) -> list:
    """Assign ranks with average ranks for ties (standard Spearman)."""
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg_rank
        i = j + 1
    return ranks


def _pearson(x: list, y: list) -> float:
    """Compute Pearson correlation coefficient."""
    n = len(x)
    if n != len(y) or n == 0:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    den_x = sum((xi - mean_x) ** 2 for xi in x)
    den_y = sum((yi - mean_y) ** 2 for yi in y)
    den = (den_x * den_y) ** 0.5
    if den == 0:
        return 0.0
    return num / den


def spearman_rank_correlation(human: list, machine: list) -> float:
    """Compute Spearman rank correlation coefficient.

    Uses Pearson correlation on rank vectors with average ranks for ties.
    This is the standard definition of Spearman with tie correction.
    Returns 0.0 if either vector has zero variance (all values identical).
    """
    if len(human) < 2:
        return 0.0
    human_ranks = _rank_with_ties(human)
    machine_ranks = _rank_with_ties(machine)
    return _pearson(human_ranks, machine_ranks)


def classification_accuracy(human: list, machine: list, thresholds: dict = None) -> float:
    """Compute classification accuracy (publish/revise/reject)."""
    if thresholds is None:
        thresholds = {"reject": 70, "revise": 82}
    correct = 0
    total = len(human)
    for h, m in zip(human, machine):
        h_class = _classify(h, thresholds)
        m_class = _classify(m, thresholds)
        if h_class == m_class:
            correct += 1
    return correct / total if total > 0 else 0.0


def _classify(score: int, thresholds: dict) -> str:
    if score < thresholds["reject"]:
        return "reject"
    elif score < thresholds["revise"]:
        return "revise"
    else:
        return "publish"


def check_id_overlap(calibration_ids: list, blind_ids: list) -> list:
    """Check for article_id overlap between calibration and blind sets.

    Returns list of overlapping IDs. Empty list means no overlap.
    """
    cal_set = set(calibration_ids)
    blind_set = set(blind_ids)
    return list(cal_set & blind_set)


# ── Sample loading ──

def load_samples(samples_dir: str, labels_path: str) -> list:
    """Load sample articles and their human labels.

    Does NOT load machine scores. Machine scores are loaded separately
    via load_machine_scores() and merged in run_calibration().

    Raises ValueError if any article file is missing, empty, too short,
    or if labels contain duplicate article_ids.
    """
    samples_dir = Path(samples_dir)
    if not Path(labels_path).exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    labels = json.loads(Path(labels_path).read_text(encoding='utf-8'))
    if not labels:
        raise ValueError(f"Labels file is empty: {labels_path}")

    # Check for duplicate article_ids
    ids = [l.get("article_id", "") for l in labels]
    seen = set()
    duplicates = []
    for aid in ids:
        if aid in seen:
            duplicates.append(aid)
        seen.add(aid)
    if duplicates:
        raise ValueError(f"Duplicate article_id in labels: {duplicates}")

    samples = []
    missing_ids = []
    for label in labels:
        aid = label["article_id"]
        article_path = samples_dir / f"{aid}.md"
        if not article_path.exists():
            missing_ids.append(aid)
            continue
        article_text = article_path.read_text(encoding='utf-8')
        if not article_text.strip():
            raise ValueError(f"Article file is empty: {aid}.md")
        if len(article_text.strip()) < 50:
            raise ValueError(f"Article file too short (<50 chars): {aid}.md")
        samples.append({
            "article_id": aid,
            "article_text": article_text,
            "human_verdict": label.get("human_verdict", ""),
            "human_score": label.get("score", 0),
            "human_strengths": label.get("strengths", []),
            "human_p0": label.get("p0", []),
            "human_p1": label.get("p1", []),
            "human_p2": label.get("p2", []),
            "human_reasoning": label.get("reasoning_summary", ""),
        })

    if missing_ids:
        raise ValueError(
            f"Missing {len(missing_ids)} article file(s) in {samples_dir}: {missing_ids}. "
            f"Expected {len(labels)} articles, found {len(samples)}."
        )
    return samples


def load_machine_scores(machine_scores_path: str) -> dict:
    """Load machine scores from a separate JSON file.

    Expected format:
    [
        {
            "article_id": "sample-001",
            "overall_score": 85,
            "dimensions": {"core_strength": 13, ...},
            "reviewer_version": "0.1.0",
            "run_config": {...}
        },
        ...
    ]

    Returns dict keyed by article_id.

    Raises ValueError for:
    - Duplicate article_id
    - overall_score outside [0, 100]
    - Dimension score outside [0, max] for that dimension
    - Dimension sum not matching overall_score
    """
    if not machine_scores_path or not Path(machine_scores_path).exists():
        raise FileNotFoundError(f"Machine scores file not found: {machine_scores_path}")

    data = json.loads(Path(machine_scores_path).read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise ValueError("Machine scores file must be a JSON array")

    scores = {}
    for entry in data:
        aid = entry.get("article_id", "")
        if not aid:
            raise ValueError("Machine score entry missing article_id")
        if aid in scores:
            raise ValueError(f"Duplicate article_id in machine scores: '{aid}'")
        if "overall_score" not in entry:
            raise ValueError(f"Machine score entry '{aid}' missing overall_score")

        overall = entry["overall_score"]
        if not isinstance(overall, (int, float)):
            raise ValueError(
                f"Machine score entry '{aid}': overall_score must be a number, got {type(overall).__name__}"
            )
        if overall < 0 or overall > 100:
            raise ValueError(
                f"Machine score entry '{aid}': overall_score must be 0-100, got {overall}"
            )

        # Validate dimensions if present
        dimensions = entry.get("dimensions", {})
        if dimensions:
            if not isinstance(dimensions, dict):
                raise ValueError(
                    f"Machine score entry '{aid}': dimensions must be a JSON object"
                )
            dim_sum = 0
            for dim_name, dim_max in SCORING_DIMENSIONS.items():
                if dim_name in dimensions:
                    dim_val = dimensions[dim_name]
                    if not isinstance(dim_val, (int, float)):
                        raise ValueError(
                            f"Machine score entry '{aid}': dimension '{dim_name}' must be a number, got {type(dim_val).__name__}"
                        )
                    if dim_val < 0 or dim_val > dim_max["max"]:
                        raise ValueError(
                            f"Machine score entry '{aid}': dimension '{dim_name}' must be 0-{dim_max['max']}, got {dim_val}"
                        )
                    dim_sum += dim_val
            # Check dimension sum consistency (allow ±1 tolerance for rounding)
            if abs(dim_sum - overall) > 1:
                raise ValueError(
                    f"Machine score entry '{aid}': dimension sum ({dim_sum}) "
                    f"does not match overall_score ({overall})"
                )

        scores[aid] = entry
    return scores


# ── Calibration execution ──

def run_calibration(samples: list, machine_scores: dict = None, scorer_config: dict = None,
                    mode: str = "architecture") -> dict:
    """Run calibration on samples and compute metrics.

    Args:
        samples: List of sample dicts from load_samples().
        machine_scores: Dict from load_machine_scores(), keyed by article_id.
                        Required for mode='calibrated'. Ignored for mode='architecture'.
        scorer_config: Optional scorer configuration.
        mode: 'architecture' or 'calibrated'.
    """
    if not samples:
        raise ValueError("No samples provided. Cannot run calibration.")

    if mode == "calibrated":
        if not machine_scores:
            raise ValueError("Calibrated mode requires machine_scores. Use --machine-scores.")
        # Merge machine scores into samples
        missing = []
        for s in samples:
            aid = s["article_id"]
            if aid in machine_scores:
                s["machine_score"] = machine_scores[aid]["overall_score"]
                s["machine_dimensions"] = machine_scores[aid].get("dimensions", {})
            else:
                missing.append(aid)
                s["machine_score"] = None
        if missing:
            raise ValueError(
                f"Machine scores missing for {len(missing)} articles: {missing}. "
                f"Every sample must have a corresponding machine score."
            )
        cal_status = "calibrated"
        note = "Calibrated with real Reviewer scores."
    else:
        # Architecture mode: use placeholder 0 scores
        for s in samples:
            s["machine_score"] = 0
        cal_status = "architecture_only"
        note = "Architecture mode: placeholder scores. Use --mode calibrated for real scores."

    machine_scores_list = [s["machine_score"] for s in samples]
    human_scores_list = [s["human_score"] for s in samples]

    mae = mean_absolute_error(human_scores_list, machine_scores_list)
    spearman = spearman_rank_correlation(human_scores_list, machine_scores_list)
    accuracy = classification_accuracy(human_scores_list, machine_scores_list)

    return {
        "scorer_version": SCORER_VERSION,
        "scorer_config": scorer_config or {},
        "timestamp": datetime.now().isoformat(),
        "mode": mode,
        "sample_count": len(samples),
        "metrics": {
            "mae": round(mae, 4),
            "spearman": round(spearman, 4),
            "classification_accuracy": round(accuracy, 4),
        },
        "per_sample": [
            {
                "article_id": s["article_id"],
                "human_score": s["human_score"],
                "machine_score": s["machine_score"],
                "diff": s["machine_score"] - s["human_score"],
            }
            for s in samples
        ],
        "calibration_status": cal_status,
        "note": note,
    }


def main():
    p = argparse.ArgumentParser(description="Scorer calibration script.")
    p.add_argument('--mode', choices=['architecture', 'calibrated'], default='architecture',
                   help='architecture: placeholder scores; calibrated: requires real machine scores')
    p.add_argument('--samples', required=True, help='Path to samples directory')
    p.add_argument('--labels', required=True, help='Path to human labels JSON file')
    p.add_argument('--machine-scores', default=None,
                   help='Path to machine scores JSON file (required for --mode calibrated)')
    p.add_argument('--blind', default=None, help='Path to blind test directory (optional)')
    p.add_argument('--blind-labels', default=None, help='Path to blind test labels JSON file')
    p.add_argument('--blind-machine-scores', default=None,
                   help='Path to blind test machine scores JSON file')
    p.add_argument('--output', default='calibration-report.json')
    p.add_argument('--scorer-config', default=None, help='Path to scorer config JSON')
    a = p.parse_args()

    # Validate mode requirements
    if a.mode == "calibrated" and not a.machine_scores:
        p.error("--mode calibrated requires --machine-scores")
    if a.mode == "calibrated" and a.blind and not a.blind_machine_scores:
        p.error("--mode calibrated with --blind requires --blind-machine-scores")

    # Load scorer config
    scorer_config = {}
    if a.scorer_config and Path(a.scorer_config).exists():
        scorer_config = json.loads(Path(a.scorer_config).read_text(encoding='utf-8'))

    # Load calibration samples
    print(f"Loading calibration samples from {a.samples}...")
    samples = load_samples(a.samples, a.labels)
    print(f"Loaded {len(samples)} calibration samples")

    # Load machine scores
    machine_scores = None
    if a.mode == "calibrated":
        print(f"Loading machine scores from {a.machine_scores}...")
        machine_scores = load_machine_scores(a.machine_scores)
        print(f"Loaded {len(machine_scores)} machine scores")

    # Run calibration
    print(f"Running calibration in {a.mode} mode...")
    calibration_result = run_calibration(samples, machine_scores, scorer_config, a.mode)

    # Load and evaluate blind samples (if provided)
    blind_result = None
    if a.blind and a.blind_labels:
        print(f"Loading blind test samples from {a.blind}...")
        blind_samples = load_blind_samples(a.blind, a.blind_labels)
        print(f"Loaded {len(blind_samples)} blind test samples")

        # Check ID overlap
        cal_ids = [s["article_id"] for s in samples]
        blind_ids = [s["article_id"] for s in blind_samples]
        overlap = check_id_overlap(cal_ids, blind_ids)
        if overlap:
            print(f"ERROR: Article ID overlap between calibration and blind sets: {overlap}")
            sys.exit(1)
        print("ID overlap check: PASSED (no overlap)")

        blind_machine_scores = None
        if a.mode == "calibrated" and a.blind_machine_scores:
            blind_machine_scores = load_machine_scores(a.blind_machine_scores)

        print("Running blind test evaluation...")
        blind_result = run_calibration(blind_samples, blind_machine_scores, scorer_config, a.mode)
        blind_result["note"] = "Blind test results MUST NOT influence rule writing or threshold adjustment."

    # Generate report
    report = {
        "calibration": calibration_result,
        "blind_test": blind_result,
        "target_mae_calibration": 10.0,
        "target_mae_blind": 15.0,
        "ready_for_production": (
            calibration_result.get("metrics", {}).get("mae", float('inf')) <= 10.0 and
            (blind_result is None or blind_result.get("metrics", {}).get("mae", float('inf')) <= 15.0)
        ),
    }

    Path(a.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Calibration report saved to {a.output}")
    print(f"Calibration MAE: {calibration_result['metrics']['mae']}")
    if blind_result:
        print(f"Blind test MAE: {blind_result['metrics']['mae']}")
    print(f"Ready for production: {report['ready_for_production']}")


def load_blind_samples(blind_dir: str, blind_labels_path: str) -> list:
    """Load blind test samples. These MUST NOT participate in rule writing or threshold adjustment."""
    return load_samples(blind_dir, blind_labels_path)


if __name__ == '__main__':
    main()
