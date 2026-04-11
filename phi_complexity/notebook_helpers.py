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

    def _phi_sentinel(line: str) -> None:
        """%phi_sentinel [dossier] — Diagnostic de sécurité Sentinel."""
        cible = line.strip() or "."
        rapport = diagnostic_systeme(cible_code=cible if cible != "." else None)
        print(rapport["rapport_console"])

    _register(_phi_check)
    _register(_phi_report)
    _register(_phi_spiral)
    _register(_phi_sentinel)


# ────────────────────────────────────────────────────────
# DIAGNOSTIC CYBERSÉCURITÉ (Sentinel + Quasicristaux)
# ────────────────────────────────────────────────────────


def diagnostic_systeme(
    cible_code: Optional[str] = None,
    score_commit: float = 0.0,
) -> Dict[str, Any]:
    """
    Exécute un diagnostic de sécurité complet depuis Jupyter.

    Pipeline Sentinel intégral :
        HostCollector → TelemetryNormalizer → BehaviorAnalyzer
        → BayesianCorrelator → SentinelResponse

    Si *cible_code* est fourni, les métriques φ du code sont croisées
    avec les signaux système pour enrichir le rapport.

    Args:
        cible_code   : Chemin vers un fichier/dossier Python à auditer.
        score_commit : Score de risque commit externe [0, 1].

    Returns:
        Dictionnaire avec toutes les couches décomposées :
        events, traces, signaux, score, alertes, rapport_console, metriques.
    """
    from .sentinel import (
        HostCollector,
        TelemetryNormalizer,
        BehaviorAnalyzer,
        BayesianCorrelator,
        SentinelResponse,
    )

    # Couche 1 — Collecte
    collector = HostCollector()
    events = collector.collecter_tout()

    # Couche 2 — Normalisation
    normalizer = TelemetryNormalizer()
    traces = normalizer.normaliser(events)
    stats_tel = normalizer.statistiques(traces)

    # Couche 3 — Comportements
    analyzer = BehaviorAnalyzer()
    signaux = analyzer.analyser(traces)

    # Couche 4 — Corrélation bayésienne
    correlator = BayesianCorrelator()
    score = correlator.calculer_score(
        signaux=signaux,
        traces=traces,
        score_commit=score_commit,
    )

    # Couche 5 — Réponse
    responder = SentinelResponse()
    alertes = responder.generer_alertes(score, signaux)
    rapport_txt = correlator.rapport_correlation(score)

    # Métriques φ optionnelles
    metriques: List[Dict[str, Any]] = []
    if cible_code:
        metriques = charger_metriques(cible_code)

    return {
        "events": events,
        "traces": traces,
        "stats_telemetrie": stats_tel,
        "signaux": signaux,
        "score": score,
        "alertes": alertes,
        "rapport_console": rapport_txt,
        "metriques": metriques,
        "politique": responder.politique_de_reponse(alertes),
    }


