"""
phi_complexity/search.py — Phi Search : Recherche Sémantique dans le Vault.

Permet de chercher dans le vault par métriques, statut, catégorie d'annotation,
et par proximité vectorielle (similitude cosinus via les vecteurs harvest).

Phase 18 du Morphic Phi Framework.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List


class PhiSearch:
    """
    Moteur de recherche sémantique pour le Phi Vault.

    Supporte trois modes de recherche :
    1. Par métriques (radiance, entropy, etc.)
    2. Par statut gnostique (HERMÉTIQUE, EN ÉVEIL, DORMANT)
    3. Par proximité vectorielle (similitude cosinus)
    """

    def __init__(self, workspace_root: str = ".") -> None:
        self.phi_dir = os.path.join(workspace_root, ".phi")
        self.vault_index_path = os.path.join(self.phi_dir, "vault", "index.json")
        self.harvest_path = os.path.join(self.phi_dir, "harvest.jsonl")

    def chercher_par_radiance(
        self,
        minimum: float = 0.0,
        maximum: float = 100.0,
    ) -> List[Dict[str, Any]]:
        """Recherche les fichiers dont la radiance est dans l'intervalle donné."""
        index = self._charger_index()
        resultats: List[Dict[str, Any]] = []

        for fichier, info in index.get("notes", {}).items():
            radiance = _to_float(info.get("radiance", 0.0))
            if minimum <= radiance <= maximum:
                resultats.append(
                    {
                        "fichier": fichier,
                        "radiance": radiance,
                        "statut": str(info.get("statut", "")),
                        "note": str(info.get("note", "")),
                    }
                )

        return sorted(resultats, key=lambda x: x["radiance"], reverse=True)

    def chercher_par_statut(self, statut: str) -> List[Dict[str, Any]]:
        """
        Recherche les fichiers par statut gnostique.
        Accepte : 'HERMÉTIQUE', 'EN ÉVEIL', 'DORMANT' (insensible à la casse).
        """
        statut_upper = statut.upper()
        index = self._charger_index()
        resultats: List[Dict[str, Any]] = []

        for fichier, info in index.get("notes", {}).items():
            info_statut = str(info.get("statut", "")).upper()
            if statut_upper in info_statut:
                resultats.append(
                    {
                        "fichier": fichier,
                        "radiance": _to_float(info.get("radiance", 0.0)),
                        "statut": str(info.get("statut", "")),
                        "note": str(info.get("note", "")),
                    }
                )

        return sorted(resultats, key=lambda x: x["radiance"], reverse=True)

    def chercher_par_similarite(
        self, vecteur_cible: List[float], seuil: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Recherche par proximité vectorielle (similitude cosinus)
        dans les vecteurs harvest collectés.
        """
        vecteurs = self._charger_harvest()
        resultats: List[Dict[str, Any]] = []

        for v in vecteurs:
            vecteur_phi = v.get("vecteur_phi", [])
            if not vecteur_phi or len(vecteur_phi) != len(vecteur_cible):
                continue

            sim = _similitude_cosinus(vecteur_cible, vecteur_phi)
            if sim >= seuil:
                resultats.append(
                    {
                        "radiance": _to_float(v.get("radiance", 0.0)),
                        "similarite": round(sim, 4),
                        "lilith_variance": _to_float(v.get("lilith_variance", 0.0)),
                        "shannon_entropy": _to_float(v.get("shannon_entropy", 0.0)),
                        "labels": v.get("labels", {}),
                    }
                )

        return sorted(resultats, key=lambda x: x["similarite"], reverse=True)

    def chercher_annotations(self, categorie: str) -> List[Dict[str, Any]]:
        """
        Recherche les vecteurs harvest ayant des labels d'une catégorie donnée.
        Catégories : LILITH, SUTURE, FIBONACCI, SOUVERAINETE.
        """
        cat_upper = categorie.upper()
        vecteurs = self._charger_harvest()
        resultats: List[Dict[str, Any]] = []

        for v in vecteurs:
            labels = v.get("labels", {})
            count = int(labels.get(cat_upper, 0))
            if count > 0:
                resultats.append(
                    {
                        "radiance": _to_float(v.get("radiance", 0.0)),
                        f"nb_{cat_upper.lower()}": count,
                        "nb_critiques": int(v.get("nb_critiques", 0)),
                        "timestamp": v.get("timestamp", 0),
                    }
                )

        return sorted(resultats, key=lambda x: x["radiance"])

    def chercher_transitions_zero(self, etat: str) -> List[Dict[str, Any]]:
        """
        Recherche les vecteurs harvest par état morphogénétique.
        États : PRE_ZERO, ZERO_CAUSAL, POST_RENAISSANCE.
        """
        etat_upper = etat.upper()
        vecteurs = self._charger_harvest()
        resultats: List[Dict[str, Any]] = []

        for v in vecteurs:
            taxonomie = dict(v.get("taxonomie_transition") or {})
            etat_vecteur = str(
                v.get("zero_morphogenetic_state", taxonomie.get("etat", ""))
            ).upper()
            if etat_vecteur != etat_upper:
                continue
            coherence_raw = v.get(
                "quasicrystal_coherence", taxonomie.get("coherence", 0.0)
            )
            coherence = _to_float(coherence_raw)
            resultats.append(
                {
                    "radiance": _to_float(v.get("radiance", 0.0)),
                    "etat_zero": etat_vecteur,
                    "quasicrystal_state": str(
                        v.get("quasicrystal_state", taxonomie.get("quasicristal", ""))
                    ),
                    "quasicrystal_coherence": coherence,
                    "timestamp": v.get("timestamp", 0),
                }
            )

        return sorted(resultats, key=lambda x: x["radiance"], reverse=True)

    def rapport_recherche(
        self, resultats: List[Dict[str, Any]], titre: str = "Recherche"
    ) -> str:
        """Génère un rapport ASCII des résultats de recherche."""
        if not resultats:
            return f"  ░  Aucun résultat pour : {titre}"

        lignes = [
            "  ╔══════════════════════════════════════════════════╗",
            f"  ║  PHI-SEARCH — {titre:<36}║",
            "  ╚══════════════════════════════════════════════════╝",
            "",
            f"  ◈  {len(resultats)} résultat(s) trouvé(s)",
            "",
        ]

        for i, r in enumerate(resultats[:20]):  # Limite l'affichage à 20
            fichier = r.get("fichier", "")
            radiance = r.get("radiance", 0.0)
            statut = r.get("statut", "")
            sim = r.get("similarite", None)
            etat_zero = r.get("etat_zero", "")
            coherence = r.get("quasicrystal_coherence", None)

            if fichier:
                base = os.path.basename(fichier)
                ligne = f"  [{i+1:>2}] {base:<30} Radiance: {radiance:.1f}"
                if statut:
                    ligne += f"  ({statut})"
            else:
                ligne = f"  [{i+1:>2}] Radiance: {radiance:.1f}"
                if sim is not None:
                    ligne += f"  Similarité: {sim:.4f}"
                if etat_zero:
                    ligne += f"  État: {etat_zero}"
                if coherence is not None:
                    ligne += f"  Cohérence: {_to_float(coherence):.3f}"

            lignes.append(ligne)

        lignes.append("")
        return "\n".join(lignes)

    def _charger_index(self) -> Dict[str, Any]:
        """Charge l'index du vault."""
        if not os.path.exists(self.vault_index_path):
            return {"notes": {}}
        try:
            with open(self.vault_index_path, "r", encoding="utf-8") as f:
                return dict(json.load(f))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"notes": {}}

    def _charger_harvest(self) -> List[Dict[str, Any]]:
        """Charge les vecteurs harvest depuis le fichier JSONL."""
        if not os.path.exists(self.harvest_path):
            return []
        try:
            with open(self.harvest_path, "r", encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        except (json.JSONDecodeError, FileNotFoundError, OSError):
            return []


def _similitude_cosinus(a: List[float], b: List[float]) -> float:
    """Calcule la similitude cosinus entre deux vecteurs."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _to_float(value: Any, default: float = 0.0) -> float:
    """Convertit une valeur quelconque en float de manière sûre."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
