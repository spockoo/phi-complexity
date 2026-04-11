"""
phi_complexity/notebook_helpers.py — Fonctions d'aide pour Jupyter Notebooks

Fournit :
    - Chargement simplifié des données φ-complexity
    - Fonctions de visualisation standard (matplotlib)
    - Magic commands IPython : %phi_check, %phi_report, %phi_spiral

Usage dans un notebook :
    from phi_complexity.notebook_helpers import (
        charger_metriques,
        radar_radiance,
        carte_heisenberg,
        enregistrer_magics,
    )
    enregistrer_magics()  # Active %phi_check, %phi_report, %phi_spiral

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional

from .core import PHI, HBAR_PHI

# ────────────────────────────────────────────────────────
# CHARGEMENT DE DONNÉES
# ────────────────────────────────────────────────────────


def charger_metriques(cible: str) -> List[Dict[str, Any]]:
    """
    Charge les métriques φ-complexity pour un fichier ou dossier.

    Args:
        cible: Chemin vers un fichier .py ou un dossier.

    Returns:
        Liste de dictionnaires de métriques (un par fichier).
    """
    from . import auditer

    resultats: List[Dict[str, Any]] = []
    if os.path.isfile(cible):
        resultats.append(auditer(cible))
    elif os.path.isdir(cible):
        for root, _dirs, files in os.walk(cible):
            for f in sorted(files):
                if f.endswith(".py") and not f.startswith("__"):
                    chemin = os.path.join(root, f)
                    try:
                        resultats.append(auditer(chemin))
                    except Exception:
                        pass
    return resultats


def charger_harvest(chemin: str = ".phi/harvest.jsonl") -> List[Dict[str, Any]]:
    """
    Charge un corpus JSONL de harvest.

    Args:
        chemin: Chemin vers le fichier JSONL.

    Returns:
        Liste de dictionnaires de vecteurs φ.
    """
    import json

    vecteurs: List[Dict[str, Any]] = []
    if not os.path.exists(chemin):
        return vecteurs
    with open(chemin, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne:
                vecteurs.append(json.loads(ligne))
    return vecteurs


# ────────────────────────────────────────────────────────
# VISUALISATIONS STANDARD
# ────────────────────────────────────────────────────────


def radar_radiance(metriques: Dict[str, Any], ax: Optional[Any] = None) -> Any:
    """
    Génère un radar chart des métriques de radiance.

    Args:
        metriques: Dictionnaire de métriques d'un fichier.
        ax: Axes matplotlib (créé automatiquement si None).

    Returns:
        L'objet axes matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "matplotlib et numpy requis. "
            "Installez avec : pip install phi-complexity[notebooks]"
        ) from e

    labels = ["Radiance", "Résistance", "1-Lilith", "1-Shannon", "1-φΔ"]
    valeurs = [
        metriques.get("radiance", 0) / 100.0,
        min(1.0, metriques.get("resistance", 0)),
        max(0, 1.0 - metriques.get("lilith_variance", 0) / 1000.0),
        max(0, 1.0 - metriques.get("shannon_entropy", 0) / 10.0),
        max(0, 1.0 - metriques.get("phi_ratio_delta", 0)),
    ]

    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    valeurs_plot = valeurs + [valeurs[0]]
    angles_plot = angles + [angles[0]]

    if ax is None:
        _fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={"projection": "polar"})

    ax.fill(angles_plot, valeurs_plot, color="#FFD700", alpha=0.3)
    ax.plot(angles_plot, valeurs_plot, color="#FFD700", linewidth=2)
    ax.scatter(angles, valeurs, color="#FFD700", s=60, zorder=5)

    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1)

    titre = metriques.get("fichier", "?")
    radiance = metriques.get("radiance", 0)
    ax.set_title(
        f"{os.path.basename(titre)}\nRadiance = {radiance:.1f}", fontsize=11, pad=15
    )

    return ax


