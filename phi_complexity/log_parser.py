"""
phi_complexity/log_parser.py — Analyseur de Logs Structuré (Phase 3.1)

Parser qui applique des signatures regex sur les logs bruts pour classifier
les échecs CI avec une confiance calculée sur le nombre de patterns matchés.

Architecture :
    LogEntry → [PatternMatcher] → ClassificationResult

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PatternSignature:
    """Signature regex pour une catégorie d'échec CI."""

    category: str
    patterns: List[str]
    confidence_base: float
    priority: int
    hint: str
    mutation: str


@dataclass
class ClassificationResult:
    """Résultat de classification d'un log CI."""

    category: str
    confidence: float
    priority: int
    hint: str
    mutation: str
    matched_patterns: List[str] = field(default_factory=list)


CATALOGUE_SIGNATURES: List[PatternSignature] = [
    PatternSignature(
        category="INFRA_RUNNER_UNAVAILABLE",
        patterns=[
            r"runner.*not found",
            r"no.*runner.*available",
            r"queued.*timeout",
            r"unable to find.*runner",
        ],
        confidence_base=0.75,
        priority=1,
        hint="Label runner indisponible/non supporté.",
        mutation="Réduire la matrice au couple os/version supporté puis réactiver graduellement.",
    ),
    PatternSignature(
        category="TOOLCHAIN_SETUP",
        patterns=[
            r"error.*setup.*python",
            r"setup-python.*failed",
            r"python.*version.*not found",
            r"node.*version.*not found",
            r"version.*not.*available",
        ],
        confidence_base=0.72,
        priority=1,
        hint="Échec setup toolchain/version.",
        mutation="Épingler la version de runtime et désactiver temporairement le cache pour isoler.",
    ),
    PatternSignature(
        category="DEPENDENCY_INSTALL",
        patterns=[
            r"pip install.*failed",
            r"could not find.*version",
            r"no matching distribution",
            r"packagenotfounderror",
            r"error.*requirements",
            r"modulenotfounderror",
            r"importerror",
        ],
        confidence_base=0.72,
        priority=1,
        hint="Échec installation dépendances.",
        mutation="Régénérer le verrouillage de dépendances et ajouter retry exponentiel sur install.",
    ),
    PatternSignature(
        category="CHECKOUT_REF_NOT_FOUND",
        patterns=[
            r"(?i)a branch or tag with the name .* could not be found",
            r"fatal: couldn't find remote ref",
            r"fatal: reference is not a tree",
            r"(?i)unable to checkout (?:requested )?ref(?:erence)?(?:\s|:)",
        ],
        confidence_base=0.85,
        priority=1,
        hint="Référence git introuvable au checkout (branche/tag/sha).",
        mutation="Vérifier que la branche existe encore côté remote et aligner la référence checkout (head_ref/sha).",
    ),
    PatternSignature(
        category="PERMISSIONS",
        patterns=[
            r"permission denied",
            r"403 forbidden",
            r"insufficient.*permission",
            r"resource not accessible",
            r"403.*github",
            r"unauthorized",
        ],
        confidence_base=0.75,
        priority=1,
        hint="Permissions insuffisantes (token/ACL).",
        mutation="Ajouter les permissions minimales requises au job et vérifier secrets disponibles.",
    ),
    PatternSignature(
        category="NETWORK_TRANSIENT",
        patterns=[
            r"connection.*timeout",
            r"name resolution failed",
            r"network.*unreachable",
            r"ssl.*error",
            r"read timeout",
            r"connection reset",
        ],
        confidence_base=0.70,
        priority=2,
        hint="Instabilité réseau probable (timeouts/DNS).",
        mutation="Introduire retries idempotents avec backoff et miroir de registry.",
    ),
    PatternSignature(
        category="API_CONTRACT_DRIFT",
        patterns=[
            r"importerror.*cannot import",
            r"attributeerror.*module.*has no attribute",
            r"failed to import",
            r"api.*contract",
            r"smoke.*test.*failed",
        ],
        confidence_base=0.75,
        priority=1,
        hint="Imports critiques cassés.",
        mutation="Aligner l'API publique et le test de contrat import après revue des exports.",
    ),
    PatternSignature(
        category="TYPE_CHECK",
        patterns=[
            r"error:.*\[.*\]",
            r"found \d+ error.*in \d+ file",
            r"incompatible type",
            r"missing return statement",
            r"no return value expected",
        ],
        confidence_base=0.73,
        priority=1,
        hint="Échec vérification de types (mypy).",
        mutation="Corriger les annotations/types manquants ou isoler imports optionnels en mode typé.",
    ),
    PatternSignature(
        category="QUALITY_GATE",
        patterns=[
            r"ruff.*error",
            r"would reformat",
            r"reformatted",
            r"e\d{3}.*\[.*\]",
            r"black.*failed",
        ],
        confidence_base=0.73,
        priority=2,
        hint="Échec qualité (lint/format).",
        mutation="Appliquer le formatage/lint en local et verrouiller la version des outils.",
    ),
    PatternSignature(
        category="TEST_REGRESSION",
        patterns=[
            r"failed.*\d+.*error",
            r"assert.*failed",
            r"\d+ failed",
            r"coverage.*below",
            r"assertion error",
            r"test.*failed",
        ],
        confidence_base=0.70,
        priority=1,
        hint="Échec tests. Examiner stacktrace et régression fonctionnelle.",
        mutation="Isoler le test fautif, reproduire localement, corriger puis ajouter garde anti-régression.",
    ),
    PatternSignature(
        category="TIMEOUT_CAPACITY",
        patterns=[
            r"timed out after",
            r"job.*cancelled.*timeout",
            r"exceeded.*time limit",
            r"timeout.*\d+.*minutes",
        ],
        confidence_base=0.72,
        priority=2,
        hint="Job expiré. Capacité runner ou suite trop longue.",
        mutation="Scinder le job en segments et activer cache pour réduire la durée.",
    ),
    PatternSignature(
        category="CI_GATE_CASCADE",
        patterns=[
            r"ci resonance.*sous le seuil",
            r"résonance.*mode block",
            r"below.*dynamic.*threshold",
            r"ci resonance gate.*fail",
        ],
        confidence_base=0.80,
        priority=3,
        hint="Échec en cascade du CI Gate (effet secondaire d'un autre échec). Ce n'est pas une cause racine.",
        mutation="Résoudre les échecs en amont. Ce job se rétablira automatiquement.",
    ),
]

