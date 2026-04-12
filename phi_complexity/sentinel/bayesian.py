"""
phi_complexity/sentinel/bayesian.py — Couche 4 : Corrélation Bayésienne Multi-Signaux

Fusionne les signaux de toutes les couches précédentes (OS + commits)
en un score de risque unifié, calibré par un modèle bayésien.

Sources de signaux intégrées :
    - Couche 3 (Behavior) : score comportemental OS
    - commit_risk         : score de risque du commit git
    - Télémétrie          : statistiques de traces suspectes

Formule de fusion :
    P(menace | OS, commit, télémétrie) ∝
        P(menace) × L(OS) × L(commit) × L(télémétrie)

Le résultat est un ScoreSentinel avec décomposition des contributions.

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .behavior import BehaviorAnalyzer, SignalComportemental
from .telemetry import TelemetryNormalizer, TraceNormalisee

# ──────────────────────────────────────────────
# CONSTANTES DU MODÈLE BAYÉSIEN SENTINEL
# ──────────────────────────────────────────────

# Prior : probabilité a priori d'une menace active sur un système quelconque
_PRIOR_MENACE: float = 0.05  # Conservateur : 5% de base

# Seuils de classification
_SEUIL_FAIBLE: float = 0.20
_SEUIL_MODERE: float = 0.45
_SEUIL_ELEVE: float = 0.70


# ──────────────────────────────────────────────
# STRUCTURES DE DONNÉES
# ──────────────────────────────────────────────


@dataclass
class ScoreSentinel:
    """
    Score unifié produit par le corrélateur bayésien (Couche 4).

    Attributs :
        score_final       : Score global de menace [0.0, 1.0].
        niveau            : Classification textuelle du risque.
        score_os          : Contribution du score comportemental OS.
        score_commit      : Contribution du score de risque commit (si fourni).
        score_telemetrie  : Contribution des statistiques de télémétrie.
        facteurs          : Facteurs principaux ayant influencé le score.
        timestamp         : Epoch de calcul du score.
    """

    score_final: float
    niveau: str
    score_os: float
    score_commit: float
    score_telemetrie: float
    facteurs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, object]:
        """Sérialise le score en dictionnaire JSON-compatible."""
        return {
            "score_final": round(self.score_final, 4),
            "niveau": self.niveau,
            "score_os": round(self.score_os, 4),
            "score_commit": round(self.score_commit, 4),
            "score_telemetrie": round(self.score_telemetrie, 4),
            "facteurs": self.facteurs,
            "timestamp": self.timestamp,
        }


# ──────────────────────────────────────────────
# CORRÉLATEUR BAYÉSIEN
# ──────────────────────────────────────────────


class BayesianCorrelator:
    """
    Couche 4 — Corrélateur Bayésien Multi-Signaux.

    Fusionne les signaux comportementaux, de commit et de télémétrie
    pour produire un score de menace unifié et explicable.

    Usage :
        correlator = BayesianCorrelator()
        score = correlator.calculer_score(
            signaux=signaux,
            traces=traces,
            score_commit=0.3,
        )
    """

    def __init__(self, prior: float = _PRIOR_MENACE) -> None:
        """
        Args:
            prior: Probabilité a priori d'une menace (défaut: 0.05).
        """
        self._prior = prior
        self._analyzer = BehaviorAnalyzer()
        self._normalizer = TelemetryNormalizer()

    def _score_telemetrie(self, traces: List[TraceNormalisee]) -> float:
        """
        Calcule le score de risque à partir des statistiques de télémétrie.

        Formule : (nb_suspect + 2 × nb_critique) / (total + ε)
        Normalisé dans [0, 1].
        """
        if not traces:
            return 0.0
        stats = self._normalizer.statistiques(traces)
        nb_suspect = int(stats.get("suspect", 0))
        nb_critique = int(stats.get("critique", 0))
        total = int(stats.get("total", 1))
        score = (nb_suspect + 2 * nb_critique) / (total + 1e-9)
        return min(1.0, score)

    def _fusionner_bayesien(
        self,
        score_os: float,
        score_commit: float,
        score_telemetrie: float,
        score_fingerprint: float = 0.0,
    ) -> float:
        """
        Fusionne les scores par mise à jour bayésienne successive.

        Utilise le log-odds pour une fusion stable numériquement.
        Chaque signal est pondéré par sa fiabilité estimée :
            - OS behavior      : fiabilité 0.8 (observations directes)
            - commit risk      : fiabilité 0.6 (heuristique)
            - télémétrie stats : fiabilité 0.7 (indirect)
            - φ-fingerprint    : fiabilité 0.75 (géométrie structurelle)
        """
        # Log-odds initial depuis le prior
        epsilon = 1e-9
        log_odds = math.log((self._prior + epsilon) / (1.0 - self._prior + epsilon))

        # Mise à jour bayésienne pour chaque signal
        poids = [
            (score_os, 0.8),
            (score_commit, 0.6),
            (score_telemetrie, 0.7),
            (score_fingerprint, 0.75),
        ]

        for score, fiabilite in poids:
            # Un score nul signifie "absence d'information" → prior inchangé (LR = 1).
            if score < 1e-4:
                continue
            # Formule de fiabilité : si la source n'est pas parfaitement fiable,
            # on mélange son score avec l'incertitude uniforme (0.5).
            # score_effectif = r * score + (1 - r) * 0.5
            # Cela garantit que même un signal peu fiable reste une évidence positive.
            score_effectif = fiabilite * score + (1.0 - fiabilite) * 0.5
            lr_numerateur = score_effectif + epsilon
            lr_denominateur = (1.0 - score_effectif) + epsilon
            log_lr = math.log(lr_numerateur / lr_denominateur)
            log_odds += log_lr

        # Conversion log-odds → probabilité
        return float(1.0 / (1.0 + math.exp(-log_odds)))

    def _classifier_niveau(self, score: float) -> str:
        """Retourne le niveau de risque textuel."""
        if score < _SEUIL_FAIBLE:
            return "FAIBLE"
        if score < _SEUIL_MODERE:
            return "MODÉRÉ"
        if score < _SEUIL_ELEVE:
            return "ÉLEVÉ"
        return "CRITIQUE"

    def _identifier_facteurs(
        self,
        signaux: List[SignalComportemental],
        score_os: float,
        score_commit: float,
        score_telemetrie: float,
        score_fingerprint: float = 0.0,
    ) -> List[str]:
        """Identifie les facteurs dominants pour l'explication du score."""
        facteurs: List[str] = []

        if score_os >= 0.40:
            critiques = self._analyzer.signaux_critiques(signaux, seuil_confiance=0.60)
            if critiques:
                for s in critiques[:3]:
                    facteurs.append(
                        f"OS [{s.mitre_technique}]: {s.description} "
                        f"(confiance: {s.confiance * 100:.0f}%)"
                    )
            else:
                facteurs.append(f"Score OS élevé : {score_os * 100:.1f}%")

        if score_commit >= 0.30:
            facteurs.append(f"Score commit à risque : {score_commit * 100:.1f}%")

        if score_telemetrie >= 0.20:
            facteurs.append(
                f"Télémétrie suspecte : {score_telemetrie * 100:.1f}% de traces anormales"
            )

        if score_fingerprint >= 0.30:
            facteurs.append(
                f"φ-Fingerprint anomalique : divergence {score_fingerprint * 100:.1f}% "
                f"du profil géométrique idéal"
            )

        return facteurs

    def calculer_score(
        self,
        signaux: Optional[List[SignalComportemental]] = None,
        traces: Optional[List[TraceNormalisee]] = None,
        score_commit: float = 0.0,
        score_fingerprint: float = 0.0,
    ) -> ScoreSentinel:
        """
        Calcule le score de menace unifié à partir des signaux disponibles.

        Args:
            signaux           : Signaux comportementaux (Couche 3). Peut être None.
            traces            : Traces normalisées (Couche 2). Peut être None.
            score_commit      : Score de risque commit [0,1] (commit_risk.py). Défaut: 0.
            score_fingerprint : Score d'anomalie φ-fingerprint [0,1] (Phase 24). Défaut: 0.

        Returns:
            ScoreSentinel avec score final, niveau et facteurs dominants.
        """
        signaux = signaux or []
        traces = traces or []

        # Score OS (depuis les signaux comportementaux)
        score_os = self._analyzer.score_global(signaux)

        # Score télémétrie (depuis les stats de traces)
        score_tel = self._score_telemetrie(traces)

        # Fusion bayésienne (inclut le fingerprint si fourni)
        score_final = self._fusionner_bayesien(
            score_os, score_commit, score_tel, score_fingerprint
        )

        # Classification et facteurs
        niveau = self._classifier_niveau(score_final)
        facteurs = self._identifier_facteurs(
            signaux, score_os, score_commit, score_tel, score_fingerprint
        )

        return ScoreSentinel(
            score_final=score_final,
            niveau=niveau,
            score_os=score_os,
            score_commit=score_commit,
            score_telemetrie=score_tel,
            facteurs=facteurs,
        )

    def rapport_correlation(self, score: ScoreSentinel) -> str:
        """Génère le rapport ASCII du corrélateur bayésien."""
        pct = score.score_final * 100
        symbole = {
            "FAIBLE": "✅",
            "MODÉRÉ": "⚠️ ",
            "ÉLEVÉ": "🔴",
            "CRITIQUE": "🚨",
        }.get(score.niveau, "❓")

        barre_len = 30
        rempli = int(pct / 100 * barre_len)
        barre = "█" * rempli + "░" * (barre_len - rempli)

        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║   PHI-SENTINEL — CORRÉLATION BAYÉSIENNE          ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  Score Final   : [{barre}] {pct:.1f}%",
            f"  Niveau        : {symbole}  {score.niveau}",
            "",
            "  Décomposition :",
            f"    ◈  Score OS Comportemental : {score.score_os * 100:.1f}%",
            f"    ◈  Score Risque Commit     : {score.score_commit * 100:.1f}%",
            f"    ◈  Score Télémétrie        : {score.score_telemetrie * 100:.1f}%",
            "",
        ]

        if score.facteurs:
            lignes.append("  Facteurs dominants :")
            for facteur in score.facteurs:
                lignes.append(f"    ⚠  {facteur}")
        else:
            lignes.append("  ✦  Aucun facteur de risque dominant.")

        lignes += [
            "",
            "  ─────────────────────────────────────────────────",
            "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
        ]
        return "\n".join(lignes)
