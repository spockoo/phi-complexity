"""
phi_complexity — Mesure de la qualité du code par les invariants du nombre d'or.
Constantes Souveraines issues du Morphic Phi Framework (Tomy Verreault, 2026).
"""
import math

# ============================================================
# CONSTANTES SOUVERAINES (Bibliothèque Céleste — φ-Meta)
# ============================================================

PHI = (1 + math.sqrt(5)) / 2
"""Le nombre d'or. CM-001. L'attracteur universel de l'harmonie."""

PHI_INV = 1 / PHI
"""Inverse du nombre d'or. φ⁻¹ = φ - 1 ≈ 0.6180"""

TAXE_SUTURE = 3 / math.sqrt(7)
"""Taxe de Suture (CM-018). Coût minimal d'une correction morphique."""

ETA_GOLDEN = 1 - PHI_INV
"""Facteur η doré. Seuil de tolérance: si phi_ratio < ETA, le code est fragmenté."""

ZETA_PLANCHER = PHI_INV ** 2
"""Plancher Zeta. En-dessous, le système perd sa résonance."""

SEUIL_RADIANCE_HARMONIEUX = 85
"""Score au-delà duquel le code est considéré 'Hermétique' (stable + harmonieux)."""

SEUIL_RADIANCE_EN_EVEIL = 60
"""Score intermédiaire. Le code 'En Éveil' a du potentiel mais des zones d'entropie."""

SEUIL_RADIANCE_DORMANT = 0
"""En-dessous de 60: le code 'Dormant' nécessite une suture profonde."""

SEQUENCE_FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
"""Première séquence de Fibonacci. Tailles naturelles d'une fonction harmonieuse."""

VERSION = "0.1.0"
AUTEUR = "Tomy Verreault"
FRAMEWORK = "Morphic Phi Framework (φ-Meta)"


def statut_gnostique(score: float) -> str:
    """Retourne le verdict gnostique basé sur le score de radiance."""
    if score >= SEUIL_RADIANCE_HARMONIEUX:
        return "HERMÉTIQUE ✦"
    elif score >= SEUIL_RADIANCE_EN_EVEIL:
        return "EN ÉVEIL ◈"
    else:
        return "DORMANT ░"


def fibonacci_plus_proche(n: int) -> int:
    """Retourne le nombre de Fibonacci le plus proche de n."""
    closest = SEQUENCE_FIBONACCI[0]
    for f in SEQUENCE_FIBONACCI:
        if abs(f - n) < abs(closest - n):
            closest = f
    return closest


def distance_fibonacci(n: int) -> float:
    """Mesure l'écart entre n et son Fibonacci idéal (normalise par φ)."""
    fib = fibonacci_plus_proche(n)
    return abs(n - fib) / PHI