_UNCLASSIFIED_RESULT = ClassificationResult(
    category="UNCLASSIFIED",
    confidence=0.55,
    priority=3,
    hint="Cause non classée automatiquement. Inspection manuelle nécessaire.",
    mutation="Collecter les logs détaillés et enrichir la taxonomie avec ce nouveau motif.",
    matched_patterns=[],
)


def classifier_log(
    log_text: str,
    catalogue: Optional[List[PatternSignature]] = None,
) -> ClassificationResult:
    """
    Classifie un log brut en appliquant les signatures du catalogue.

    Retourne le meilleur ClassificationResult ou UNCLASSIFIED si aucun pattern ne matche.
    """
    effective_catalogue = catalogue if catalogue is not None else CATALOGUE_SIGNATURES
    normalized = log_text.lower()

    best_score = 0.0
    best_result: Optional[ClassificationResult] = None

    for sig in effective_catalogue:
        matched: List[str] = []
        for pattern in sig.patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                matched.append(pattern)

        if not matched:
            continue

        score_raw = sig.confidence_base + 0.05 * min(len(matched) - 1, 4)
        confidence = min(0.99, score_raw)
        weighted = confidence * (1.0 / sig.priority)

        if weighted > best_score:
            best_score = weighted
            best_result = ClassificationResult(
                category=sig.category,
                confidence=confidence,
                priority=sig.priority,
                hint=sig.hint,
                mutation=sig.mutation,
                matched_patterns=matched,
            )

    return best_result if best_result is not None else _UNCLASSIFIED_RESULT


def classifier_depuis_nom(job_name: str, step_name: str) -> ClassificationResult:
    """
    Wrapper de compatibilité : classifie depuis les noms de job/étape.

    Construit un texte synthétique et délègue à classifier_log.
    """
    synthetic_log = f"{job_name} {step_name}"
    return classifier_log(synthetic_log)


def enrichir_depuis_logs(
    result: ClassificationResult, raw_log: str
) -> ClassificationResult:
    """
    Tente d'enrichir un résultat UNCLASSIFIED en analysant les logs bruts.

    Si le résultat est déjà classifié, le retourne inchangé.
    """
    if result.category != "UNCLASSIFIED":
        return result
    enriched = classifier_log(raw_log)
    if enriched.category != "UNCLASSIFIED":
        return enriched
    return result


__all__ = [
    "PatternSignature",
    "ClassificationResult",
    "CATALOGUE_SIGNATURES",
    "classifier_log",
    "classifier_depuis_nom",
    "enrichir_depuis_logs",
]
