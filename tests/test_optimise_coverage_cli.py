"""Bounded CLI checks for optimisation parameters and evidence preservation."""
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys

import pytest
import sympy as sp

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "experiments"))
    spec = importlib.util.spec_from_file_location("optimise_coverage_cli", ROOT / "experiments/optimise_coverage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class MockResult:
    status: str = "limit"
    analysis: dict | None = None
    solver_dual_bound: float | None = -5.0
    solver_gap: float | None = None


def test_cli_passes_fixed_budget_exact_thresholds_and_selected_families(cli, monkeypatch, tmp_path):
    calls = []
    def solve(**kwargs):
        calls.append(kwargs)
        return MockResult(analysis={"expected_profit": sp.Rational(-20, 37),
                                    "distribution": {sp.Integer(-20): sp.Rational(7, 37)}})
    monkeypatch.setattr(cli, "optimise_coverage", solve)
    output = tmp_path / "result.json"
    monkeypatch.setattr(sys, "argv", ["optimise_coverage", "--families", "six_line", "six_line",
                                     "--output", str(output)])
    cli.main()
    assert [call["target_profitable"] for call in calls] == [26, 28, 30, 32, 34]
    assert all(call["budget"] == 20 and call["max_bets"] == 10 and call["time_limit"] == 10 for call in calls)
    assert all(len(call["catalogue"]) == 11 for call in calls)
    report = json.loads(output.read_text())
    assert report["families"] == ["six_line"]
    assert report["metadata"]["rng"] is None
    assert report["metadata"]["code_sha256"]
    assert report["results"][0]["status"] == "limit"
    assert report["results"][0]["analysis"]["expected_profit"] == "-20/37"
    assert report["results"][0]["analysis"]["distribution"] == {"-20": "7/37"}


def test_cli_preserves_existing_evidence_before_solving(cli, monkeypatch, tmp_path):
    output = tmp_path / "result.json"
    output.write_text("original evidence")
    monkeypatch.setattr(sys, "argv", ["optimise_coverage", "--output", str(output)])
    monkeypatch.setattr(cli, "optimise_coverage", lambda **kwargs: pytest.fail("solver must not run"))
    with pytest.raises(FileExistsError):
        cli.main()
    assert output.read_text() == "original evidence"


@pytest.mark.parametrize("args", [["--chip-budget", "0"], ["--chip-budget", "1000001"], ["--max-bets", "-1"], ["--max-bets", "11"],
                                    ["--targets", "0"], ["--targets", "101"],
                                    ["--time-limit", "nan"], ["--time-limit", "inf"],
                                    ["--time-limit", "0"], ["--time-limit", "3601"]])
def test_cli_rejects_invalid_arguments_without_solving(cli, monkeypatch, tmp_path, args):
    output = tmp_path / "result.json"
    monkeypatch.setattr(sys, "argv", ["optimise_coverage", "--output", str(output), *args])
    monkeypatch.setattr(cli, "optimise_coverage", lambda **kwargs: pytest.fail("solver must not run"))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    assert not output.exists()


def test_cli_exclusive_creation_handles_output_race(cli, monkeypatch, tmp_path):
    output = tmp_path / "result.json"
    def solve(**kwargs):
        output.write_text("concurrent evidence")
        return MockResult()
    monkeypatch.setattr(cli, "optimise_coverage", solve)
    monkeypatch.setattr(sys, "argv", ["optimise_coverage", "--targets", "70", "--output", str(output)])
    with pytest.raises(FileExistsError):
        cli.main()
    assert output.read_text() == "concurrent evidence"


def test_real_solver_cli_on_one_legal_bet(cli, monkeypatch, tmp_path):
    from roulette.rules import straight
    monkeypatch.setattr(cli, "european_catalogue", lambda: {"straight": (straight(0),)})
    output = tmp_path / "result.json"
    monkeypatch.setattr(sys, "argv", ["optimise_coverage", "--chip-budget", "1", "--max-bets", "1",
                                     "--targets", "1", "--time-limit", "2", "--output", str(output)])
    cli.main()
    row = json.loads(output.read_text())["results"][0]
    assert row["status"] == "optimal"
    assert row["analysis"]["profitable_count"] == 1
    assert row["analysis"]["expected_profit"] == "-1/37"
    assert row["stakes"] == [1]
    assert row["optimality_evidence"] == "analytical_bound_attained"
    assert row["elapsed_seconds"] >= 0
