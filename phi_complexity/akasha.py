from __future__ import annotations
import os
import json
import time
import math
from typing import Dict, Any, List, Optional, Tuple

class MatriceGnostique:
    """
    Transforme un dictionnaire de métriques (boîte noire) en une matrice
    algébrique transparente et comparable.
    """
    
    def __init__(self, donnees: Dict[str, Any]) -> None:
        self.axes = ["radiance", "resistance", "lilith_variance", "shannon_entropy", "phi_ratio"]
        self.vecteur = self._encoder(donnees)

    def _encoder(self, d: Dict[str, Any]) -> List[float]:
        """Convertit les métriques en vecteur normalisé (0-1)."""
        v = []
        v.append(float(d.get("radiance", 0)) / 100.0)
        v.append(min(1.0, float(d.get("resistance", 0))))
        v.append(min(1.0, float(d.get("lilith_variance", 0)) / 1000.0))
        v.append(min(1.0, float(d.get("shannon_entropy", 0)) / 10.0))
        v.append(min(1.0, abs(float(d.get("phi_ratio", 0)) - 1.618)))
        return v

    def calculer_similitude(self, autre: MatriceGnostique) -> float:
        """Calcule le produit scalaire (similitude cosinus) entre deux matrices."""
        dot = sum(a * b for a, b in zip(self.vecteur, autre.vecteur))
        norm_a = math.sqrt(sum(a*a for a in self.vecteur))
        norm_b = math.sqrt(sum(b*b for b in autre.vecteur))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def vers_grille(self) -> str:
        """Exporte la matrice sous forme de grille transparente auditables."""
        res = "  AXE            | VALEUR | INTENSITÉ\n"
        res += "  ---------------|--------|----------\n"
        for i, axe in enumerate(self.axes):
            intensite = "█" * int(self.vecteur[i] * 10)
            res += f"  {axe:<14} | {self.vecteur[i]:.4f} | {intensite}\n"
        return res


class RegistreAkashique:
    """
    Gestionnaire souverain des Annales Akashiques.
    Utilise le moteur de Matrice Gnostique pour la recherche de formes.
    """
    
    def __init__(self, workspace_root: str = ".") -> None:
        self.phi_dir = os.path.join(workspace_root, ".phi")
        self.db_path = os.path.join(self.phi_dir, "akasha.json")
        self._initialiser_espace()

    def _initialiser_espace(self) -> None:
        if not os.path.exists(self.phi_dir):
            os.makedirs(self.phi_dir)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({"annales": [], "version": "1.1"}, f)

    def enregistrer(self, resultat: Dict[str, Any]) -> None:
        """Enregistre un événement filtré par la matrice gnostique."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            evenement = {
                "timestamp": time.time(),
                "fichier": resultat.get("fichier", "inconnu"),
                "radiance": resultat.get("radiance", 0),
                "resistance": resultat.get("resistance", 0),
                "vecteur": MatriceGnostique(resultat).vecteur,
                "signature": resultat.get("signature", "")
            }
            
            data["annales"].append(evenement)
            if len(data["annales"]) > 1000:
                data["annales"] = data["annales"][-1000:]
                
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def consulter_historique(self, limite: int = 7) -> List[Dict[str, Any]]:
        """Retourne les dernières entrées (garanti type List[Dict])."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            annales = data.get("annales", [])
            if not isinstance(annales, list):
                return []
            # Conversion explicite pour MyPy
            return [dict(e) for e in annales[-limite:]]
        except Exception:
            return []

    def trouver_similitude(self, dictionnaire_cible: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Recherche par proximité matricielle (> 0.98 de similitude)."""
        cible_mat = MatriceGnostique(dictionnaire_cible)
        annales = self.consulter_historique(500)
        
        meilleure_entree = None
        max_sim = 0.98
        
        for entry in annales:
            if "vecteur" not in entry:
                continue
            if entry["fichier"] == dictionnaire_cible.get("fichier"):
                continue
            
            # Reconstruction de la matrice pour comparaison
            # On simule un dictionnaire pour l'initialisation (via axes)
            pseudo_dict = {axe: val for axe, val in zip(cible_mat.axes, entry["vecteur"])}
            mat_compare = MatriceGnostique(pseudo_dict)
            mat_compare.vecteur = entry["vecteur"] # Injection directe pour précision
            
            sim = cible_mat.calculer_similitude(mat_compare)
            if sim > max_sim:
                max_sim = sim
                meilleure_entree = entry
                
        return meilleure_entree
