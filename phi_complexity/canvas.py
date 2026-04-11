"""
phi_complexity/canvas.py — Phi Canvas : Export compatible Obsidian Canvas.

Génère un fichier ``.canvas`` (JSON) représentant l'architecture du code audité
avec des nœuds colorés selon le statut gnostique et des arêtes de dépendances.

Phase 17 du Morphic Phi Framework.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from .core import statut_gnostique, PHI


def _generer_id(texte: str) -> str:
    """Génère un identifiant court et déterministe pour un nœud."""
    return hashlib.md5(texte.encode()).hexdigest()[:12]


def _couleur_statut(radiance: float) -> str:
    """Retourne la couleur Obsidian Canvas selon le statut gnostique."""
    statut = statut_gnostique(radiance)
    if "HERMÉTIQUE" in statut:
        return "4"  # Obsidian green
    elif "EN ÉVEIL" in statut:
        return "5"  # Obsidian yellow
    return "1"  # Obsidian red


class PhiCanvas:
    """
    Générateur de Canvas Obsidian (.canvas) pour la visualisation
    de l'architecture du code audité.

    Chaque fichier audité devient un nœud, les fonctions deviennent
    des sous-nœuds, et les dépendances (imports) deviennent des arêtes.
    """

    def __init__(self) -> None:
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self._x_offset = 0
        self._y_offset = 0

    def ajouter_fichier(self, metriques: Dict[str, Any]) -> str:
        """
        Ajoute un fichier audité au canvas comme nœud principal.
        Retourne l'ID du nœud créé.
        """
        fichier = str(metriques.get("fichier", "inconnu"))
        radiance = float(metriques.get("radiance", 0.0))
        statut = statut_gnostique(radiance)
        node_id = _generer_id(fichier)

        texte = (
            f"# {os.path.basename(fichier)}\n"
            f"**Radiance**: {radiance:.1f}\n"
            f"**Statut**: {statut}\n"
            f"**Lignes**: {metriques.get('nb_lignes_total', 0)}"
        )

        self.nodes.append(
            {
                "id": node_id,
                "type": "text",
                "text": texte,
                "x": self._x_offset,
                "y": self._y_offset,
                "width": 300,
                "height": 180,
                "color": _couleur_statut(radiance),
            }
        )

        # Ajouter les fonctions comme sous-nœuds
        fonctions = metriques.get("fonctions", [])
        func_y = self._y_offset + 220
        for i, fn in enumerate(fonctions[:10]):  # Limite à 10 fonctions
            fn_dict = fn if isinstance(fn, dict) else {}
            fn_id = self._ajouter_fonction(
                fn_dict,
                self._x_offset + 350,
                func_y + i * 100,
            )
            # Arête fichier → fonction
            self.edges.append(
                {
                    "id": _generer_id(f"{node_id}-{fn_id}"),
                    "fromNode": node_id,
                    "fromSide": "right",
                    "toNode": fn_id,
                    "toSide": "left",
                }
            )

        self._x_offset += 800
        return node_id

    def _ajouter_fonction(
        self, fn: Dict[str, Any], x: int, y: int
    ) -> str:
        """Ajoute un nœud de fonction au canvas."""
        nom = str(fn.get("nom", "?"))
        complexite = int(fn.get("complexite", 0))
        fn_id = _generer_id(f"fn-{nom}-{fn.get('ligne', 0)}")

        texte = (
            f"**{nom}**\n"
            f"Complexité: {complexite}\n"
            f"Ligne: {fn.get('ligne', '?')}"
        )

        # Couleur basée sur la complexité
        if complexite <= 21:  # Fibonacci(8)
            color = "4"  # vert
        elif complexite <= 55:  # Fibonacci(10)
            color = "5"  # jaune
        else:
            color = "1"  # rouge

        self.nodes.append(
            {
                "id": fn_id,
                "type": "text",
                "text": texte,
                "x": x,
                "y": y,
                "width": 200,
                "height": 80,
                "color": color,
            }
        )
        return fn_id

    def ajouter_dependance(self, source_fichier: str, cible_fichier: str) -> None:
        """Ajoute une arête de dépendance entre deux fichiers."""
        source_id = _generer_id(source_fichier)
        cible_id = _generer_id(cible_fichier)

        self.edges.append(
            {
                "id": _generer_id(f"dep-{source_fichier}-{cible_fichier}"),
                "fromNode": source_id,
                "fromSide": "bottom",
                "toNode": cible_id,
                "toSide": "top",
                "label": "import",
            }
        )

    def exporter(self, chemin: str) -> str:
        """
        Exporte le canvas au format JSON Obsidian Canvas.
        Retourne le contenu JSON.
        """
        canvas = {"nodes": self.nodes, "edges": self.edges}
        contenu = json.dumps(canvas, indent=2, ensure_ascii=False)

        dossier = os.path.dirname(chemin)
        if dossier and not os.path.exists(dossier):
            os.makedirs(dossier)

        with open(chemin, "w", encoding="utf-8") as f:
            f.write(contenu)

        return contenu

    def exporter_json(self) -> str:
        """Retourne le canvas au format JSON sans l'écrire sur disque."""
        canvas = {"nodes": self.nodes, "edges": self.edges}
        return json.dumps(canvas, indent=2, ensure_ascii=False)