def radar_menaces(
    signaux_ou_diagnostic: Any,
    ax: Optional[Any] = None,
) -> Any:
    """
    Génère un radar chart des menaces détectées (MITRE ATT&CK).

    Args:
        signaux_ou_diagnostic : Liste de SignalComportemental ou dict
                                retourné par diagnostic_systeme().
        ax : Axes matplotlib (créé automatiquement si None).

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

    # Accepte soit la liste directe soit le dict de diagnostic
    if isinstance(signaux_ou_diagnostic, dict):
        signaux = signaux_ou_diagnostic.get("signaux", [])
    else:
        signaux = signaux_ou_diagnostic

    categories = [
        "PERSISTANCE",
        "ELEVATION",
        "EXFILTRATION",
        "CHIFFREMENT",
        "C2",
        "RECONNAISSANCE",
        "MOUVEMENT_LAT",
        "DEFENCE_EVASION",
        "INJECTION",
        "ACCES_CREDENTIAL",
    ]

    # Remplir les confiances par catégorie
    confiances: Dict[str, float] = {c: 0.0 for c in categories}
    for signal in signaux:
        nom = signal.type.value.upper()
        if nom in confiances:
            confiances[nom] = max(confiances[nom], signal.confiance)

    valeurs = [confiances[c] for c in categories]

    n = len(categories)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    valeurs_plot = valeurs + [valeurs[0]]
    angles_plot = angles + [angles[0]]

    if ax is None:
        _fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})

    ax.fill(angles_plot, valeurs_plot, color="#FF4136", alpha=0.25)
    ax.plot(angles_plot, valeurs_plot, color="#FF4136", linewidth=2)
    ax.scatter(angles, valeurs, color="#FF4136", s=60, zorder=5)

    # Seuils visuels
    theta_full = np.linspace(0, 2 * np.pi, 100)
    ax.plot(theta_full, [0.70] * 100, "--", color="orange", alpha=0.5, linewidth=1)
    ax.plot(theta_full, [0.40] * 100, "--", color="green", alpha=0.4, linewidth=1)

    labels_courts = [c[:12] for c in categories]
    ax.set_xticks(angles)
    ax.set_xticklabels(labels_courts, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_title("Radar MITRE ATT&CK — Menaces Détectées", fontsize=12, pad=20)

    return ax


def carte_entropie_penrose(
    metriques_list: List[Dict[str, Any]],
    ax: Optional[Any] = None,
) -> Any:
    """
    Carte d'entropie inspirée des pavages de Penrose (quasicristaux).

    Chaque fichier est placé dans un espace 2D (radiance × entropie)
    et coloré selon son score φ. Les zones d'anomalie sont identifiées
    par les frontières de Penrose : là où l'ordre apériodique se brise,
    le code présente un risque de dissimulation de complexité.

    Principe quasicristallin : un système sain présente un ordre
    apériodique (φ-cohérent) ; les outliers signalent des zones
    où la complexité est dissimulée dans les données.

    Args:
        metriques_list : Liste de métriques (de charger_metriques ou diagnostic).
        ax : Axes matplotlib.

    Returns:
        L'objet axes matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError(
            "matplotlib requis. "
            "Installez avec : pip install phi-complexity[notebooks]"
        ) from e

    if ax is None:
        _fig, ax = plt.subplots(figsize=(10, 8))

    if not metriques_list:
        ax.text(
            0.5,
            0.5,
            "Aucune métrique à afficher",
            ha="center",
            va="center",
            fontsize=14,
        )
        return ax

    # Extraire les coordonnées
    radiances = [m.get("radiance", 60.0) for m in metriques_list]
    entropies = [m.get("fibonacci_entropy", 0.0) for m in metriques_list]
    phi_deltas = [m.get("phi_ratio_delta", 0.0) for m in metriques_list]
    max_label_len = 15  # Tronquer les noms pour la lisibilité des annotations
    noms = [
        os.path.basename(m.get("fichier", "?"))[:max_label_len] for m in metriques_list
    ]

    # Normaliser les couleurs par phi_ratio_delta
    max_delta = max(phi_deltas) if phi_deltas and max(phi_deltas) > 0 else 1.0
    couleurs_norm = [d / max_delta for d in phi_deltas]

    # Grille de Penrose (angle doré 36°)
    angle_penrose = math.radians(36)
    for k in range(10):
        theta = k * angle_penrose
        longueur = max(max(radiances) if radiances else 100, 100)
        ax.plot(
            [50 - longueur * math.cos(theta), 50 + longueur * math.cos(theta)],
            [0 - longueur * math.sin(theta), 0 + longueur * math.sin(theta)],
            color="#FFD700",
            alpha=0.15,
            linewidth=1,
        )

    # Frontière φ (seuil Heisenberg-Phi)
    plancher = HBAR_PHI / 2
    seuil_entropie = math.log2(PHI**4) if PHI > 1 else 1.0
    ax.axhline(
        y=seuil_entropie,
        color="red",
        alpha=0.3,
        linestyle="--",
        label=f"H_max = log₂(φ⁴) ≈ {seuil_entropie:.2f}",
    )
    ax.axvline(
        x=60,
        color="orange",
        alpha=0.3,
        linestyle="--",
        label="Seuil Radiance Éveil",
    )
    ax.axvline(
        x=85,
        color="green",
        alpha=0.3,
        linestyle="--",
        label="Seuil Radiance Hermétique",
    )

    # Scatter plot
    cmap = plt.colormaps["RdYlGn_r"]
    sc = ax.scatter(
        radiances,
        entropies,
        c=couleurs_norm,
        cmap=cmap,
        s=80,
        edgecolors="black",
        linewidth=0.5,
        zorder=5,
    )
    plt.colorbar(sc, ax=ax, label="Δφ (écart au nombre d'or)", shrink=0.8)

    # Annotations
    for nom, rad, ent in zip(noms, radiances, entropies):
        ax.annotate(
            nom,
            (rad, ent),
            fontsize=7,
            textcoords="offset points",
            xytext=(5, 5),
            alpha=0.8,
        )

    ax.set_xlabel("Radiance (score φ-complexity)", fontsize=11)
    ax.set_ylabel("Entropie Fibonacci (H_F)", fontsize=11)
    ax.set_title(
        "Carte d'Entropie Penrose — Détection d'Anomalies\n"
        f"(ħ_φ/2 = {plancher:.4f} — seuil quasicristallin)",
        fontsize=12,
    )
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.2)

    return ax


