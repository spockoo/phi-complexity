"""
Outils de reporting de couverture pour distinguer noyau produit et modules optionnels.
"""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class SnapshotCouverture:
    total_covered: int
    total_statements: int
    core_covered: int
    core_statements: int
    optional_covered: int
    optional_statements: int

    @property
    def total_ratio(self) -> float:
        if self.total_statements == 0:
            return 0.0
        return self.total_covered / self.total_statements

    @property
    def core_ratio(self) -> float:
        if self.core_statements == 0:
            return 0.0
        return self.core_covered / self.core_statements

    @property
    def optional_ratio(self) -> float:
        if self.optional_statements == 0:
            return 0.0
        return self.optional_covered / self.optional_statements

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": {
                "covered": self.total_covered,
                "statements": self.total_statements,
                "ratio": round(self.total_ratio, 6),
            },
            "core": {
                "covered": self.core_covered,
                "statements": self.core_statements,
                "ratio": round(self.core_ratio, 6),
            },
            "optional": {
                "covered": self.optional_covered,
                "statements": self.optional_statements,
                "ratio": round(self.optional_ratio, 6),
            },
        }


_SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"
_OPTIONAL_SUFFIXES = ("phi_complexity/notebook_helpers.py",)


def _line_stats_from_class_node(class_node: ET.Element) -> tuple[int, int]:
    covered = 0
    statements = 0
    lines_node = class_node.find("lines")
    if lines_node is None:
        return covered, statements
    for line in lines_node.findall("line"):
        statements += 1
        hits = int(line.get("hits", "0"))
        if hits > 0:
            covered += 1
    return covered, statements


def _is_optional_file(filename: str) -> bool:
    normalized = filename.replace("\\", "/")
    return any(normalized.endswith(suffix) for suffix in _OPTIONAL_SUFFIXES)


def calculer_snapshot_couverture(coverage_xml_path: str) -> SnapshotCouverture:
    root = ET.parse(coverage_xml_path).getroot()
    total_covered = 0
    total_statements = 0
    optional_covered = 0
    optional_statements = 0

    for class_node in root.findall(".//class"):
        filename = class_node.get("filename", "")
        covered, statements = _line_stats_from_class_node(class_node)
        total_covered += covered
        total_statements += statements
        if _is_optional_file(filename):
            optional_covered += covered
            optional_statements += statements

    return SnapshotCouverture(
        total_covered=total_covered,
        total_statements=total_statements,
        core_covered=total_covered - optional_covered,
        core_statements=total_statements - optional_statements,
        optional_covered=optional_covered,
        optional_statements=optional_statements,
    )


def charger_historique_couverture(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    entries: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                entries.append(data)
    return entries


def sauvegarder_snapshot_couverture(
    history_path: str,
    snapshot: SnapshotCouverture,
    analyzed_at: str,
    max_entries: int = 200,
) -> List[Dict[str, Any]]:
    history = charger_historique_couverture(history_path)
    history.append({"analyzed_at": analyzed_at, **snapshot.to_dict()})
    trimmed = history[-max_entries:]
    os.makedirs(os.path.dirname(history_path) or ".", exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as fh:
        for entry in trimmed:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return trimmed


def sparkline_couverture_core(history: List[Dict[str, Any]], n: int = 20) -> str:
    if not history:
        return ""
    chars: List[str] = []
    nb_buckets = len(_SPARKLINE_CHARS)
    for entry in history[-n:]:
        ratio = float(entry.get("core", {}).get("ratio", 0.0))
        ratio = max(0.0, min(1.0, ratio))
        idx = min(int(ratio * nb_buckets), nb_buckets - 1)
        chars.append(_SPARKLINE_CHARS[idx])
    return "".join(chars)


def rapport_couverture_markdown(
    snapshot: SnapshotCouverture,
    trend_sparkline: str = "",
) -> str:
    lines = [
        "## 🧪 Couverture — Cœur vs Optionnel",
        "",
        f"- **Couverture globale** : {snapshot.total_ratio * 100:.2f}%",
        f"- **Couverture cœur produit** : {snapshot.core_ratio * 100:.2f}%",
        f"- **Couverture optionnelle notebooks** : {snapshot.optional_ratio * 100:.2f}%",
    ]
    if trend_sparkline:
        lines.extend(["", f"**Tendance hebdo (cœur)** : `{trend_sparkline}`"])
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "SnapshotCouverture",
    "calculer_snapshot_couverture",
    "charger_historique_couverture",
    "sauvegarder_snapshot_couverture",
    "sparkline_couverture_core",
    "rapport_couverture_markdown",
]
