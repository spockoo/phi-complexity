"""
phi_complexity/fingerprint.py — Empreinte φ (Phi-Fingerprint)

Calcule un vecteur géométrique normalisé pour tout fichier analysé
(source ou binaire). Basé sur les invariants mathématiques du nombre d'or,
ce fingerprint capture la **structure** du code plutôt que son contenu,
rendant la détection de variants résistante aux mutations cosmétiques.

Composantes du vecteur φ-fingerprint (8 dimensions) :
    [0] branch_ratio     : Ratio branchements / instructions linéaires → 1/φ idéal
    [1] entropy_mean     : Entropie de Shannon moyenne (normalisée sur 8.0 bits)
    [2] entropy_variance : Variance de l'entropie entre sections/fonctions
    [3] lilith_variance  : Variance de Lilith sur la distribution des routines
    [4] fibonacci_dist   : Distance de Fibonacci normalisée des tailles
    [5] phi_ratio_delta  : |φ_ratio - φ| — écart au nombre d'or
    [6] zeta_score       : Score Zeta de résonance globale
    [7] complexity_ratio : Ratio complexité max / complexité moyenne

Phase 24 du Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .core import PHI, SEQUENCE_FIBONACCI, distance_fibonacci

# ────────────────────────────────────────────────────────
# CONSTANTES DE NORMALISATION
# ────────────────────────────────────────────────────────

_NORM_ENTROPIE: float = 8.0  # Entropie max pour un octet (log2(256))
_NORM_LILITH: float = 10000.0  # Plafond de normalisation variance
_NORM_FIB_DIST: float = 100.0  # Distance Fibonacci maximale attendue
_NORM_COMPLEXITY: float = 1000.0  # Complexité maximale attendue

# Seuils de classification par fingerprint
_SEUIL_SUSPECT: float = 0.65
_SEUIL_MALVEILLANT: float = 0.80

_FINGERPRINT_DIM: int = 8
"""Nombre de dimensions du vecteur φ-fingerprint."""


# ────────────────────────────────────────────────────────
# STRUCTURE DE DONNÉES
# ────────────────────────────────────────────────────────


@dataclass
class PhiFingerprint:
    """
    Empreinte géométrique φ d'un fichier analysé.

    Capture la structure mathématique invariante du code,
    indépendamment du contenu textuel ou des mutations cosmétiques.

    Attributs :
        vecteur         : Vecteur normalisé à 8 dimensions [0.0, 1.0].
        score_anomalie  : Score de divergence par rapport au profil φ idéal.
        classification  : 'SAIN', 'SUSPECT', ou 'MALVEILLANT'.
        nb_sections     : Nombre de sections/fonctions analysées.
        format_source   : Format du fichier source ('python', 'elf', 'asm', etc.).
        timestamp       : Epoch UNIX de calcul.
    """

    vecteur: List[float] = field(default_factory=list)
    score_anomalie: float = 0.0
    classification: str = "SAIN"
    nb_sections: int = 0
    format_source: str = "inconnu"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, object]:
        """Sérialise le fingerprint en dictionnaire JSON-compatible."""
        return {
            "vecteur": [round(v, 6) for v in self.vecteur],
            "score_anomalie": round(self.score_anomalie, 4),
            "classification": self.classification,
            "nb_sections": self.nb_sections,
            "format_source": self.format_source,
            "timestamp": self.timestamp,
        }


# ────────────────────────────────────────────────────────
# MOTEUR DE FINGERPRINTING
# ────────────────────────────────────────────────────────


class FingerprintEngine:
    """
    Moteur de calcul de l'empreinte φ (Phi-Fingerprint).

    Analyse un fichier via le pipeline phi-complexity et produit
    un vecteur géométrique normalisé capturant la structure invariante.

    Usage :
        engine = FingerprintEngine()
        fp = engine.calculer("mon_binaire.elf")
        print(fp.classification)  # → 'SAIN' ou 'SUSPECT'
        print(fp.vecteur)         # → [0.38, 0.72, ...]
    """

    def calculer(self, fichier: str) -> PhiFingerprint:
        """
        Calcule le φ-fingerprint d'un fichier.

        Args:
            fichier : Chemin du fichier à analyser (source ou binaire).

        Returns:
            PhiFingerprint avec vecteur normalisé et classification.
        """
        from .analyseur import AnalyseurPhi
        from .metriques import CalculateurRadiance

        analyseur = AnalyseurPhi(fichier)
        resultat = analyseur.analyser()
        calc = CalculateurRadiance(resultat)
        metriques = calc.calculer()

        return self._construire_fingerprint(metriques, fichier)

    def calculer_depuis_metriques(
        self, metriques: Dict[str, Any], fichier: str = ""
    ) -> PhiFingerprint:
        """
        Calcule le φ-fingerprint depuis des métriques pré-calculées.

        Utile pour éviter de ré-analyser un fichier déjà audité.
        """
        return self._construire_fingerprint(metriques, fichier)

    def _construire_fingerprint(
        self, metriques: Dict[str, Any], fichier: str
    ) -> PhiFingerprint:
        """Construit le fingerprint depuis les métriques calculées."""
        vecteur = self._calculer_vecteur(metriques)
        score = self._calculer_score_anomalie(vecteur)
        classification = self._classifier(score)

        # Détecter le format source depuis l'extension
        ext = fichier.rsplit(".", 1)[-1].lower() if "." in fichier else ""
        format_source = self._detecter_format(ext)

        return PhiFingerprint(
            vecteur=vecteur,
            score_anomalie=score,
            classification=classification,
            nb_sections=int(metriques.get("nb_fonctions", 0)),
            format_source=format_source,
        )

    def _calculer_vecteur(self, m: Dict[str, Any]) -> List[float]:
        """
        Encode les métriques en vecteur normalisé à 8 dimensions.

        Chaque dimension est bornée dans [0.0, 1.0] pour permettre
        la comparaison par similitude cosinus.
        """
        # [0] Branch ratio : ratio de complexité relative
        phi_ratio = float(m.get("phi_ratio", 1.0))
        branch_ratio = min(1.0, abs(1.0 / phi_ratio - 1.0 / PHI) if phi_ratio > 1e-9 else 1.0)

        # [1] Entropie moyenne normalisée
        entropy_mean = min(1.0, float(m.get("shannon_entropy", 0.0)) / _NORM_ENTROPIE)

        # [2] Variance de l'entropie (approximée par la variance de Lilith normalisée)
        lilith = float(m.get("lilith_variance", 0.0))
        entropy_variance = min(1.0, math.sqrt(lilith) / math.sqrt(_NORM_LILITH))

        # [3] Variance de Lilith pure
        lilith_norm = min(1.0, lilith / _NORM_LILITH)

        # [4] Distance de Fibonacci normalisée
        fib_dist = float(m.get("fibonacci_distance", 0.0))
        fibonacci_dist = min(1.0, fib_dist / _NORM_FIB_DIST)

        # [5] Delta par rapport au nombre d'or
        phi_delta = float(m.get("phi_ratio_delta", abs(phi_ratio - PHI)))
        phi_ratio_delta = min(1.0, phi_delta / PHI)

        # [6] Score Zeta (déjà dans [0, 1])
        zeta = min(1.0, float(m.get("zeta_score", 0.0)))

        # [7] Ratio de complexité (oudjat_complexite / moyenne)
        oudjat = m.get("oudjat") or {}
        oudjat_c = float(oudjat.get("complexite", 0)) if isinstance(oudjat, dict) else 0.0
        nb_fonctions = max(1, int(m.get("nb_fonctions", 1)))
        complexity_ratio = min(1.0, oudjat_c / (_NORM_COMPLEXITY / nb_fonctions)) if oudjat_c > 0 else 0.0

        return [
            branch_ratio,
            entropy_mean,
            entropy_variance,
            lilith_norm,
            fibonacci_dist,
            phi_ratio_delta,
            zeta,
            complexity_ratio,
        ]

    def _calculer_score_anomalie(self, vecteur: List[float]) -> float:
        """
        Calcule le score de divergence par rapport au profil φ idéal.

        Le profil idéal est un code dont :
        - Le branch_ratio est proche de 0 (ratio = φ)
        - L'entropie est modérée (≈ 0.3-0.5)
        - La variance est faible
        - La distance Fibonacci est faible
        - Le phi_ratio_delta est 0

        Score = distance euclidienne pondérée au vecteur idéal.
        Les poids sont calibrés selon Fibonacci : [1,1,2,3,5,8,5,3].
        """
        # Vecteur idéal : code parfaitement harmonieux
        ideal = [0.0, 0.35, 0.0, 0.0, 0.0, 0.0, 0.8, 0.1]

        # Poids Fibonacci pour chaque dimension (les plus discriminantes pèsent plus)
        poids = [1.0, 1.0, 2.0, 3.0, 5.0, 8.0, 5.0, 3.0]
        total_poids = sum(poids)

        distance_sq = sum(
            p * (v - i) ** 2
            for v, i, p in zip(vecteur, ideal, poids)
        )
        return min(1.0, math.sqrt(distance_sq / total_poids))

    def _classifier(self, score: float) -> str:
        """Classifie selon le score d'anomalie."""
        if score >= _SEUIL_MALVEILLANT:
            return "MALVEILLANT"
        if score >= _SEUIL_SUSPECT:
            return "SUSPECT"
        return "SAIN"

    def _detecter_format(self, ext: str) -> str:
        """Détecte le format source depuis l'extension."""
        formats: Dict[str, str] = {
            "py": "python",
            "c": "c",
            "cpp": "cpp",
            "h": "c-header",
            "hpp": "cpp-header",
            "rs": "rust",
            "asm": "assembleur",
            "s": "assembleur",
            "elf": "elf",
            "so": "elf-shared",
            "o": "elf-object",
            "exe": "pe",
            "dll": "pe-dll",
            "sys": "pe-driver",
            "dylib": "macho-dylib",
            "bin": "binaire",
        }
        return formats.get(ext, "inconnu")


# ────────────────────────────────────────────────────────
# SIMILITUDE COSINUS (pour comparaison de fingerprints)
# ────────────────────────────────────────────────────────


def similitude_cosinus(a: List[float], b: List[float]) -> float:
    """
    Calcule la similitude cosinus entre deux vecteurs φ-fingerprint.

    Retourne une valeur dans [0.0, 1.0] :
        1.0 = structures identiques
        0.0 = structures orthogonales (totalement différentes)
    """
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))
