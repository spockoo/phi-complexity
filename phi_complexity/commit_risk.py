"""
phi_complexity/commit_risk.py — Analyse Bayésienne du Risque de Commit (Phase B)

Modèle Bayésien Naïf pour estimer la probabilité qu'un commit représente un risque
pour la stabilité ou la sécurité du projet.

Formule :
    P(risque | features) ∝ P(risque) · ∏ P(feature_i | risque)

Facteurs analysés :
    - Taille du diff (lignes ajoutées / supprimées)
    - Nombre de fichiers modifiés
    - Chemins sensibles (.github/, *.yml, *.cfg, setup.*, *.key, etc.)
    - Densité de mots-clés suspects dans le message de commit
    - Heure du commit (hors heures ouvrées → risque légèrement plus élevé)
    - Fichiers binaires modifiés
    - Modifications de fichiers de configuration de sécurité

Niveaux de risque :
    - FAIBLE    : score < 0.30
    - MODÉRÉ    : 0.30 ≤ score < 0.60
    - ÉLEVÉ     : 0.60 ≤ score < 0.80
    - CRITIQUE  : score ≥ 0.80

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────
# CONSTANTES DU MODÈLE BAYÉSIEN
# ──────────────────────────────────────────────

# Probabilité a priori : taux de base de risque estimé sur un commit quelconque
_PRIOR_RISQUE: float = 0.15

# Seuils de classification du risque
_SEUIL_FAIBLE: float = 0.30
_SEUIL_MODERE: float = 0.60
_SEUIL_ELEVE: float = 0.80

# Chemins sensibles — modifications qui augmentent le risque
_CHEMINS_SENSIBLES: Tuple[str, ...] = (
    ".github/",
    ".env",
    "*.key",
    "*.pem",
    "*.p12",
    "requirements",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "Makefile",
    "Dockerfile",
    "docker-compose",
    "SECURITY",
    "secrets",
    "credentials",
    "password",
    "token",
    "auth",
)

# Mots-clés suspects dans les messages de commit
_MOTS_SUSPECTS: Tuple[str, ...] = (
    "bypass",
    "disable",
    "remove check",
    "skip ci",
    "force push",
    "override",
    "hack",
    "workaround",
    "temporary",
    "fixme",
    "xxx",
    "password",
    "secret",
    "credential",
    "token",
    "disable security",
    "remove auth",
    "no verify",
    "--force",
    "rm -rf",
    "eval(",
    "exec(",
)

# Heures hors période ouvrable standard (heure locale du commit)
_HEURES_HORS_BUREAU: Tuple[int, ...] = tuple(range(0, 6)) + tuple(range(22, 24))


# ──────────────────────────────────────────────
# STRUCTURES DE DONNÉES
# ──────────────────────────────────────────────


@dataclass
class FeaturesCommit:
    """Vecteur de features extraites d'un commit git."""

    sha: str = ""
    message: str = ""
    auteur: str = ""
    heure: int = 12  # heure UTC du commit (0-23)
    lignes_ajoutees: int = 0
    lignes_supprimees: int = 0
    fichiers_changes: int = 0
    chemins_sensibles: int = 0  # nombre de fichiers touchant des chemins sensibles
    mots_suspects_count: int = 0  # occurences de mots-clés suspects
    fichiers_binaires: int = 0
    hors_heures_bureau: bool = False
    est_weekend: bool = False


@dataclass
class RapportRisque:
    """Résultat complet de l'analyse bayésienne d'un commit."""

    sha: str
    score: float  # [0.0, 1.0]
    niveau: str  # FAIBLE | MODÉRÉ | ÉLEVÉ | CRITIQUE
    facteurs_dominants: List[str] = field(default_factory=list)
    features: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise le rapport en dictionnaire JSON-compatible."""
        return {
            "sha": self.sha,
            "score": round(self.score, 4),
            "niveau": self.niveau,
            "facteurs_dominants": self.facteurs_dominants,
            "features": self.features or {},
            "details": self.details or {},
        }


# ──────────────────────────────────────────────
# EXTRACTION DES FEATURES
# ──────────────────────────────────────────────


def _run_git(args: List[str], cwd: Optional[str] = None) -> str:
    """Exécute une commande git et retourne stdout. Silencieux en cas d'erreur."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd or os.getcwd(),
            timeout=30,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError, subprocess.TimeoutExpired):
        return ""


