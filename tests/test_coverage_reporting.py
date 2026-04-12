from __future__ import annotations

import json
from pathlib import Path

from phi_complexity.coverage_reporting import (
    calculer_snapshot_couverture,
    charger_historique_couverture,
    rapport_couverture_markdown,
    sauvegarder_snapshot_couverture,
    sparkline_couverture_core,
)


def _write_coverage_xml(path: Path) -> None:
    path.write_text(
        """<?xml version="1.0" ?>
<coverage>
  <packages>
    <package name="phi_complexity">
      <classes>
        <class filename="phi_complexity/cli.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="0"/>
            <line number="3" hits="1"/>
          </lines>
        </class>
        <class filename="phi_complexity/notebook_helpers.py">
          <lines>
            <line number="1" hits="0"/>
            <line number="2" hits="0"/>
            <line number="3" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )


def test_snapshot_separe_core_et_optionnel(tmp_path: Path) -> None:
    xml_path = tmp_path / "coverage.xml"
    _write_coverage_xml(xml_path)
    snapshot = calculer_snapshot_couverture(str(xml_path))
    assert snapshot.total_statements == 6
    assert snapshot.total_covered == 3
    assert snapshot.core_statements == 3
    assert snapshot.core_covered == 2
    assert snapshot.optional_statements == 3
    assert snapshot.optional_covered == 1


def test_sauvegarde_et_charge_historique(tmp_path: Path) -> None:
    xml_path = tmp_path / "coverage.xml"
    _write_coverage_xml(xml_path)
    history_path = tmp_path / "coverage-history.jsonl"
    snapshot = calculer_snapshot_couverture(str(xml_path))
    history = sauvegarder_snapshot_couverture(
        str(history_path),
        snapshot,
        analyzed_at="2026-04-12T00:00:00Z",
    )
    assert len(history) == 1
    loaded = charger_historique_couverture(str(history_path))
    assert len(loaded) == 1
    assert loaded[0]["core"]["ratio"] == snapshot.to_dict()["core"]["ratio"]


def test_sparkline_core(tmp_path: Path) -> None:
    history_path = tmp_path / "coverage-history.jsonl"
    entries = [
        {"analyzed_at": "2026-01-01T00:00:00Z", "core": {"ratio": 0.40}},
        {"analyzed_at": "2026-01-08T00:00:00Z", "core": {"ratio": 0.60}},
        {"analyzed_at": "2026-01-15T00:00:00Z", "core": {"ratio": 0.90}},
    ]
    history_path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    history = charger_historique_couverture(str(history_path))
    spark = sparkline_couverture_core(history, n=10)
    assert len(spark) == 3


def test_rapport_couverture_markdown(tmp_path: Path) -> None:
    xml_path = tmp_path / "coverage.xml"
    _write_coverage_xml(xml_path)
    snapshot = calculer_snapshot_couverture(str(xml_path))
    report = rapport_couverture_markdown(snapshot, trend_sparkline="▁▅█")
    assert "Couverture — Cœur vs Optionnel" in report
    assert "Tendance hebdo (cœur)" in report
