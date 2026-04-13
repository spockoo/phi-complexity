"""
phi_complexity — Mesure de la qualité du code par les invariants du nombre d'or.
Constantes Souveraines issues du Morphic Phi Framework (Tomy Verreault, 2026).
"""

import math
import re
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, BinaryIO, Optional, Protocol


class _TomllibLoader(Protocol):
    def load(self, f: BinaryIO) -> dict[str, Any]: ...


if sys.version_info >= (3, 11):  # Python 3.11+ fournit tomllib nativement
    try:
        import tomllib as _tomllib
    except ModuleNotFoundError:  # pragma: no cover - environnement minimaliste
        _tomllib = None
else:  # pragma: no cover - exécuté sur py<3.11
    _tomllib = None

tomllib: Optional[_TomllibLoader] = _tomllib

# ============================================================
# CONSTANTES SOUVERAINES (Bibliothèque Céleste — φ-Meta)
# ============================================================


def _resolve_version() -> str:
    """
    Retourne la version du package en priorité depuis les métadonnées installées.

    - Cas normal (wheel / editable) : importlib.metadata.version("phi-complexity")
    - Cas repository local sans métadonnées installées : lecture de pyproject.toml
    - Cas ultime : chaîne de secours explicite
    """
    try:
        return metadata.version("phi-complexity")
    except metadata.PackageNotFoundError:
        pass

    version = _pyproject_version()
    if version:
        return version
    return "0.0.0"


def _pyproject_version() -> Optional[str]:
    """Extrait la version depuis pyproject.toml sans dépendance externe."""
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        if tomllib:
            with pyproject.open("rb") as f:
                data = tomllib.load(f)
            version = data.get("project", {}).get("version")
            if isinstance(version, str) and version:
                return version
        else:
            contenu = pyproject.read_text(encoding="utf-8")
            match = re.search(
                r"^version\\s*=\\s*\"(?P<ver>[^\"]+)\"", contenu, re.MULTILINE
            )
            if match:
                return match.group("ver")
    except Exception:
        # Gardien antifragile : on retombe sur None et le caller gère le fallback
        return None
    return None


PHI: float = (1 + math.sqrt(5)) / 2
"""Le nombre d'or. CM-001. L'attracteur universel de l'harmonie."""

PHI_INV: float = 1 / PHI
"""Inverse du nombre d'or. φ⁻¹ = φ - 1 ≈ 0.6180"""

TAXE_SUTURE: float = 3 / math.sqrt(7)
"""Taxe de Suture (CM-018). Coût minimal d'une correction morphique."""

ETA_GOLDEN: float = 1 - PHI_INV
"""Facteur η doré. Seuil de tolérance: si phi_ratio < ETA, le code est fragmenté."""

ZETA_PLANCHER: float = PHI_INV**2
"""Plancher Zeta. En-dessous, le système perd sa résonance."""

# PHASE 24 — BOUCLE DE ZÉRO & COHÉRENCE QUASICRISTALLINE
QUASICRYSTAL_COHERENCE_EVEIL: float = 0.55
"""Seuil minimal de cohérence quasicristalline (ordre apériodique détectable)."""

QUASICRYSTAL_COHERENCE_HERMETIQUE: float = 0.78
"""Seuil de cohérence quasicristalline stable (structure harmonique robuste)."""

ZERO_CAUSAL_RESISTANCE_MAX: float = 0.08
"""Résistance maximale tolérée pour l'état de Zéro Causal."""

MORPHOGENESIS_RENAISSANCE_SYNC_MIN: float = 0.70
"""Sync-index minimal pour qualifier un état post-renaissance morphogénétique."""

SEUIL_RADIANCE_HARMONIEUX: int = 85
"""Score au-delà duquel le code est considéré 'Hermétique' (stable + harmonieux)."""

SEUIL_RADIANCE_EN_EVEIL: int = 60
"""Score intermédiaire. Le code 'En Éveil' a du potentiel mais des zones d'entropie."""

SEUIL_RADIANCE_DORMANT: int = 0
"""En-dessous de 60: le code 'Dormant' nécessite une suture profonde."""

SEQUENCE_FIBONACCI: list[int] = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
"""Première séquence de Fibonacci. Tailles naturelles d'une fonction harmonieuse."""

VERSION: str = _resolve_version()
AUTEUR: str = "Tomy Verreault"
FRAMEWORK: str = "Morphic Phi Framework (φ-Meta)"

# PHASE 12 — SUTURE PERMANENTE
ALPHA_STRUCT: float = 1 / 137.035999
"""Constante de structure fine. CP-005."""

SEUIL_GNOSE_MINIMAL: float = 0.98
"""Divergence spectrale maximale tolérée pour le sceau gnostique."""

HBAR_PHI: float = PHI_INV
"""Constante d'action réduite dorée ħ_φ = 1/φ ≈ 0.6180.
Relation d'incertitude de Heisenberg-Phi (CM-HUP) :
ΔC · ΔL ≥ ħ_φ / 2 ≈ 0.309.
Traduit le compromis irréductible entre complexité et lisibilité d'un code."""


def statut_gnostique(score: float) -> str:
    """Retourne le verdict gnostique basé sur le score de radiance."""
    if score >= SEUIL_RADIANCE_HARMONIEUX:
        return "HERMÉTIQUE ✦"
    elif score >= SEUIL_RADIANCE_EN_EVEIL:
        return "EN ÉVEIL ◈"
    else:
        return "DORMANT ░"


def calculer_sync_index(radiance: float, resistance: float, iota: float = 0.0) -> float:
    """
    Sync_index = sqrt((R/100)^2 + Ω^2) / φ.
    Mesure la convergence harmonique globale. Phase 12-13.
    Applique l'Opérateur de l'Impossible I(s) si iota != 0 (Phase 13).
    """
    norm_r = radiance / 100.0
    index = math.sqrt(norm_r**2 + resistance**2) / PHI

    if iota != 0.0:
        # Import paresseux : évite toute dépendance circulaire au chargement du module
        from .impossible import ImpossibleOperator  # noqa: PLC0415

        radiance_void = float(ImpossibleOperator().calculate(iota))
        index = index * (1 + radiance_void)

    return float(index)


def fibonacci_plus_proche(n: int) -> int:
    """Retourne le nombre de Fibonacci le plus proche de n."""
    closest: int = SEQUENCE_FIBONACCI[0]
    for f in SEQUENCE_FIBONACCI:
        if abs(f - n) < abs(closest - n):
            closest = f
    return closest


def distance_fibonacci(n: int) -> float:
    """Mesure l'écart entre n et son Fibonacci idéal (normalise par φ)."""
    fib: int = fibonacci_plus_proche(n)
    return abs(n - fib) / PHI