def _est_chemin_sensible(chemin: str) -> bool:
    """Retourne True si le chemin correspond à un pattern sensible."""
    chemin_lower = chemin.lower()
    for pattern in _CHEMINS_SENSIBLES:
        # Pattern glob simple (suffix ou préfixe ou contenu) — insensible à la casse
        pattern_lower = pattern.lower()
        if pattern_lower.startswith("*"):
            if chemin_lower.endswith(pattern_lower[1:]):
                return True
        elif pattern_lower in chemin_lower:
            return True
    return False


def _compter_mots_suspects(texte: str) -> int:
    """Compte les occurrences de mots-clés suspects dans un texte."""
    texte_lower = texte.lower()
    return sum(1 for mot in _MOTS_SUSPECTS if mot in texte_lower)


def extraire_features(sha: str, cwd: Optional[str] = None) -> FeaturesCommit:
    """
    Extrait le vecteur de features d'un commit git par son SHA.

    Args:
        sha: Le SHA du commit à analyser.
        cwd: Répertoire de travail du dépôt git (défaut: CWD).

    Returns:
        FeaturesCommit rempli avec les données extraites.
    """
    features = FeaturesCommit(sha=sha)

    # Message du commit
    features.message = _run_git(["log", "-1", "--format=%s", sha], cwd)

    # Auteur
    features.auteur = _run_git(["log", "-1", "--format=%an", sha], cwd)

    # Horodatage (heure UTC)
    timestamp_str = _run_git(["log", "-1", "--format=%ai", sha], cwd)
    if timestamp_str:
        try:
            # Format: "2024-01-15 14:30:00 +0200"
            heure_part = timestamp_str.split()[1] if " " in timestamp_str else ""
            features.heure = int(heure_part.split(":")[0]) if ":" in heure_part else 12
        except (IndexError, ValueError):
            features.heure = 12

    # Jour de la semaine (0=lundi, 6=dimanche)
    jour_str = _run_git(["log", "-1", "--format=%ad", "--date=format:%w", sha], cwd)
    try:
        jour = int(jour_str)
        features.est_weekend = jour in (0, 6)  # dimanche=0, samedi=6 selon %w
    except (ValueError, TypeError):
        features.est_weekend = False

    # Hors heures bureau
    features.hors_heures_bureau = features.heure in _HEURES_HORS_BUREAU

    # Stats du diff (lignes ajoutées/supprimées)
    numstat = _run_git(["diff", "--numstat", f"{sha}^..{sha}"], cwd)
    if not numstat:
        # Premier commit sans parent
        numstat = _run_git(["diff", "--numstat", sha], cwd)

    lignes = [l for l in numstat.splitlines() if l.strip()]
    features.fichiers_changes = len(lignes)

    for ligne in lignes:
        parties = ligne.split("\t")
        if len(parties) >= 3:
            fichier = parties[2]
            # Détecter les fichiers binaires (représentés par "-" dans numstat)
            if parties[0] == "-" and parties[1] == "-":
                features.fichiers_binaires += 1
                continue
            try:
                features.lignes_ajoutees += int(parties[0])
                features.lignes_supprimees += int(parties[1])
            except ValueError:
                pass
            if _est_chemin_sensible(fichier):
                features.chemins_sensibles += 1

    # Mots suspects dans le message
    features.mots_suspects_count = _compter_mots_suspects(features.message)

    return features


# ──────────────────────────────────────────────
# MODÈLE BAYÉSIEN
# ──────────────────────────────────────────────


def _ratio_de_vraisemblance(feature_value: float, mu_risque: float, mu_safe: float) -> float:
    """
    Calcule le ratio de vraisemblance L = P(feature | risque) / P(feature | safe)
    en utilisant une approximation log-normale simplifiée.

    Pour les features continues, on modélise la probabilité par une sigmoïde
    centrée sur la valeur normalisée pour obtenir un rapport compact.
    """
    if mu_safe == 0.0:
        return 1.0
    return mu_risque / mu_safe


