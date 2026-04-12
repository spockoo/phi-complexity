"""
phi_complexity/consensus.py — Consensus par Rétroaction Positive Récursive.

Module de validation croisée multi-signal avec convergence itérative.
Chaque cycle de rétroaction renforce les signaux concordants et atténue
les signaux divergents, jusqu'à convergence du score de consensus.

Architecture :
    Signal_1 ─┐
    Signal_2 ─┼─→ Fusion → Rétroaction → Convergence → Verdict
    Signal_N ─┘

Algorithme (Rétroaction Positive Récursive — RPR) :
    1. Collecte des signaux indépendants (sécurité, qualité, crypto).
    2. Moyenne pondérée initiale (fusion bayésienne).
    3. Pour chaque itération k :
       a. Calcul de l'accord δᵢ = 1 - |sᵢ - μₖ| / φ
       b. Renforcement : wᵢ ← wᵢ × (1 + δᵢ × α)    (rétroaction positive)
       c. Normalisation des poids ∑wᵢ = 1
       d. Recalcul μₖ₊₁ = ∑(wᵢ × sᵢ)
       e. Si |μₖ₊₁ - μₖ| < ε → convergence
    4. Verdict final avec métadonnées de convergence.

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .core import PHI, PHI_INV

# ──────────────────────────────────────────────
# CONSTANTES DU CONSENSUS RPR
# ──────────────────────────────────────────────

EPSILON_CONVERGENCE: float = 1e-4
"""Seuil de convergence : |μₖ₊₁ - μₖ| < ε."""

MAX_ITERATIONS: int = 200
"""Nombre maximal d'itérations de rétroaction."""

ALPHA_RETROACTION: float = PHI_INV
"""Facteur de rétroaction positive : α = 1/φ ≈ 0.618."""

SEUIL_CONSENSUS_FORT: float = 0.85
"""Consensus fort : tous les signaux convergent au-delà de 85%."""

SEUIL_CONSENSUS_MODERE: float = 0.60
"""Consensus modéré : convergence partielle."""


# ──────────────────────────────────────────────
# STRUCTURES DE DONNÉES
# ──────────────────────────────────────────────


@dataclass
class SignalConsensus:
    """Un signal d'analyse individuel soumis au consensus.

    Attributs :
        source     : Nom du système source (e.g. 'securite', 'qualite', 'crypto').
        score      : Score normalisé [0.0, 1.0].
        confiance  : Fiabilité estimée du signal [0.0, 1.0].
        metadata   : Données additionnelles du signal.
    """

    source: str
    score: float
    confiance: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.score = max(0.0, min(1.0, self.score))
        self.confiance = max(0.0, min(1.0, self.confiance))


