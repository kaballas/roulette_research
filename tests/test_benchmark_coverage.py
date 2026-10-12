"""Bounded benchmark orchestration and incumbent validation checks."""

from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from roulette.coverage import analyse
from roulette.rules import RED, straight

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "experiments"))
    spec = importlib.util.spec_from_file_location(
        "benchmark_coverage_cli", ROOT / "experiments/benchmark_coverage.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "backend_available", lambda backend: True)
    return module


@dataclass
class Result:
    bets: tuple
    stakes: tuple
    analysis: object
    status: str = "feasible"
    solver_gap: float | None = None


def test_invalid_seed_never_reused(cli):
    catalogue = (straight(0), RED)
    assert cli.checked_seed((RED,), (1.5,), "bad", catalogue, 1, 10) is None
    assert cli.checked_seed((straight(1),), (1,), "bad", catalogue, 1, 10) is None
    assert cli.checked_seed((RED,), (2,), "bad", catalogue, 1, 10) is None
    assert cli.checked_seed((RED, RED), (1, 1), "bad", catalogue, 2, 10) is None
    seed = cli.checked_seed((RED,), (1,), "good", catalogue, 1, 10)
    assert cli.best_seed([seed], 18) == seed
    assert cli.best_seed([seed], 19) is None


def test_constructive_seed_verified_exactly(cli):
    catalogue = tuple(
        bet for group in cli.european_catalogue().values() for bet in group
    )
    seeds, hashes = cli.initial_seeds(catalogue, 20, 10, [])
    assert len(seeds) == 1
    assert not hashes
    analysis = analyse(seeds[0].bets, seeds[0].stakes)
    assert analysis.total_stake == 20
    assert analysis.profitable_count == 30
    assert analysis.worst_profit == -20


def test_shared_backend_start_and_cross_target_incumbents(cli, monkeypatch, tmp_path):
    bet = straight(0)
    monkeypatch.setattr(cli, "european_catalogue", lambda: {"straight": (bet,)})
    calls = []

    def solve(**kwargs):
        calls.append(kwargs)
        return Result((bet,), (1,), analyse((bet,), (1,)))

    monkeypatch.setattr(cli, "optimise_coverage", solve)
    output = tmp_path / "benchmark.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "benchmark", "--chip-budget", "1", "--targets", "1", "2",
            "--incumbent-evidence", "--output", str(output),
        ],
    )
    cli.main()
    assert len(calls) == 8
    assert calls[0]["incumbent"] is None
    assert calls[2]["incumbent"] is None
    assert calls[1]["incumbent"] == ((bet,), (1,))
    assert calls[3]["incumbent"] == ((bet,), (1,))
    assert calls[4]["incumbent"] == calls[6]["incumbent"] == ((bet,), (1,))
    assert all(call["time_limit"] == 60 for call in calls)
    report = json.loads(output.read_text())
    assert report["configuration"]["seconds_per_stage"] == 60
    assert report["metadata"]["registration_sha256"]
    assert len(report["results"]) == 4


def test_missing_backend_is_explicit(cli, monkeypatch):
    def unavailable(**kwargs):
        raise ImportError("OR-Tools unavailable")

    monkeypatch.setattr(cli, "optimise_coverage", unavailable)
    row, seed = cli.run_stage("cpsat", "optimise", None, (RED,), 1, 18, 1, 60)
    assert row["status"] == "unavailable"
    assert row["reason"] == "OR-Tools unavailable"
    assert seed is None


def test_inconsistent_solver_incumbent_is_rejected(cli, monkeypatch):
    monkeypatch.setattr(
        cli,
        "optimise_coverage",
        lambda **kwargs: Result((RED,), (1,), analyse((straight(0),), (1,))),
    )
    with pytest.raises(ValueError, match="independent exact settlement"):
        cli.run_stage("highs", "feasibility", None, (RED,), 1, 18, 1, 60)


def test_existing_output_preserved_before_solver(cli, monkeypatch, tmp_path):
    output = tmp_path / "benchmark.json"
    output.write_text("existing evidence")
    monkeypatch.setattr(sys, "argv", ["benchmark", "--output", str(output)])
    monkeypatch.setattr(
        cli, "optimise_coverage", lambda **kwargs: pytest.fail("solver must not run")
    )
    with pytest.raises(FileExistsError):
        cli.main()
    assert output.read_text() == "existing evidence"


def test_unregistered_time_tier_rejected(cli, monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys, "argv", ["benchmark", "--seconds", "61", "--output", str(tmp_path / "x")]
    )
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2


def test_real_feasibility_stage_with_verified_seed(cli):
    seed = cli.checked_seed((RED,), (1,), "test", (RED,), 1, 1)
    row, verified = cli.run_stage("highs", "feasibility", seed, (RED,), 1, 18, 1, 60)
    assert row["status"] == "feasible"
    assert verified is not None
    assert verified.stakes == (1,)


def test_absent_backend_is_not_counted_as_a_solver_run(cli, monkeypatch):
    monkeypatch.setattr(cli, "backend_available", lambda backend: False)
    monkeypatch.setattr(
        cli, "optimise_coverage", lambda **kwargs: pytest.fail("absent backend ran")
    )
    row, seed = cli.run_stage("cpsat", "optimise", None, (RED,), 1, 18, 1, 60)
    assert row["status"] == "unavailable"
    assert seed is None