def scorer_commit(features: FeaturesCommit) -> Tuple[float, Dict[str, float]]:
    """
    Calcule le score de risque bayésien pour un vecteur de features.

    Implémentation du Bayésien Naïf :
        log P(risque | X) = log P(risque) + Σ log P(x_i | risque) - log P(x_i)

    Retourne:
        (score, dict des contributions individuelles)
    """
    details: Dict[str, float] = {}

    # Log-prior
    log_posterior = math.log(_PRIOR_RISQUE / (1.0 - _PRIOR_RISQUE))

    # ── Feature: taille du diff ──────────────────────────────────────────
    diff_total = features.lignes_ajoutees + features.lignes_supprimees
    # Risque croît avec la taille (100 lignes = risque modéré, 500+ = risque élevé)
    contribution_diff = min(1.0, diff_total / 500.0) * 0.8
    log_posterior += math.log(1.0 + contribution_diff)
    details["diff_size"] = contribution_diff

    # ── Feature: fichiers modifiés ────────────────────────────────────────
    # Beaucoup de fichiers = risque d'effet de bord non anticipé
    contribution_fichiers = min(1.0, features.fichiers_changes / 20.0) * 0.5
    log_posterior += math.log(1.0 + contribution_fichiers)
    details["fichiers_changes"] = contribution_fichiers

    # ── Feature: chemins sensibles ────────────────────────────────────────
    # Chaque chemin sensible touché augmente significativement le risque
    contribution_sensible = min(1.0, features.chemins_sensibles * 0.25) * 2.0
    log_posterior += math.log(1.0 + contribution_sensible)
    details["chemins_sensibles"] = contribution_sensible

    # ── Feature: mots suspects ────────────────────────────────────────────
    contribution_suspects = min(1.0, features.mots_suspects_count * 0.20) * 1.5
    log_posterior += math.log(1.0 + contribution_suspects)
    details["mots_suspects"] = contribution_suspects

    # ── Feature: fichiers binaires ────────────────────────────────────────
    contribution_binaires = min(1.0, features.fichiers_binaires * 0.30) * 1.0
    log_posterior += math.log(1.0 + contribution_binaires)
    details["fichiers_binaires"] = contribution_binaires

    # ── Feature: hors heures bureau ───────────────────────────────────────
    contribution_horaire = 0.15 if features.hors_heures_bureau else 0.0
    log_posterior += math.log(1.0 + contribution_horaire)
    details["hors_heures_bureau"] = contribution_horaire

    # ── Feature: weekend ─────────────────────────────────────────────────
    contribution_weekend = 0.10 if features.est_weekend else 0.0
    log_posterior += math.log(1.0 + contribution_weekend)
    details["weekend"] = contribution_weekend

    # Transformation sigmoïde pour ramener dans [0, 1]
    score = 1.0 / (1.0 + math.exp(-log_posterior))
    return float(score), details


def _classifier_niveau(score: float) -> str:
    """Retourne le niveau de risque textuel selon le score."""
    if score < _SEUIL_FAIBLE:
        return "FAIBLE"
    if score < _SEUIL_MODERE:
        return "MODÉRÉ"
    if score < _SEUIL_ELEVE:
        return "ÉLEVÉ"
    return "CRITIQUE"


def _identifier_facteurs_dominants(
    features: FeaturesCommit, details: Dict[str, float], seuil: float = 0.20
) -> List[str]:
    """Identifie les facteurs les plus contributeurs au score de risque."""
    facteurs: List[str] = []

    diff_total = features.lignes_ajoutees + features.lignes_supprimees
    if details.get("diff_size", 0.0) >= seuil:
        facteurs.append(f"Diff volumineux : {diff_total} lignes modifiées")

    if details.get("fichiers_changes", 0.0) >= seuil:
        facteurs.append(f"Nombreux fichiers modifiés : {features.fichiers_changes}")

    if details.get("chemins_sensibles", 0.0) >= seuil:
        facteurs.append(
            f"Fichiers sensibles modifiés : {features.chemins_sensibles} chemin(s)"
        )

    if details.get("mots_suspects", 0.0) >= seuil:
        facteurs.append(
            f"Mots suspects dans le message : {features.mots_suspects_count} occurrence(s)"
        )

    if details.get("fichiers_binaires", 0.0) >= seuil:
        facteurs.append(f"Fichiers binaires modifiés : {features.fichiers_binaires}")

    if features.hors_heures_bureau:
        facteurs.append(f"Commit hors heures ouvrées : {features.heure}h UTC")

    if features.est_weekend:
        facteurs.append("Commit le week-end")

    return facteurs


