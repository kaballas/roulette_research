"""Saved evidence is independently checked before a candidate frontier is built."""

from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from roulette.coverage import analyse
from roulette.rules import RED


@pytest.fixture
def frontier_cli(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "experiments"))
    spec = importlib.util.spec_from_file_location(
        "coverage_frontier_cli", root / "experiments/coverage_frontier.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def saved_row(module):
    return module._json_exact(
        {"bets": [asdict(RED)], "stakes": [20], "analysis": asdict(analyse([RED], [20]))}
    )


def test_frontier_load_rejects_tampered_pocket(frontier_cli, tmp_path):
    row = saved_row(frontier_cli)
    row["analysis"]["profits"][0] = "20"
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps({"results": [row]}))
    with pytest.raises(ValueError, match="independent settlement"):
        frontier_cli.load_candidates([path])


def test_frontier_records_exact_conditional_risk(frontier_cli, monkeypatch, tmp_path):
    source, output = tmp_path / "input.json", tmp_path / "output.json"
    source.write_text(json.dumps({"results": [saved_row(frontier_cli)]}))
    monkeypatch.setattr(
        sys, "argv", ["frontier", "--inputs", str(source), "--output", str(output)]
    )
    frontier_cli.main()
    report = json.loads(output.read_text())
    assert len(report["frontier"]) == 1
    metrics = next(iter(report["candidates"].values()))["metrics"]
    assert metrics["conditional_positive_mean"] == "20"
    assert metrics["conditional_loss_mean"] == "20"
    assert metrics["expected_shortfall"] == "20"
    with pytest.raises(FileExistsError):
        frontier_cli.main()