def carte_heisenberg(
    metriques_list: List[Dict[str, Any]], ax: Optional[Any] = None
) -> Any:
    """
    Trace la carte d'incertitude Heisenberg-Phi pour une liste de fichiers.

    Args:
        metriques_list: Liste de dictionnaires de métriques.
        ax: Axes matplotlib (créé automatiquement si None).

    Returns:
        L'objet axes matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "matplotlib et numpy requis. "
            "Installez avec : pip install phi-complexity[notebooks]"
        ) from e

    plancher = HBAR_PHI / 2
    sigma_max_sq = PHI**2 * 100
    h_max = math.log2(PHI**4)

    if ax is None:
        _fig, ax = plt.subplots(figsize=(10, 8))

    # Courbe d'incertitude
    dc_curve = np.linspace(0.01, 1.5, 300)
    dl_curve = plancher / dc_curve
    ax.plot(dc_curve, dl_curve, color="#FF6347", linewidth=2, alpha=0.5)
    ax.fill_between(dc_curve, 0, np.minimum(dl_curve, 1.5), alpha=0.08, color="red")

    # Point golden
    golden = math.sqrt(plancher)
    ax.plot(
        golden,
        golden,
        "*",
        color="#FFD700",
        markersize=18,
        zorder=5,
        label="Point Doré",
    )

    # Fichiers
    for m in metriques_list:
        dc = (
            math.sqrt(m["lilith_variance"] / sigma_max_sq)
            if m.get("lilith_variance", 0) > 0
            else 0.01
        )
        dl = min(1.0, m.get("fibonacci_entropy", 0) / h_max) if h_max > 0 else 0.01
        nom = os.path.basename(m.get("fichier", "?"))[:15]
        ax.plot(dc, dl, "o", markersize=8, zorder=5)
        ax.annotate(
            nom, (dc, dl), fontsize=7, textcoords="offset points", xytext=(5, 5)
        )

    ax.set_xlabel("ΔC — Incertitude de Complexité", fontsize=12)
    ax.set_ylabel("ΔL — Incertitude de Lisibilité", fontsize=12)
    ax.set_title(f"Carte Heisenberg-Phi (ħ_φ/2 = {plancher:.4f})", fontsize=13)
    ax.set_xlim(0, 1.5)
    ax.set_ylim(0, 1.5)
    ax.set_aspect("equal")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    return ax


def spirale_doree(radiance: float = 75.0, ax: Optional[Any] = None) -> Any:
    """
    Génère la spirale dorée de Fibonacci (angle 137.5°).

    Args:
        radiance: Score de radiance (contrôle la densité de points).
        ax: Axes matplotlib (créé automatiquement si None).

    Returns:
        L'objet axes matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "matplotlib et numpy requis. "
            "Installez avec : pip install phi-complexity[notebooks]"
        ) from e

    angle_dore = 137.5 * (math.pi / 180)
    n_points = int(50 + radiance * 3)

    indices = np.arange(1, n_points + 1)
    r = np.sqrt(indices)
    theta = indices * angle_dore
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    if ax is None:
        _fig, ax = plt.subplots(figsize=(8, 8))

    cmap = plt.colormaps["magma"]
    colors = cmap(np.linspace(0.15, 0.9, n_points))
    ax.scatter(x, y, c=colors, s=20, alpha=0.85, edgecolors="none")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        f"Spirale Dorée φ (Radiance = {radiance:.1f})\n"
        f"n = {n_points} points — Angle doré 137.5°",
        fontsize=12,
    )

    return ax


# ────────────────────────────────────────────────────────
# MAGIC COMMANDS IPYTHON
# ────────────────────────────────────────────────────────


def enregistrer_magics() -> None:
    """
    Enregistre les magic commands IPython :
        %phi_check <fichier.py>   — Audit rapide avec résumé
        %phi_report <fichier.py>  — Rapport complet console
        %phi_spiral <fichier.py>  — Spirale dorée du fichier

    Ne fait rien si IPython n'est pas disponible (exécution hors notebook).
    """
    try:
        import IPython.core.magic as _ipm  # noqa: PLC0415
    except ImportError:
        return

    # get_ipython is a top-level function in IPython but not always in __all__
    _get_ip: Any = getattr(__import__("IPython"), "get_ipython", None)
    if _get_ip is None:
        return

    ip: Any = _get_ip()
    if ip is None:
        return

    _register: Any = _ipm.register_line_magic

    def _phi_check(line: str) -> None:
        """%phi_check <fichier.py> — Audit rapide."""
        cible = line.strip()
        if not cible:
            print("Usage : %phi_check <fichier.py ou dossier>")
            return
        resultats = charger_metriques(cible)
        if not resultats:
            print(f"Aucun fichier Python trouvé dans : {cible}")
            return
        for m in resultats:
            nom = os.path.basename(m.get("fichier", "?"))
            radiance = m.get("radiance", 0)
            statut = m.get("statut_gnostique", "?")
            phi_r = m.get("phi_ratio", 0)
            print(f"  {nom:25s}  R={radiance:6.1f}  φ={phi_r:.3f}  {statut}")

    def _phi_report(line: str) -> None:
        """%phi_report <fichier.py> — Rapport console complet."""
        cible = line.strip()
        if not cible:
            print("Usage : %phi_report <fichier.py>")
            return
        from . import rapport_console

        print(rapport_console(cible))

    def _phi_spiral(line: str) -> None:
        """%phi_spiral <fichier.py> — Spirale dorée."""
        cible = line.strip()
        if not cible:
            print("Usage : %phi_spiral <fichier.py>")
            return
        try:
            from . import auditer as _auditer

            m = _auditer(cible)
            spirale_doree(m.get("radiance", 75.0))
            try:
                import matplotlib.pyplot as plt

                plt.show()
            except ImportError:
                print("matplotlib requis pour la spirale visuelle.")
        except Exception as e:
            print(f"Erreur : {e}")

    _register(_phi_check)
    _register(_phi_report)
    _register(_phi_spiral)
