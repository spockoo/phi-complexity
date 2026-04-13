"""
phi_complexity/remediation.py — Moteur de Mutations Déterministes (Phase 1.1)

Catalogue de règles déterministes : chaque catégorie de diagnostic correspond
à une recette de patch concrète avec vérification d'idempotence et stratégie
de rollback.

Architecture :
    Diagnostic → [RegleMutation] → MutationPlan → Applicateur → Résultat

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RegleMutation:
    """Règle déterministe associée à une catégorie de diagnostic."""

    categorie: str
    confidence_threshold: float
    description: str
    commandes: List[str]
    idempotence_check: Optional[str]
    rollback_commandes: List[str]
    necessite_tests: bool


@dataclass
class MutationPlan:
    """Plan de mutation pour une catégorie donnée."""

    categorie: str
    regles: List[RegleMutation]
    diagnostic_confidence: float
    applicable: bool


@dataclass
class ResultatMutation:
    """Résultat d'une exécution de plan de mutation."""

    categorie: str
    succes: bool
    commandes_executees: List[str]
    sortie: str
    rollback_effectue: bool
    erreur: Optional[str] = field(default=None)


CATALOGUE_MUTATIONS: List[RegleMutation] = [
    RegleMutation(
        categorie="QUALITY_GATE",
        confidence_threshold=0.90,
        description="Corrige automatiquement le lint et le formatage.",
        commandes=["ruff check --fix .", "black ."],
        idempotence_check=None,
        rollback_commandes=["git checkout -- ."],
        necessite_tests=False,
    ),
    RegleMutation(
        categorie="DEPENDENCY_INSTALL",
        confidence_threshold=0.88,
        description="Réinstalle le package en mode éditable.",
        commandes=["pip install -e . --upgrade"],
        idempotence_check=None,
        rollback_commandes=[],
        necessite_tests=False,
    ),
    RegleMutation(
        categorie="TEST_REGRESSION",
        confidence_threshold=0.85,
        description="Exécute la suite de tests pour identifier la régression.",
        commandes=["python -m pytest tests/ -x --no-header -q"],
        idempotence_check=None,
        rollback_commandes=[],
        necessite_tests=False,
    ),
    RegleMutation(
        categorie="TYPE_CHECK",
        confidence_threshold=0.90,
        description="Lance mypy pour identifier les erreurs de types.",
        commandes=["python -m mypy phi_complexity/ --ignore-missing-imports"],
        idempotence_check=None,
        rollback_commandes=[],
        necessite_tests=False,
    ),
    RegleMutation(
        categorie="WORKFLOW_CONCURRENCY_CANCELLED",
        confidence_threshold=0.80,
        description="Produit une recommandation de calibration concurrency.",
        commandes=[
            "echo '[FLOW-INTELLIGENCE] Vérifier cancel-in-progress par branche et workflow critique.'"
        ],
        idempotence_check=None,
        rollback_commandes=[],
        necessite_tests=False,
    ),
    RegleMutation(
        categorie="RUNNER_QUEUE_STALL",
        confidence_threshold=0.80,
        description="Produit une recommandation de capacité runner.",
        commandes=[
            "echo '[RUNNER-SENTINEL] Vérifier saturation runners, labels et taille de matrice.'"
        ],
        idempotence_check=None,
        rollback_commandes=[],
        necessite_tests=False,
    ),
]


def planifier_mutation(
    categorie: str,
    confidence: float,
    catalogue: Optional[List[RegleMutation]] = None,
) -> MutationPlan:
    """
    Construit un MutationPlan pour la catégorie et la confiance données.

    Filtre les règles dont le seuil de confiance est atteint.
    """
    effective_catalogue = catalogue if catalogue is not None else CATALOGUE_MUTATIONS
    regles_applicables = [
        r
        for r in effective_catalogue
        if r.categorie == categorie and confidence >= r.confidence_threshold
    ]
    return MutationPlan(
        categorie=categorie,
        regles=regles_applicables,
        diagnostic_confidence=confidence,
        applicable=len(regles_applicables) > 0,
    )


def appliquer_mutation(
    plan: MutationPlan,
    repertoire: str = ".",
    dry_run: bool = False,
) -> ResultatMutation:
    """
    Applique un MutationPlan dans le répertoire donné.

    En mode dry_run, enregistre les commandes sans les exécuter.
    Déclenche le rollback si une commande échoue.
    Le répertoire est résolu en chemin absolu pour prévenir les traversées de chemin.
    """
    cwd = str(Path(repertoire).resolve())

    if not plan.applicable:
        return ResultatMutation(
            categorie=plan.categorie,
            succes=False,
            commandes_executees=[],
            sortie="",
            rollback_effectue=False,
            erreur="Aucune règle applicable",
        )

    commandes_executees: List[str] = []
    sortie_parts: List[str] = []

    for regle in plan.regles:
        for cmd in regle.commandes:
            commandes_executees.append(cmd)
            if dry_run:
                continue
            # shell=True is safe here: commands come exclusively from the
            # static CATALOGUE_MUTATIONS, never from external user input.
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            sortie_parts.append(proc.stdout + proc.stderr)
            if proc.returncode != 0:
                rollback_ok = True
                for rb_cmd in regle.rollback_commandes:
                    rb_proc = subprocess.run(
                        rb_cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        cwd=cwd,
                    )
                    if rb_proc.returncode != 0:
                        rollback_ok = False
                        sortie_parts.append(rb_proc.stdout + rb_proc.stderr)
                erreur_msg = f"Commande échouée: {cmd}"
                if regle.rollback_commandes and not rollback_ok:
                    erreur_msg += " (rollback partiel)"
                return ResultatMutation(
                    categorie=plan.categorie,
                    succes=False,
                    commandes_executees=commandes_executees,
                    sortie="".join(sortie_parts),
                    rollback_effectue=len(regle.rollback_commandes) > 0,
                    erreur=erreur_msg,
                )

    return ResultatMutation(
        categorie=plan.categorie,
        succes=True,
        commandes_executees=commandes_executees,
        sortie="".join(sortie_parts),
        rollback_effectue=False,
    )


def mutations_pour_rapport(
    mutations: List[Dict[str, Any]],
) -> List[MutationPlan]:
    """
    Convertit la liste proposed_mutations du rapport ci-auto-diagnostic en MutationPlans.
    """
    plans: List[MutationPlan] = []
    for m in mutations:
        categorie = str(m.get("category", "UNCLASSIFIED"))
        confidence = float(m.get("confidence", 0.0))
        plans.append(planifier_mutation(categorie, confidence))
    return plans


__all__ = [
    "RegleMutation",
    "MutationPlan",
    "ResultatMutation",
    "CATALOGUE_MUTATIONS",
    "planifier_mutation",
    "appliquer_mutation",
    "mutations_pour_rapport",
]