def tableau_diagnostic(
    diagnostic: Dict[str, Any],
) -> str:
    """
    Génère un tableau ASCII lisible du diagnostic Sentinel complet.

    Args:
        diagnostic : Dictionnaire retourné par diagnostic_systeme().

    Returns:
        Rapport formaté en texte.
    """
    score = diagnostic.get("score")
    stats = diagnostic.get("stats_telemetrie", {})
    alertes = diagnostic.get("alertes", [])
    signaux = diagnostic.get("signaux", [])
    politique = diagnostic.get("politique", {})

    lignes = [
        "╔══════════════════════════════════════════════════════════╗",
        "║   PHI-SENTINEL — DIAGNOSTIC SYSTÈME COMPLET (NOTEBOOK)  ║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
    ]

    if score is not None:
        pct = score.score_final * 100
        symbole = {
            "FAIBLE": "✅",
            "MODÉRÉ": "⚠️ ",
            "ÉLEVÉ": "🔴",
            "CRITIQUE": "🚨",
        }.get(score.niveau, "❓")
        barre_len = 40
        rempli = int(pct / 100 * barre_len)
        barre = "█" * rempli + "░" * (barre_len - rempli)
        lignes += [
            f"  Score Global : [{barre}] {pct:.1f}%",
            f"  Niveau       : {symbole}  {score.niveau}",
            "",
            "  Décomposition :",
            f"    ◈  OS Comportemental  : {score.score_os * 100:.1f}%",
            f"    ◈  Risque Commit      : {score.score_commit * 100:.1f}%",
            f"    ◈  Télémétrie         : {score.score_telemetrie * 100:.1f}%",
            "",
        ]

    lignes += [
        "  Télémétrie :",
        f"    Total traces   : {stats.get('total', 0)}",
        f"    INFO           : {stats.get('info', 0)}",
        f"    ATTENTION      : {stats.get('attention', 0)}",
        f"    SUSPECT        : {stats.get('suspect', 0)}",
        f"    CRITIQUE       : {stats.get('critique', 0)}",
        "",
    ]

    if signaux:
        lignes.append(f"  Signaux MITRE ATT&CK ({len(signaux)}) :")
        for s in signaux[:5]:
            mitre = f" [{s.mitre_technique}]" if s.mitre_technique else ""
            lignes.append(
                f"    ◈  {s.type.value.upper():20s}  "
                f"{s.confiance * 100:5.1f}%{mitre}"
            )
    else:
        lignes.append("  ✦  Aucun signal comportemental suspect.")

    lignes.append("")

    if alertes:
        lignes.append(f"  Alertes ({len(alertes)}) :")
        for a in alertes[:5]:
            lignes.append(f"    🔔  [{a.niveau.value.upper()}] {a.titre}")
    else:
        lignes.append("  ✦  Aucune alerte active.")

    lignes.append("")

    if politique:
        actions_str = []
        if politique.get("bloquer_pr"):
            actions_str.append("BLOQUER PR")
        if politique.get("escalader"):
            actions_str.append("ESCALADER")
        if politique.get("isoler"):
            actions_str.append("ISOLER")
        if politique.get("notifier"):
            actions_str.append("NOTIFIER")
        if actions_str:
            lignes.append(f"  Actions recommandées : {' | '.join(actions_str)}")
        else:
            lignes.append("  Actions recommandées : LOG_ONLY")

    lignes += [
        "",
        "  ─────────────────────────────────────────────────────────",
        "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
    ]
    return "\n".join(lignes)