# ──────────────────────────────────────────────
# POINT D'ENTRÉE PRINCIPAL
# ──────────────────────────────────────────────


def analyser_commit(sha: str, cwd: Optional[str] = None) -> RapportRisque:
    """
    Analyse complète d'un commit : extraction des features → score bayésien → rapport.

    Args:
        sha: SHA du commit à analyser.
        cwd: Répertoire git (défaut: CWD).

    Returns:
        RapportRisque avec score, niveau et facteurs dominants.
    """
    features = extraire_features(sha, cwd)
    score, details = scorer_commit(features)
    niveau = _classifier_niveau(score)
    facteurs = _identifier_facteurs_dominants(features, details)

    return RapportRisque(
        sha=sha,
        score=score,
        niveau=niveau,
        facteurs_dominants=facteurs,
        features={
            "message": features.message,
            "auteur": features.auteur,
            "heure": features.heure,
            "lignes_ajoutees": features.lignes_ajoutees,
            "lignes_supprimees": features.lignes_supprimees,
            "fichiers_changes": features.fichiers_changes,
            "chemins_sensibles": features.chemins_sensibles,
            "mots_suspects_count": features.mots_suspects_count,
            "fichiers_binaires": features.fichiers_binaires,
            "hors_heures_bureau": features.hors_heures_bureau,
            "est_weekend": features.est_weekend,
        },
        details=details,
    )


def rapport_console(rapport: RapportRisque) -> str:
    """Génère le rapport ASCII formaté pour le terminal."""
    score_pct = rapport.score * 100
    symbole_niveau = {
        "FAIBLE": "✅",
        "MODÉRÉ": "⚠️ ",
        "ÉLEVÉ": "🔴",
        "CRITIQUE": "🚨",
    }.get(rapport.niveau, "❓")

    barre_len = 30
    rempli = int(score_pct / 100 * barre_len)
    barre = "█" * rempli + "░" * (barre_len - rempli)

    lignes = [
        "╔══════════════════════════════════════════════════╗",
        "║   PHI-SENTINEL — ANALYSE DE RISQUE BAYÉSIEN      ║",
        "╚══════════════════════════════════════════════════╝",
        "",
        f"  SHA      : {rapport.sha[:16]}...",
        f"  Score    : [{barre}] {score_pct:.1f}%",
        f"  Niveau   : {symbole_niveau}  {rapport.niveau}",
        "",
    ]

    if rapport.facteurs_dominants:
        lignes.append("  Facteurs dominants :")
        for facteur in rapport.facteurs_dominants:
            lignes.append(f"    ◈  {facteur}")
    else:
        lignes.append("  ✦  Aucun facteur de risque élevé détecté.")

    lignes += [
        "",
        "  ─────────────────────────────────────────────────",
        "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
    ]
    return "\n".join(lignes)


# ──────────────────────────────────────────────
# CLI (python -m phi_complexity.commit_risk)
# ──────────────────────────────────────────────


def main(argv: Optional[List[str]] = None) -> int:
    """Point d'entrée CLI pour le scorer de risque de commit."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="phi-commit-risk",
        description="Analyse bayésienne du risque d'un commit git.",
    )
    parser.add_argument("--sha", required=True, help="SHA du commit à analyser")
    parser.add_argument(
        "--output",
        default=None,
        help="Fichier de sortie JSON (défaut: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "console"],
        default="console",
        help="Format de sortie (défaut: console)",
    )

    args = parser.parse_args(argv)

    rapport = analyser_commit(args.sha)

    if args.format == "json" or args.output:
        contenu = json.dumps(rapport.to_dict(), ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(contenu)
            print(f"Rapport écrit dans : {args.output}")
        else:
            print(contenu)
    else:
        print(rapport_console(rapport))

    return 0


if __name__ == "__main__":
    sys.exit(main())
