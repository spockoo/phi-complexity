"""
phi_complexity/audit_slo.py — Pipeline SLO (Phase 3.2)

Métriques de service calculées localement sur ci-history.jsonl :
    - MTTR : Mean Time To Recover
    - Taux de classification : % classés vs UNCLASSIFIED
    - Taux de faux positifs : % OPERATIONAL_FALSE_POSITIVE
    - Tendance de résonance : sparkline ASCII sur N derniers runs

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EntreeHistorique:
    """Entrée parsée depuis ci-history.jsonl."""

    analyzed_at: str
    run_id: int
    run_conclusion: str
    ci_resonance_score: float
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MetriquesSLO:
    """Métriques SLO calculées sur l'historique CI."""

    mttr_secondes: Optional[float]
    taux_classification: float
    taux_faux_positifs: float
    nb_runs_analyses: int
    nb_runs_consecutifs_bons: int
    recommandation_upgrade: bool
    objectif_classification: float = 0.90
    objectif_mttr_secondes: float = 86400.0


@dataclass
class MetriqueEfficaciteDev:
    """Score composite d'efficacité développeur (0-100)."""

    score_global: float
    stabilite_ci: float
    qualite_livraison: float
    couverture_utile: float
    complexite_maitrisee: float
    vitesse_correction: float


_SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


