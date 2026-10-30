"""Shape checks: results/ holds raw `wp-bench run` outputs and the page data is current."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
DATA_FILE = ROOT / "site" / "data" / "leaderboard.json"
RUN_FILE = re.compile(r"^results_\d{8}_\d{6}\.jsonl?$")
SCORE_KEYS = {
    "correctness",
    "execution_pass_rate",
    "runtime",
    "static_policy_pass_rate",
    "overall",
}


def run_files() -> list[Path]:
    return sorted(RESULTS_DIR.glob("results_*.json"))


def baseline_models(payload: dict) -> dict[str, float]:
    """model id -> overall score for every leaderboard-eligible model in a payload."""
    if "results" in payload:
        return {
            payload["metadata"]["model"]["name"]: payload["metadata"]["scores"][
                "overall"
            ]
        }
    return {
        e["config"]["name"]: e["scores"]["overall"]
        for e in payload["models"].values()
        if (e.get("variant") or {}).get("kind", "none") == "none"
    }


def test_folder_only_holds_run_outputs() -> None:
    assert run_files(), f"no results_<timestamp>.json files in {RESULTS_DIR}"
    stray = sorted(p.name for p in RESULTS_DIR.iterdir() if not RUN_FILE.match(p.name))
    assert not stray, f"only wp-bench run outputs belong in results/: {stray}"


def _check_scores(scores: dict, label: str) -> None:
    assert SCORE_KEYS <= set(scores), f"{label} is missing score keys"
    for key, value in scores.items():
        if value is not None:
            assert 0.0 <= value <= 1.0, (
                f"{label} scores.{key}={value} is not a 0-1 fraction"
            )
    assert scores["overall"] is not None, f"{label} has no overall score"


@pytest.mark.parametrize("path", run_files(), ids=lambda p: p.name)
def test_run_output_shape(path: Path) -> None:
    payload = json.loads(path.read_text())
    metadata = payload["metadata"]
    assert metadata.get("suite"), f"{path.name}: run has no suite"
    assert metadata.get("scoring_version"), f"{path.name}: run has no scoring_version"
    assert not (metadata.get("synthetic") or metadata.get("generator")), (
        f"{path.name}: synthetic data belongs in examples/, not results/"
    )

    if "results" in payload:  # single-model run
        assert metadata["mode"] == "model", (
            f"{path.name}: reference runs are not entries"
        )
        model = metadata["model"]["name"]
        _check_scores(metadata["scores"], path.name)
        assert payload["results"], f"{path.name}: run has no test records"
        for record in payload["results"]:
            assert record["model"]["name"] == model, (
                f"{path.name}: record for another model"
            )
    else:  # multi-model run
        assert payload["models"], f"{path.name}: multi-model run lists no models"
        for name, entry in payload["models"].items():
            _check_scores(entry["scores"], f"{path.name} models[{name}]")
            assert entry["results"], f"{path.name}: {name} has no test records"

    jsonl = path.with_suffix(".jsonl")
    if jsonl.exists():
        lines = [line for line in jsonl.read_text().splitlines() if line.strip()]
        records = (
            payload["results"]
            if "results" in payload
            else [r for entry in payload["models"].values() for r in entry["results"]]
        )
        assert len(lines) == len(records), f"{jsonl.name} does not match {path.name}"


def test_site_data_matches_results_folder() -> None:
    """The page's prebuilt data must describe exactly the runs in results/."""
    assert DATA_FILE.exists(), (
        "run `python3 site/build_data.py` and commit the data file"
    )
    data = json.loads(DATA_FILE.read_text())
    assert data.get("results_dir") == "results", "data was built from another folder"
    runs = data["runs"]
    assert {r["file"] for r in runs} == {p.name for p in run_files()}, (
        "site/data/leaderboard.json is stale: rerun `python3 site/build_data.py`"
    )
    by_file: dict[str, dict[str, float]] = {}
    for r in runs:
        by_file.setdefault(r["file"], {})[r["model"]] = r["scores"]["overall"]
    for path in run_files():
        expected = baseline_models(json.loads(path.read_text()))
        assert by_file[path.name] == expected, (
            f"{path.name}: data file scores differ from the run"
        )