@dataclass
class ResultatConsensus:
    """Résultat de la validation croisée par consensus RPR.

    Attributs :
        score_consensus : Score final après convergence [0.0, 1.0].
        niveau          : Classification du consensus.
        iterations      : Nombre d'itérations pour converger.
        convergent      : True si le processus a convergé.
        delta_final     : Dernière variation |μₖ₊₁ - μₖ|.
        poids_finaux    : Poids normalisés finaux par source.
        signaux         : Signaux d'entrée originaux.
        historique      : Historique des scores par itération.
        hash_consensus  : SHA-256 du consensus pour intégrité.
        timestamp       : Horodatage du calcul.
    """

    score_consensus: float
    niveau: str
    iterations: int
    convergent: bool
    delta_final: float
    poids_finaux: Dict[str, float]
    signaux: List[SignalConsensus]
    historique: List[float] = field(default_factory=list)
    hash_consensus: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le résultat en dictionnaire JSON-compatible."""
        return {
            "score_consensus": round(self.score_consensus, 6),
            "niveau": self.niveau,
            "iterations": self.iterations,
            "convergent": self.convergent,
            "delta_final": round(self.delta_final, 9),
            "poids_finaux": {k: round(v, 6) for k, v in self.poids_finaux.items()},
            "signaux": [
                {
                    "source": s.source,
                    "score": round(s.score, 6),
                    "confiance": round(s.confiance, 6),
                }
                for s in self.signaux
            ],
            "historique": [round(h, 6) for h in self.historique],
            "hash_consensus": self.hash_consensus,
            "timestamp": self.timestamp,
        }


# ──────────────────────────────────────────────
# JOURNAL DE CONSENSUS
# ──────────────────────────────────────────────


class JournalConsensus:
    """Journal structuré pour le processus de consensus RPR.

    Enregistre chaque itération, chaque décision, et le verdict final
    dans un fichier JSONL append-only avec intégrité SHA-256.
    """

    def __init__(self, workspace_root: str = ".") -> None:
        phi_dir = os.path.join(workspace_root, ".phi")
        consensus_dir = os.path.join(phi_dir, "consensus")
        if not os.path.exists(consensus_dir):
            os.makedirs(consensus_dir)
        self.journal_path = os.path.join(consensus_dir, "journal.jsonl")

    def enregistrer(self, evenement: str, details: Dict[str, Any]) -> None:
        """Enregistre un événement dans le journal de consensus."""
        entry: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "evenement": evenement,
            "details": details,
        }
        entry_json = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        entry["hash"] = hashlib.sha256(entry_json.encode("utf-8")).hexdigest()

        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def lire(self, limite: int = 100) -> List[Dict[str, Any]]:
        """Lit les dernières entrées du journal."""
        if not os.path.exists(self.journal_path):
            return []
        try:
            with open(self.journal_path, "r", encoding="utf-8") as f:
                lignes = [json.loads(line) for line in f if line.strip()]
            return lignes[-limite:]
        except (json.JSONDecodeError, OSError):
            return []

    def verifier_integrite(self) -> bool:
        """Vérifie l'intégrité cryptographique du journal."""
        entries = self.lire(10000)
        for entry in entries:
            stored_hash = entry.pop("hash", "")
            entry_json = json.dumps(entry, sort_keys=True, ensure_ascii=False)
            computed = hashlib.sha256(entry_json.encode("utf-8")).hexdigest()
            entry["hash"] = stored_hash
            if computed != stored_hash:
                return False
        return True


# ──────────────────────────────────────────────
# MOTEUR DE CONSENSUS RPR
# ──────────────────────────────────────────────


