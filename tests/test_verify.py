"""Regression checks for the evidence verifier's rejection paths."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
spec = importlib.util.spec_from_file_location("evidence_verify", ROOT / "experiments/verify.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
sys.path.pop(0)


def evidence():
    return tuple(json.loads((ROOT / "results" / name).read_text())
                 for name in ("baseline.json", "strategies.json"))


def test_registered_cases_accepted():
    verify.validate_cases(*evidence())


@pytest.mark.parametrize("which", [0, 1])
@pytest.mark.parametrize("corruption", ["empty", "missing", "duplicate", "unknown"])
def test_incomplete_or_substituted_cases_rejected(which, corruption):
    records = deepcopy(evidence())
    rows = records[which]["results"]
    if corruption == "empty":
        rows.clear()
    elif corruption == "missing":
        rows.pop()
    elif corruption == "duplicate":
        rows[-1] = deepcopy(rows[0])
    else:
        rows[0]["bet"] = "unknown bet"
    with pytest.raises(ValueError, match="distinct registered cases"):
        verify.validate_cases(*records)


def test_validation_remains_enabled_with_python_optimisation():
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "src"),
                                                    str(ROOT / "experiments")]))
    result = subprocess.run([sys.executable, "-O", "-c",
                             "from verify import require; require(False, 'invalid evidence')"],
                            env=env, text=True, capture_output=True)
    assert result.returncode != 0
    assert "ValueError: invalid evidence" in result.stderr


@pytest.mark.parametrize("corruption", [None, "baseline_coverage", "house_edge", "residual", "return"])
def test_selected_inputs_and_hashes(tmp_path, monkeypatch, corruption):
    baseline, strategies = evidence()
    if corruption == "baseline_coverage":
        baseline["results"][0]["covered"] = False
    elif corruption == "house_edge":
        strategies["results"][0]["house_edge"] = 0
    elif corruption == "residual":
        strategies["results"][0]["residual_covers_zero"] = False
    elif corruption == "return":
        strategies["results"][0]["return_covers_benchmark"] = False
    baseline_path = tmp_path / "custom-baseline.json"
    strategies_path = tmp_path / "custom-strategies.json"
    baseline_path.write_text(json.dumps(baseline))
    strategies_path.write_text(json.dumps(strategies))
    output = tmp_path / "verification.json"
    monkeypatch.setattr(sys, "argv", ["verify", "--baseline", str(baseline_path),
                                      "--strategies", str(strategies_path),
                                      "--output", str(output)])
    monkeypatch.setattr(verify.subprocess, "run", lambda *a, **k:
                        subprocess.CompletedProcess(a, 0, "tests passed", ""))
    monkeypatch.setattr(verify, "simulate_wagers", lambda w, b, n, seed:
                        next(r["interval"] for r in baseline["results"] if r["seed"] == seed))
    monkeypatch.setattr(verify, "mean_interval", lambda summary, comparisons: summary)
    monkeypatch.setattr(verify, "simulate_sessions", lambda *args:
                        next(r for r in strategies["results"] if r["seed"] == args[8]))
    metadata_keys = {"wheel", "strategy", "bet", "base", "seed", "house_edge", "elapsed_seconds",
                     "residual_covers_zero", "return_covers_benchmark"}
    monkeypatch.setattr(verify, "evaluate_sessions", lambda row, *args:
                        {k: v for k, v in row.items() if k not in metadata_keys})
    if corruption:
        with pytest.raises(ValueError):
            verify.main()
        assert not output.exists()
        return
    verify.main()
    report = json.loads(output.read_text())
    assert report["evidence_paths"]["baseline.json"] == str(baseline_path)
    assert report["evidence_sha256"]["baseline.json"] == verify.hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    assert report["evidence_sha256"]["strategies.json"] == verify.hashlib.sha256(strategies_path.read_bytes()).hexdigest()
    assert report["baseline_cases_exactly_replayed"] == 8
    assert report["strategy_cases_exactly_replayed"] == 16
