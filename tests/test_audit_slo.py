"""
tests/test_audit_slo.py — Tests du pipeline SLO (Phase 3.2)
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List

import pytest

from phi_complexity.audit_slo import (
    ControlPlaneSnapshot,
    EntreeHistorique,
    MetriqueEfficaciteDev,
    MetriquesSLO,
    calculer_efficacite_dev,
    calculer_mttr,
    calculer_slo,
    calculer_taux_classification,
    calculer_taux_faux_positifs,
    charger_historique,
    construire_control_plane_snapshot,
    estimer_efficacite_dev_depuis_historique,
    exporter_control_plane_snapshot_json,
    rapport_control_plane_markdown,
    rapport_slo_markdown,
    sparkline_resonance,
)


def _make_entree(
    analyzed_at: str,
    run_id: int,
    conclusion: str,
    score: float,
    diagnostics: List[Dict[str, Any]] | None = None,
) -> EntreeHistorique:
    return EntreeHistorique(
        analyzed_at=analyzed_at,
        run_id=run_id,
        run_conclusion=conclusion,
        ci_resonance_score=score,
        diagnostics=diagnostics or [],
    )


def _write_jsonl(entries: List[Dict[str, Any]]) -> str:
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry) + "\n")
    except Exception:
        os.close(fd)
        raise
    return path


class TestChargerHistorique:
    def test_loads_valid_jsonl(self) -> None:
        data = [
            {
                "analyzed_at": "2024-01-01T00:00:00Z",
                "run_id": 1,
                "run_conclusion": "success",
                "ci_resonance": {"score": 0.9},
                "diagnostics": [],
            }
        ]
        path = _write_jsonl(data)
        try:
            entrees = charger_historique(path)
            assert len(entrees) == 1
            assert entrees[0].run_id == 1
            assert entrees[0].ci_resonance_score == pytest.approx(0.9)
        finally:
            os.unlink(path)

    def test_ignores_malformed_lines(self) -> None:
        fd, path = tempfile.mkstemp(suffix=".jsonl", dir=os.getcwd())
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write("not valid json\n")
                fh.write(
                    json.dumps(
                        {
                            "analyzed_at": "2024-01-02T00:00:00Z",
                            "run_id": 2,
                            "run_conclusion": "failure",
                            "ci_resonance": {"score": 0.3},
                            "diagnostics": [],
                        }
                    )
                    + "\n"
                )
            entrees = charger_historique(path)
            assert len(entrees) == 1
            assert entrees[0].run_id == 2
        finally:
            os.unlink(path)

    def test_returns_empty_for_nonexistent_file(self) -> None:
        entrees = charger_historique("/nonexistent/path/to/ci-history.jsonl")
        assert entrees == []

    def test_empty_file(self) -> None:
        fd, path = tempfile.mkstemp(suffix=".jsonl", dir=os.getcwd())
        os.close(fd)
        try:
            entrees = charger_historique(path)
            assert entrees == []
        finally:
            os.unlink(path)


class TestCalculerMttr:
    def test_basic_failure_success_pair(self) -> None:
        historique = [
            _make_entree("2024-01-01T00:00:00", 1, "failure", 0.3),
            _make_entree("2024-01-01T02:00:00", 2, "success", 0.9),
            _make_entree("2024-01-02T00:00:00", 3, "failure", 0.2),
            _make_entree("2024-01-02T04:00:00", 4, "success", 0.85),
        ]
        mttr = calculer_mttr(historique)
        assert mttr is not None
        assert mttr == pytest.approx(10800.0)

    def test_returns_none_for_single_pair(self) -> None:
        historique = [
            _make_entree("2024-01-01T00:00:00", 1, "failure", 0.3),
            _make_entree("2024-01-01T02:00:00", 2, "success", 0.9),
        ]
        mttr = calculer_mttr(historique)
        assert mttr is None

    def test_returns_none_for_empty(self) -> None:
        assert calculer_mttr([]) is None

    def test_returns_none_for_no_failure_success_pairs(self) -> None:
        historique = [
            _make_entree("2024-01-01T00:00:00", 1, "success", 0.9),
            _make_entree("2024-01-02T00:00:00", 2, "success", 0.85),
        ]
        assert calculer_mttr(historique) is None

    def test_multiple_pairs_averaged(self) -> None:
        historique = [
            _make_entree("2024-01-01T00:00:00", 1, "failure", 0.2),
            _make_entree("2024-01-01T01:00:00", 2, "success", 0.9),
            _make_entree("2024-01-02T00:00:00", 3, "failure", 0.2),
            _make_entree("2024-01-02T03:00:00", 4, "success", 0.8),
            _make_entree("2024-01-03T00:00:00", 5, "failure", 0.2),
            _make_entree("2024-01-03T05:00:00", 6, "success", 0.9),
        ]
        mttr = calculer_mttr(historique)
        assert mttr is not None
        assert mttr == pytest.approx(10800.0)


class TestCalculerTauxClassification:
    def test_all_classified(self) -> None:
        historique = [
            _make_entree(
                "2024-01-01T00:00:00",
                1,
                "failure",
                0.3,
                [{"category": "QUALITY_GATE"}, {"category": "TEST_REGRESSION"}],
            )
        ]
        assert calculer_taux_classification(historique) == pytest.approx(1.0)

    def test_all_unclassified(self) -> None:
        historique = [
            _make_entree(
                "2024-01-01T00:00:00",
                1,
                "failure",
                0.3,
                [{"category": "UNCLASSIFIED"}],
            )
        ]
        assert calculer_taux_classification(historique) == pytest.approx(0.0)

    def test_mixed(self) -> None:
        historique = [
            _make_entree(
                "2024-01-01T00:00:00",
                1,
                "failure",
                0.3,
                [{"category": "QUALITY_GATE"}, {"category": "UNCLASSIFIED"}],
            )
        ]
        assert calculer_taux_classification(historique) == pytest.approx(0.5)

    def test_empty_history_returns_one(self) -> None:
        assert calculer_taux_classification([]) == pytest.approx(1.0)

    def test_no_diagnostics(self) -> None:
        historique = [_make_entree("2024-01-01T00:00:00", 1, "success", 0.9)]
        assert calculer_taux_classification(historique) == pytest.approx(1.0)


class TestCalculerTauxFauxPositifs:
    def test_no_false_positives(self) -> None:
        historique = [
            _make_entree(
                "2024-01-01T00:00:00",
                1,
                "failure",
                0.3,
                [{"category": "QUALITY_GATE"}],
            )
        ]
        assert calculer_taux_faux_positifs(historique) == pytest.approx(0.0)

    def test_all_false_positives(self) -> None:
        historique = [
            _make_entree(
                "2024-01-01T00:00:00",
                1,
                "failure",
                0.3,
                [{"category": "OPERATIONAL_FALSE_POSITIVE"}],
            )
        ]
        assert calculer_taux_faux_positifs(historique) == pytest.approx(1.0)

    def test_mixed(self) -> None:
        historique = [
            _make_entree(
                "2024-01-01T00:00:00",
                1,
                "failure",
                0.3,
                [
                    {"category": "OPERATIONAL_FALSE_POSITIVE"},
                    {"category": "QUALITY_GATE"},
                    {"category": "OPERATIONAL_FALSE_POSITIVE"},
                    {"category": "TEST_REGRESSION"},
                ],
            )
        ]
        assert calculer_taux_faux_positifs(historique) == pytest.approx(0.5)

    def test_empty_history(self) -> None:
        assert calculer_taux_faux_positifs([]) == pytest.approx(0.0)


class TestSparklineResonance:
    def test_empty_history_returns_empty_string(self) -> None:
        assert sparkline_resonance([]) == ""

    def test_length_matches_history_up_to_n(self) -> None:
        historique = [
            _make_entree(f"2024-01-{i+1:02d}T00:00:00", i, "success", float(i) / 10)
            for i in range(10)
        ]
        spark = sparkline_resonance(historique, n=50)
        assert len(spark) == 10

    def test_capped_at_n(self) -> None:
        historique = [
            _make_entree(f"2024-01-01T{i:02d}:00:00", i, "success", 0.5)
            for i in range(20)
        ]
        spark = sparkline_resonance(historique, n=5)
        assert len(spark) == 5

    def test_uses_only_sparkline_chars(self) -> None:
        valid_chars = set("▁▂▃▄▅▆▇█")
        historique = [
            _make_entree(f"2024-01-{i+1:02d}T00:00:00", i, "success", float(i) / 9)
            for i in range(10)
        ]
        spark = sparkline_resonance(historique)
        assert all(c in valid_chars for c in spark)

    def test_high_score_maps_to_high_char(self) -> None:
        historique = [_make_entree("2024-01-01T00:00:00", 1, "success", 1.0)]
        spark = sparkline_resonance(historique)
        assert spark == "█"

    def test_zero_score_maps_to_low_char(self) -> None:
        historique = [_make_entree("2024-01-01T00:00:00", 1, "failure", 0.0)]
        spark = sparkline_resonance(historique)
        assert spark == "▁"


class TestCalculerSlo:
    def test_returns_metriques_slo(self) -> None:
        data = [
            {
                "analyzed_at": "2024-01-01T00:00:00Z",
                "run_id": 1,
                "run_conclusion": "success",
                "ci_resonance": {"score": 0.9},
                "diagnostics": [{"category": "QUALITY_GATE"}],
            }
        ]
        path = _write_jsonl(data)
        try:
            slo = calculer_slo(path)
            assert isinstance(slo, MetriquesSLO)
            assert slo.nb_runs_analyses == 1
        finally:
            os.unlink(path)

    def test_empty_file_gives_defaults(self) -> None:
        fd, path = tempfile.mkstemp(suffix=".jsonl", dir=os.getcwd())
        os.close(fd)
        try:
            slo = calculer_slo(path)
            assert slo.nb_runs_analyses == 0
            assert slo.mttr_secondes is None
        finally:
            os.unlink(path)

    def test_nonexistent_file(self) -> None:
        slo = calculer_slo("/nonexistent/path.jsonl")
        assert slo.nb_runs_analyses == 0

    def test_recommandation_upgrade_false_by_default(self) -> None:
        slo = calculer_slo("/nonexistent/path.jsonl")
        assert slo.recommandation_upgrade is False


class TestRapportSloMarkdown:
    def test_contains_header(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=3600.0,
            taux_classification=0.95,
            taux_faux_positifs=0.02,
            nb_runs_analyses=42,
            nb_runs_consecutifs_bons=5,
            recommandation_upgrade=False,
        )
        rapport = rapport_slo_markdown(slo)
        assert "## 📊 Rapport SLO" in rapport

    def test_contains_dev_efficiency_section_when_provided(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=3600.0,
            taux_classification=0.95,
            taux_faux_positifs=0.02,
            nb_runs_analyses=42,
            nb_runs_consecutifs_bons=5,
            recommandation_upgrade=False,
        )
        efficacite = MetriqueEfficaciteDev(
            score_global=83.2,
            stabilite_ci=0.9,
            qualite_livraison=0.8,
            couverture_utile=0.88,
            complexite_maitrisee=0.75,
            vitesse_correction=0.7,
        )
        rapport = rapport_slo_markdown(slo, efficacite_dev=efficacite)
        assert "Score d'Efficacité Dev" in rapport
        assert "83.2/100" in rapport


class TestEfficaciteDev:
    def test_calculer_efficacite_dev_bounds_score(self) -> None:
        score = calculer_efficacite_dev(
            stabilite_ci=2.0,
            qualite_livraison=-1.0,
            couverture_utile=0.9,
            complexite_maitrisee=0.8,
            vitesse_correction=0.7,
        )
        assert 0.0 <= score.score_global <= 100.0

    def test_estimer_efficacite_depuis_historique(self) -> None:
        historique = [
            _make_entree(
                "2024-01-01T00:00:00",
                1,
                "failure",
                0.4,
                [{"category": "QUALITY_GATE"}],
            ),
            _make_entree(
                "2024-01-01T01:00:00",
                2,
                "success",
                0.9,
                [{"category": "TEST_REGRESSION"}],
            ),
            _make_entree(
                "2024-01-01T02:00:00",
                3,
                "success",
                0.95,
                [{"category": "PERMISSIONS"}],
            ),
        ]
        score = estimer_efficacite_dev_depuis_historique(
            historique, couverture_utile=0.91, complexite_maitrisee=0.8
        )
        assert isinstance(score, MetriqueEfficaciteDev)
        assert 0.0 <= score.score_global <= 100.0
        assert score.couverture_utile == pytest.approx(0.91)

    def test_contains_runs_count(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=None,
            taux_classification=0.80,
            taux_faux_positifs=0.05,
            nb_runs_analyses=10,
            nb_runs_consecutifs_bons=3,
            recommandation_upgrade=False,
        )
        rapport = rapport_slo_markdown(slo)
        assert "10" in rapport

    def test_mttr_none_shows_na(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=None,
            taux_classification=0.90,
            taux_faux_positifs=0.0,
            nb_runs_analyses=5,
            nb_runs_consecutifs_bons=2,
            recommandation_upgrade=False,
        )
        rapport = rapport_slo_markdown(slo)
        assert "N/A" in rapport

    def test_sparkline_included_when_provided(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=7200.0,
            taux_classification=0.92,
            taux_faux_positifs=0.01,
            nb_runs_analyses=20,
            nb_runs_consecutifs_bons=10,
            recommandation_upgrade=True,
        )
        rapport = rapport_slo_markdown(slo, sparkline="▁▂▃▄▅▆▇█")
        assert "▁▂▃▄▅▆▇█" in rapport

    def test_recommandation_upgrade_shown(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=1800.0,
            taux_classification=0.95,
            taux_faux_positifs=0.0,
            nb_runs_analyses=50,
            nb_runs_consecutifs_bons=15,
            recommandation_upgrade=True,
        )
        rapport = rapport_slo_markdown(slo)
        assert "Recommandation" in rapport

    def test_returns_string(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=0.0,
            taux_classification=1.0,
            taux_faux_positifs=0.0,
            nb_runs_analyses=0,
            nb_runs_consecutifs_bons=0,
            recommandation_upgrade=False,
        )
        assert isinstance(rapport_slo_markdown(slo), str)

    def test_classification_ok_emoji(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=3600.0,
            taux_classification=0.95,
            taux_faux_positifs=0.0,
            nb_runs_analyses=10,
            nb_runs_consecutifs_bons=5,
            recommandation_upgrade=False,
        )
        rapport = rapport_slo_markdown(slo)
        assert "✅" in rapport

    def test_classification_fail_emoji(self) -> None:
        slo = MetriquesSLO(
            mttr_secondes=3600.0,
            taux_classification=0.50,
            taux_faux_positifs=0.0,
            nb_runs_analyses=10,
            nb_runs_consecutifs_bons=0,
            recommandation_upgrade=False,
        )
        rapport = rapport_slo_markdown(slo)
        assert "❌" in rapport


class TestControlPlaneSnapshot:
    def test_construire_control_plane_snapshot(self) -> None:
        historique = [
            _make_entree(
                "2024-01-01T00:00:00",
                1,
                "failure",
                0.2,
                [
                    {"category": "RUNNER_QUEUE_STALL"},
                    {"category": "WORKFLOW_CONCURRENCY_CANCELLED"},
                ],
            ),
            _make_entree(
                "2024-01-01T03:00:00",
                2,
                "success",
                0.9,
                [{"category": "QUALITY_GATE"}],
            ),
            _make_entree(
                "2024-01-01T04:00:00",
                3,
                "cancelled",
                0.4,
                [{"category": "WORKFLOW_CONCURRENCY_CANCELLED"}],
            ),
        ]
        snapshot = construire_control_plane_snapshot(historique, trend_window=10)
        assert isinstance(snapshot, ControlPlaneSnapshot)
        assert snapshot.total_runs == 3
        assert snapshot.success_runs == 1
        assert snapshot.failure_runs == 1
        assert snapshot.cancelled_runs == 1
        assert snapshot.success_rate == pytest.approx(1 / 3)
        assert snapshot.runner_pressure_rate > 0.0
        assert snapshot.flow_cancellation_rate > 0.0
        assert len(snapshot.top_root_causes) > 0

    def test_exporter_control_plane_snapshot_json(self) -> None:
        snapshot = ControlPlaneSnapshot(
            total_runs=2,
            success_runs=1,
            failure_runs=1,
            cancelled_runs=0,
            success_rate=0.5,
            mttr_secondes=3600.0,
            top_root_causes=[{"category": "QUALITY_GATE", "occurrences": 1}],
            ci_resonance_trend="▁█",
            runner_pressure_rate=0.0,
            flow_cancellation_rate=0.0,
        )
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            exporter_control_plane_snapshot_json(snapshot, path)
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
            assert payload["total_runs"] == 2
            assert payload["success_rate"] == pytest.approx(0.5)
            assert payload["ci_resonance_trend"] == "▁█"
        finally:
            os.unlink(path)

    def test_rapport_control_plane_markdown(self) -> None:
        snapshot = ControlPlaneSnapshot(
            total_runs=5,
            success_runs=4,
            failure_runs=1,
            cancelled_runs=0,
            success_rate=0.8,
            mttr_secondes=None,
            top_root_causes=[{"category": "TEST_REGRESSION", "occurrences": 2}],
            ci_resonance_trend="▁▂▃▄",
            runner_pressure_rate=0.1,
            flow_cancellation_rate=0.2,
        )
        rapport = rapport_control_plane_markdown(snapshot)
        assert "Ops & Engineering Control Plane" in rapport
        assert "TEST_REGRESSION" in rapport
        assert "▁▂▃▄" in rapport