class MoteurConsensus:
    """Moteur de consensus par rétroaction positive récursive (RPR).

    Fusionne N signaux d'analyse indépendants en un score unique
    via un processus itératif où les signaux concordants sont
    renforcés à chaque cycle (rétroaction positive).

    Usage :
        moteur = MoteurConsensus()
        signaux = [
            SignalConsensus("securite", 0.85, 0.9),
            SignalConsensus("qualite", 0.78, 0.8),
            SignalConsensus("crypto", 0.90, 0.7),
        ]
        resultat = moteur.calculer_consensus(signaux)
    """

    def __init__(
        self,
        epsilon: float = EPSILON_CONVERGENCE,
        max_iterations: int = MAX_ITERATIONS,
        alpha: float = ALPHA_RETROACTION,
        journal: Optional[JournalConsensus] = None,
    ) -> None:
        self._epsilon = epsilon
        self._max_iter = max_iterations
        self._alpha = alpha
        self._journal = journal

    def _journaliser(self, evenement: str, details: Dict[str, Any]) -> None:
        """Journalise un événement si le journal est actif."""
        if self._journal is not None:
            self._journal.enregistrer(evenement, details)

    def _moyenne_ponderee(
        self, signaux: List[SignalConsensus], poids: List[float]
    ) -> float:
        """Calcule la moyenne pondérée des scores."""
        somme_poids = sum(poids)
        if somme_poids < 1e-12:
            return 0.0
        return sum(s.score * w for s, w in zip(signaux, poids)) / somme_poids

    def _calculer_accord(self, score: float, mu: float) -> float:
        """Calcule le facteur d'accord δ = 1 - |s - μ| / φ.

        Plus le signal est proche du consensus, plus δ est élevé.
        Clamped dans [0, 1] pour stabilité.
        """
        delta = 1.0 - abs(score - mu) / PHI
        return max(0.0, min(1.0, delta))

    def _retroaction_positive(
        self,
        signaux: List[SignalConsensus],
        poids: List[float],
        mu: float,
    ) -> List[float]:
        """Applique la rétroaction positive : renforce les poids concordants.

        Pour chaque signal i :
            wᵢ ← wᵢ × (1 + δᵢ × α)
        où δᵢ est le facteur d'accord et α le facteur de rétroaction.
        """
        nouveaux_poids: List[float] = []
        for s, w in zip(signaux, poids):
            accord = self._calculer_accord(s.score, mu)
            w_new = w * (1.0 + accord * self._alpha)
            nouveaux_poids.append(w_new)

        # Normalisation pour éviter la divergence
        somme = sum(nouveaux_poids)
        if somme > 1e-12:
            nouveaux_poids = [w / somme for w in nouveaux_poids]
        return nouveaux_poids

    def _classifier_consensus(self, score: float, convergent: bool) -> str:
        """Classifie le niveau de consensus."""
        if not convergent:
            return "DIVERGENT"
        if score >= SEUIL_CONSENSUS_FORT:
            return "FORT ✦"
        if score >= SEUIL_CONSENSUS_MODERE:
            return "MODÉRÉ ◈"
        return "FAIBLE ░"

    def _signer_consensus(self, resultat: ResultatConsensus) -> str:
        """Produit un hash SHA-256 du résultat pour intégrité."""
        payload = (
            f"{resultat.score_consensus:.9f}:"
            f"{resultat.iterations}:"
            f"{resultat.convergent}:"
            f"{resultat.timestamp}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def calculer_consensus(self, signaux: List[SignalConsensus]) -> ResultatConsensus:
        """Calcule le consensus par rétroaction positive récursive.

        Args:
            signaux : Liste de SignalConsensus provenant de sources
                      indépendantes (sécurité, qualité, cryptographie, etc.).

        Returns:
            ResultatConsensus avec score convergé, poids finaux,
            historique et hash d'intégrité.
        """
        if not signaux:
            return ResultatConsensus(
                score_consensus=0.0,
                niveau="VIDE",
                iterations=0,
                convergent=True,
                delta_final=0.0,
                poids_finaux={},
                signaux=[],
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

        self._journaliser(
            "consensus_debut",
            {
                "nb_signaux": len(signaux),
                "sources": [s.source for s in signaux],
            },
        )

        # Initialisation des poids par la confiance de chaque signal
        poids = [s.confiance for s in signaux]
        somme = sum(poids)
        if somme > 1e-12:
            poids = [w / somme for w in poids]
        else:
            poids = [1.0 / len(signaux)] * len(signaux)

        mu = self._moyenne_ponderee(signaux, poids)
        historique: List[float] = [mu]
        delta = float("inf")
        iteration = 0

        self._journaliser(
            "iteration_0",
            {"mu": round(mu, 9), "poids": [round(w, 6) for w in poids]},
        )

        # Boucle de rétroaction récursive
        for k in range(1, self._max_iter + 1):
            poids = self._retroaction_positive(signaux, poids, mu)
            mu_new = self._moyenne_ponderee(signaux, poids)
            delta = abs(mu_new - mu)
            mu = mu_new
            historique.append(mu)
            iteration = k

            self._journaliser(
                f"iteration_{k}",
                {
                    "mu": round(mu, 9),
                    "delta": round(delta, 9),
                    "poids": [round(w, 6) for w in poids],
                },
            )

            if delta < self._epsilon:
                break

        convergent = delta < self._epsilon
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        poids_finaux: Dict[str, float] = {}
        for s, w in zip(signaux, poids):
            poids_finaux[s.source] = w

        resultat = ResultatConsensus(
            score_consensus=mu,
            niveau=self._classifier_consensus(mu, convergent),
            iterations=iteration,
            convergent=convergent,
            delta_final=delta,
            poids_finaux=poids_finaux,
            signaux=list(signaux),
            historique=historique,
            timestamp=timestamp,
        )
        resultat.hash_consensus = self._signer_consensus(resultat)

        self._journaliser(
            "consensus_fin",
            {
                "score": round(mu, 6),
                "niveau": resultat.niveau,
                "iterations": iteration,
                "convergent": convergent,
                "hash": resultat.hash_consensus,
            },
        )

        return resultat

    def rapport_consensus(self, resultat: ResultatConsensus) -> str:
        """Génère le rapport ASCII du consensus RPR."""
        pct = resultat.score_consensus * 100
        barre_len = 30
        rempli = int(pct / 100 * barre_len)
        barre = "█" * rempli + "░" * (barre_len - rempli)

        symbole = {
            "FORT ✦": "✦",
            "MODÉRÉ ◈": "◈",
            "FAIBLE ░": "░",
            "DIVERGENT": "⚠",
            "VIDE": "∅",
        }.get(resultat.niveau, "?")

        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║  PHI-CONSENSUS — RÉTROACTION POSITIVE RÉCURSIVE  ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  Score Final    : [{barre}] {pct:.2f}%",
            f"  Niveau         : {symbole}  {resultat.niveau}",
            f"  Convergence    : {'OUI' if resultat.convergent else 'NON'}"
            f" ({resultat.iterations} itérations, δ={resultat.delta_final:.2e})",
            "",
            "  Signaux d'entrée :",
        ]

        for s in resultat.signaux:
            poids = resultat.poids_finaux.get(s.source, 0.0)
            lignes.append(
                f"    ◈  {s.source:<12s} : {s.score * 100:5.1f}%"
                f"  (poids: {poids:.4f}, confiance: {s.confiance:.2f})"
            )

        lignes += [
            "",
            f"  Hash intégrité : {resultat.hash_consensus[:16]}…",
            f"  Timestamp      : {resultat.timestamp}",
            "",
            "  ─────────────────────────────────────────────────",
            f"  α={ALPHA_RETROACTION:.4f}  ε={EPSILON_CONVERGENCE:.1e}"
            f"  φ={PHI:.6f}",
            "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
        ]
        return "\n".join(lignes)

    def exporter_json(self, resultat: ResultatConsensus, chemin: str) -> None:
        """Exporte le résultat de consensus en JSON."""
        repertoire = os.path.dirname(chemin)
        if repertoire and not os.path.exists(repertoire):
            os.makedirs(repertoire)
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(resultat.to_dict(), f, indent=2, ensure_ascii=False)

        self._journaliser(
            "export_json",
            {"chemin": chemin, "hash": resultat.hash_consensus},
        )


# ──────────────────────────────────────────────
# FONCTIONS UTILITAIRES POUR CI/CD
# ──────────────────────────────────────────────


def consensus_rapide(
    scores: Dict[str, float],
    confiances: Optional[Dict[str, float]] = None,
) -> ResultatConsensus:
    """Raccourci pour un consensus rapide sans journalisation.

    Args:
        scores     : Dict source → score [0,1].
        confiances : Dict source → confiance [0,1] (optionnel).

    Returns:
        ResultatConsensus convergé.

    Usage :
        resultat = consensus_rapide({
            "securite": 0.85,
            "qualite": 0.78,
            "crypto": 0.92,
        })
    """
    confiances = confiances or {}
    signaux = [
        SignalConsensus(
            source=src,
            score=sc,
            confiance=confiances.get(src, 0.8),
        )
        for src, sc in scores.items()
    ]
    moteur = MoteurConsensus()
    return moteur.calculer_consensus(signaux)