def charger_historique(chemin: str) -> List[EntreeHistorique]:
    """
    Charge l'historique CI depuis un fichier JSONL.

    Les lignes malformées sont ignorées silencieusement.
    """
    entrees: List[EntreeHistorique] = []
    try:
        with open(chemin, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                try:
                    resonance = data.get("ci_resonance", {})
                    score = float(resonance.get("score", 0.0))
                    entrees.append(
                        EntreeHistorique(
                            analyzed_at=str(data.get("analyzed_at", "")),
                            run_id=int(data.get("run_id", 0)),
                            run_conclusion=str(data.get("run_conclusion", "")),
                            ci_resonance_score=score,
                            diagnostics=list(data.get("diagnostics", [])),
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    continue
    except OSError:
        pass
    return entrees


def calculer_mttr(historique: List[EntreeHistorique]) -> Optional[float]:
    """
    Calcule le Mean Time To Recover en secondes.

    Paire les transitions failure→success et retourne la moyenne.
    Retourne None si moins de 2 transitions sont disponibles.
    """
    durees: List[float] = []
    failure_time: Optional[datetime] = None

    for entree in historique:
        try:
            ts = datetime.fromisoformat(entree.analyzed_at.replace("Z", "+00:00"))
        except ValueError:
            continue

        if entree.run_conclusion in ("failure", "cancelled"):
            if failure_time is None:
                failure_time = ts
        elif entree.run_conclusion == "success":
            if failure_time is not None:
                delta = (ts - failure_time).total_seconds()
                if delta >= 0:
                    durees.append(delta)
                failure_time = None

    if len(durees) < 2:
        return None
    return sum(durees) / len(durees)


def calculer_taux_classification(historique: List[EntreeHistorique]) -> float:
    """
    Retourne le taux de diagnostics classifiés (hors UNCLASSIFIED).
    """
    total = 0
    classifies = 0
    for entree in historique:
        for diag in entree.diagnostics:
            total += 1
            if diag.get("category", "UNCLASSIFIED") != "UNCLASSIFIED":
                classifies += 1
    if total == 0:
        return 1.0
    return classifies / total


def calculer_taux_faux_positifs(historique: List[EntreeHistorique]) -> float:
    """
    Retourne le taux de diagnostics catégorisés OPERATIONAL_FALSE_POSITIVE.
    """
    total = 0
    faux_positifs = 0
    for entree in historique:
        for diag in entree.diagnostics:
            total += 1
            if diag.get("category") == "OPERATIONAL_FALSE_POSITIVE":
                faux_positifs += 1
    if total == 0:
        return 0.0
    return faux_positifs / total


def sparkline_resonance(historique: List[EntreeHistorique], n: int = 50) -> str:
    """
    Génère une sparkline ASCII des N derniers scores de résonance CI.
    """
    recents = historique[-n:]
    if not recents:
        return ""
    chars: List[str] = []
    nb_buckets = len(_SPARKLINE_CHARS)
    for entree in recents:
        score = max(0.0, min(1.0, entree.ci_resonance_score))
        index = min(int(score * nb_buckets), nb_buckets - 1)
        chars.append(_SPARKLINE_CHARS[index])
    return "".join(chars)


def _compter_runs_consecutifs_bons(historique: List[EntreeHistorique]) -> int:
    """Compte le nombre de runs consécutifs à succès en partant de la fin."""
    count = 0
    for entree in reversed(historique):
        if entree.run_conclusion == "success":
            count += 1
        else:
            break
    return count


def calculer_slo(chemin_historique: str) -> MetriquesSLO:
    """
    Charge l'historique et calcule toutes les métriques SLO.
    """
    historique = charger_historique(chemin_historique)
    mttr = calculer_mttr(historique)
    taux_class = calculer_taux_classification(historique)
    taux_fp = calculer_taux_faux_positifs(historique)
    nb_bons = _compter_runs_consecutifs_bons(historique)
    recommandation = (mttr is not None and mttr < 86400.0 and nb_bons >= 10) or (
        mttr is None and nb_bons >= 10
    )
    return MetriquesSLO(
        mttr_secondes=mttr,
        taux_classification=taux_class,
        taux_faux_positifs=taux_fp,
        nb_runs_analyses=len(historique),
        nb_runs_consecutifs_bons=nb_bons,
        recommandation_upgrade=recommandation,
    )


def calculer_efficacite_dev(
    stabilite_ci: float,
    qualite_livraison: float,
    couverture_utile: float,
    complexite_maitrisee: float,
    vitesse_correction: float,
) -> MetriqueEfficaciteDev:
    """Calcule un score composite d'efficacité développeur."""
    metrics = [
        stabilite_ci,
        qualite_livraison,
        couverture_utile,
        complexite_maitrisee,
        vitesse_correction,
    ]
    clamped = [max(0.0, min(1.0, value)) for value in metrics]
    weights = [0.30, 0.25, 0.20, 0.15, 0.10]
    score = sum(value * weight for value, weight in zip(clamped, weights)) * 100.0
    return MetriqueEfficaciteDev(
        score_global=score,
        stabilite_ci=clamped[0],
        qualite_livraison=clamped[1],
        couverture_utile=clamped[2],
        complexite_maitrisee=clamped[3],
        vitesse_correction=clamped[4],
    )


def estimer_efficacite_dev_depuis_historique(
    historique: List[EntreeHistorique],
    couverture_utile: float,
    complexite_maitrisee: float = 0.80,
) -> MetriqueEfficaciteDev:
    """
    Estime le score développeur à partir de l'historique CI et d'un snapshot couverture.
    """
    if not historique:
        return calculer_efficacite_dev(
            stabilite_ci=1.0,
            qualite_livraison=1.0,
            couverture_utile=couverture_utile,
            complexite_maitrisee=complexite_maitrisee,
            vitesse_correction=1.0,
        )

    nb_success = sum(1 for h in historique if h.run_conclusion == "success")
    stabilite_ci = nb_success / len(historique)

    quality_categories = {"QUALITY_GATE", "TYPE_CHECK", "TEST_REGRESSION"}
    quality_hits = 0
    diag_total = 0
    for entree in historique:
        for diag in entree.diagnostics:
            diag_total += 1
            if diag.get("category") in quality_categories:
                quality_hits += 1
    qualite_livraison = 1.0 if diag_total == 0 else max(0.0, 1.0 - (quality_hits / diag_total))

    mttr = calculer_mttr(historique)
    vitesse_correction = 1.0 if mttr is None else max(0.0, min(1.0, 1.0 - (mttr / 172800.0)))

    return calculer_efficacite_dev(
        stabilite_ci=stabilite_ci,
        qualite_livraison=qualite_livraison,
        couverture_utile=couverture_utile,
        complexite_maitrisee=complexite_maitrisee,
        vitesse_correction=vitesse_correction,
    )


def rapport_slo_markdown(
    slo: MetriquesSLO,
    sparkline: str = "",
    efficacite_dev: Optional[MetriqueEfficaciteDev] = None,
) -> str:
    """
    Génère un rapport Markdown formaté des métriques SLO.
    """
    lines: List[str] = [
        "## 📊 Rapport SLO — Phi Complexity CI",
        "",
        f"- **Runs analysés** : {slo.nb_runs_analyses}",
    ]

    if slo.mttr_secondes is not None:
        mttr_h = slo.mttr_secondes / 3600.0
        slo_ok = "✅" if slo.mttr_secondes < slo.objectif_mttr_secondes else "❌"
        lines.append(
            f"- **MTTR** : {mttr_h:.1f}h {slo_ok} (objectif: < {slo.objectif_mttr_secondes/3600:.0f}h)"
        )
    else:
        lines.append("- **MTTR** : N/A (historique insuffisant)")

    class_pct = slo.taux_classification * 100
    class_ok = "✅" if slo.taux_classification >= slo.objectif_classification else "❌"
    lines.append(
        f"- **Taux de classification** : {class_pct:.1f}% {class_ok}"
        f" (objectif: ≥ {slo.objectif_classification * 100:.0f}%)"
    )

    fp_pct = slo.taux_faux_positifs * 100
    lines.append(f"- **Taux de faux positifs** : {fp_pct:.1f}%")
    lines.append(f"- **Runs consécutifs bons** : {slo.nb_runs_consecutifs_bons}")

    if sparkline:
        lines.extend(["", f"**Tendance résonance** : `{sparkline}`"])

    if slo.recommandation_upgrade:
        lines.extend(
            [
                "",
                "> 🟢 **Recommandation** : Le système est stable."
                " Envisager une montée de seuil de résonance.",
            ]
        )

    if efficacite_dev is not None:
        lines.extend(
            [
                "",
                "### 👩‍💻 Score d'Efficacité Dev",
                f"- **Score global** : {efficacite_dev.score_global:.1f}/100",
                f"- Stabilité CI : {efficacite_dev.stabilite_ci * 100:.1f}%",
                f"- Qualité de livraison : {efficacite_dev.qualite_livraison * 100:.1f}%",
                f"- Couverture utile (cœur) : {efficacite_dev.couverture_utile * 100:.1f}%",
                f"- Complexité maîtrisée : {efficacite_dev.complexite_maitrisee * 100:.1f}%",
                f"- Vitesse de correction : {efficacite_dev.vitesse_correction * 100:.1f}%",
            ]
        )

    lines.append("")
    return "\n".join(lines)


__all__ = [
    "EntreeHistorique",
    "MetriquesSLO",
    "MetriqueEfficaciteDev",
    "charger_historique",
    "calculer_mttr",
    "calculer_taux_classification",
    "calculer_taux_faux_positifs",
    "sparkline_resonance",
    "calculer_slo",
    "calculer_efficacite_dev",
    "estimer_efficacite_dev_depuis_historique",
    "rapport_slo_markdown",
]
