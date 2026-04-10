"""
phi_complexity/harvest.py — Moteur phi-harvest (Phase 14, Expérimental)
Collecte des vecteurs AST anonymisés pour l'apprentissage IA souverain.

Objectif : détecter les patterns de vulnérabilités (SUTURE, LILITH)
à partir de la géométrie structurelle du code, sans jamais exposer
le code source ni les noms de fichiers.

Format de sortie : JSONL (une ligne JSON par vecteur).
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from .core import PHI

# Facteurs de normalisation pour le vecteur φ
_NORM_RADIANCE: float = 100.0
_NORM_LILITH: float = 1000.0
_NORM_ENTROPIE: float = 10.0


class HarvestEngine:
    """
    Moteur phi-harvest — Collecte de Vecteurs AST Anonymisés.

    Chaque vecteur contient uniquement des métriques structurelles :
    aucun nom de fichier, aucun extrait de code source.
    Les étiquettes de vulnérabilités (LILITH, SUTURE…) servent de labels
    pour l'entraînement supervisé d'un modèle de détection.
    """

    VERSION_SCHEMA: str = "1.0"

    def __init__(self, sortie: str = ".phi/harvest.jsonl") -> None:
        self.sortie = sortie
        self._assurer_dossier()

    def _assurer_dossier(self) -> None:
        """Crée le dossier de sortie s'il n'existe pas."""
        dossier = os.path.dirname(self.sortie)
        if dossier and not os.path.exists(dossier):
            os.makedirs(dossier)

    def collecter(self, fichier: str) -> Dict[str, Any]:
        """
        Extrait un vecteur AST anonymisé depuis un fichier.
        Ne conserve aucun identifiant ni code source.
        """
        from .analyseur import AnalyseurPhi
        from .metriques import CalculateurRadiance

        analyseur = AnalyseurPhi(fichier)
        resultat = analyseur.analyser()
        calc = CalculateurRadiance(resultat)
        metriques = calc.calculer()
        return self._anonymiser(metriques)

    def _anonymiser(self, metriques: Dict[str, Any]) -> Dict[str, Any]:
        """Transforme les métriques en vecteur pur, sans identifiants."""
        annotations: List[Dict[str, Any]] = list(metriques.get("annotations", []))
        categories = [str(a.get("categorie", "")) for a in annotations]
        oudjat: Dict[str, Any] = dict(metriques.get("oudjat") or {})
        return {
            "schema": self.VERSION_SCHEMA,
            "timestamp": int(time.time()),
            # Vecteurs structurels (features)
            "radiance": float(metriques.get("radiance", 0.0)),
            "lilith_variance": float(metriques.get("lilith_variance", 0.0)),
            "shannon_entropy": float(metriques.get("shannon_entropy", 0.0)),
            "phi_ratio": float(metriques.get("phi_ratio", 0.0)),
            "phi_ratio_delta": float(metriques.get("phi_ratio_delta", 0.0)),
            "zeta_score": float(metriques.get("zeta_score", 0.0)),
            "fibonacci_distance": float(metriques.get("fibonacci_distance", 0.0)),
            "resistance": float(metriques.get("resistance", 0.0)),
            # Topologie du code (structure features)
            "nb_fonctions": int(metriques.get("nb_fonctions", 0)),
            "nb_classes": int(metriques.get("nb_classes", 0)),
            "nb_lignes_total": int(metriques.get("nb_lignes_total", 0)),
            "ratio_commentaires": float(metriques.get("ratio_commentaires", 0.0)),
            # Oudjat (dominant function topology)
            "oudjat_complexite": int(oudjat.get("complexite", 0)),
            "oudjat_phi_ratio": float(oudjat.get("phi_ratio", 1.0)),
            # Étiquettes de vulnérabilités (labels pour entraînement supervisé)
            "labels": {
                "LILITH": categories.count("LILITH"),
                "SUTURE": categories.count("SUTURE"),
                "FIBONACCI": categories.count("FIBONACCI"),
                "SOUVERAINETE": categories.count("SOUVERAINETE"),
            },
            "nb_critiques": sum(
                1 for a in annotations if str(a.get("niveau", "")) == "CRITICAL"
            ),
            # Vecteur de résonance Phi (pour clustering)
            "vecteur_phi": self._vecteur_resonance(metriques),
        }

    def _vecteur_resonance(self, m: Dict[str, Any]) -> List[float]:
        """Encode les métriques en vecteur normalisé pour la similitude cosinus."""
        return [
            float(m.get("radiance", 0.0)) / _NORM_RADIANCE,
            min(1.0, float(m.get("lilith_variance", 0.0)) / _NORM_LILITH),
            min(1.0, float(m.get("shannon_entropy", 0.0)) / _NORM_ENTROPIE),
            min(1.0, abs(float(m.get("phi_ratio", 0.0)) - PHI)),
            min(1.0, float(m.get("zeta_score", 0.0))),
        ]

    def exporter(self, vecteur: Dict[str, Any]) -> None:
        """Ajoute le vecteur au fichier JSONL de harvest (append)."""
        try:
            with open(self.sortie, "a", encoding="utf-8") as f:
                f.write(json.dumps(vecteur, ensure_ascii=False) + "\n")
        except OSError as e:
            raise OSError(f"Impossible d'écrire dans {self.sortie}") from e

    def collecter_et_exporter(self, fichier: str) -> Dict[str, Any]:
        """Collecte et exporte en une seule opération atomique."""
        vecteur = self.collecter(fichier)
        self.exporter(vecteur)
        return vecteur

    def compter_vecteurs(self) -> int:
        """Retourne le nombre de vecteurs actuellement collectés."""
        if not os.path.exists(self.sortie):
            return 0
        try:
            with open(self.sortie, "r", encoding="utf-8") as f:
                return sum(1 for ligne in f if ligne.strip())
        except OSError:
            return 0

    def charger_vecteurs(self, limite: int = 100) -> List[Dict[str, Any]]:
        """Charge les derniers vecteurs depuis le fichier JSONL."""
        if not os.path.exists(self.sortie):
            return []
        try:
            with open(self.sortie, "r", encoding="utf-8") as f:
                lignes = [line.strip() for line in f if line.strip()]
            # Utilisation de 'ligne' pour éviter toute ambiguïté
            return [json.loads(ligne) for ligne in lignes][-limite:] if lignes else []
        except (OSError, json.JSONDecodeError):
            return []

    def rapport_harvest(self) -> str:
        """Génère un résumé du corpus de harvest collecté."""
        nb = self.compter_vecteurs()
        vecteurs = self.charger_vecteurs(nb)
        if not vecteurs:
            return "  ░  Corpus harvest vide. Lancez 'phi harvest <fichier>' pour collecter."

        radiancies = [float(v.get("radiance", 0.0)) for v in vecteurs]
        radiance_moy = sum(radiancies) / len(radiancies)
        nb_suture = sum(int(v.get("labels", {}).get("SUTURE", 0)) for v in vecteurs)
        nb_lilith = sum(int(v.get("labels", {}).get("LILITH", 0)) for v in vecteurs)

        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║      PHI-HARVEST — CORPUS IA SOUVERAIN           ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  ◈  Vecteurs collectés   : {nb}",
            f"  ☼  Radiance moyenne     : {radiance_moy:.2f} / 100",
            f"  🌊 Labels SUTURE        : {nb_suture} (fuites de ressources)",
            f"  ⚖  Labels LILITH        : {nb_lilith} (boucles entropiques)",
            f"  📂 Fichier JSONL        : {self.sortie}",
            "",
            "  ─────────────────────────────────────────────────",
            "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
        ]
        return "\n".join(lignes)
