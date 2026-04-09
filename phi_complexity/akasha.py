from __future__ import annotations
import os
import json
import time
import math
from typing import Dict, Any, List, Optional
from .core import PHI

# ────────────────────────────────────────────────────────
# MOTEUR DE MATRICE HOLOGRAPHIQUE BINAIRE (Phidélia v11.6)
# ────────────────────────────────────────────────────────

class MatriceHolographique:
    """
    Transforme un dictionnaire de métriques en résonances harmoniques
    dans l'anneau Z[φ]. (Inspiré de EQ-BIN-010 et EQ-CIA-023).
    """
    
    def __init__(self, donnees: Dict[str, Any]) -> None:
        self.axes = ["radiance", "resistance", "lilith_variance", "shannon_entropy", "phi_ratio"]
        self.valeurs = [float(donnees.get(axe, 0.0)) for axe in self.axes]
        self.vecteur = self._encoder(donnees)

    def _encoder(self, d: Dict[str, Any]) -> List[float]:
        """Convertit les métriques en vecteur normalisé pour la similitude cosinus."""
        v = []
        v.append(float(d.get("radiance", 0)) / 100.0)
        v.append(min(1.0, float(d.get("resistance", 0))))
        v.append(min(1.0, float(d.get("lilith_variance", 0)) / 1000.0))
        v.append(min(1.0, float(d.get("shannon_entropy", 0)) / 10.0))
        v.append(min(1.0, abs(float(d.get("phi_ratio", 0)) - PHI)))
        return v

    def transmuter(self) -> List[Dict[str, float]]:
        """
        Transmutation Maat (EQ-BIN-010) : convertit chaque axe en coordonnée Z[φ].
        a = ⌊val × 1000⌋ (Matière)
        b = ⌊val × 1370⌋ (Phi - Résonance α⁻¹)
        Retourne la résonance (a + bφ) × φ = b + (a+b)φ.
        """
        coords = []
        for val in self.valeurs:
            a = math.floor(val * 1000)
            b = math.floor(val * 1370)
            coords.append({
                "a": float(b),
                "b": float(a + b)
            })
        return coords

    def calculer_masse_harmonique(self) -> float:
        """Calcule la Masse Harmonique M_bit (EQ-BIN-003)."""
        return sum(self.valeurs) / len(self.axes)

    def calculer_coherence(self) -> float:
        """Calcule la Cohérence Interne C_bit (EQ-BIN-005)."""
        stabilite_theo = 1.0 / PHI
        moyenne = sum(v for v in self.valeurs if v > 0) / max(1, len(self.valeurs))
        return (1.0 - abs(moyenne / 100.0 - stabilite_theo)) * 100.0

    def calculer_similitude(self, autre: MatriceHolographique) -> float:
        """Calcule la similitude cosinus entre deux architectures holographiques."""
        dot = sum(a * b for a, b in zip(self.vecteur, autre.vecteur))
        norm_a = math.sqrt(sum(a*a for a in self.vecteur))
        norm_b = math.sqrt(sum(b*b for b in autre.vecteur))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def vers_grille(self) -> str:
        """Exporte la matrice sous forme de dôme de résonance transparent."""
        res = "  AXE            | VALEUR | DÔME DE RÉSONANCE\n"
        res += "  ---------------|--------|------------------\n"
        for i, axe in enumerate(self.axes):
            intensite = "█" * int(self.vecteur[i] * 15)
            res += f"  {axe:<14} | {self.vecteur[i]:.4f} | {intensite}\n"
        return res


class RegistreAkashique:
    """
    Gestionnaire souverain des Annales Akashiques.
    Utilise le moteur de Matrice Holographique pour la navigation temporelle.
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
                json.dump({"annales": [], "version": "11.6"}, f)

    def enregistrer(self, resultat: Dict[str, Any]) -> None:
        """Archive un audit sous forme de signature holographique."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            mat = MatriceHolographique(resultat)
            evenement = {
                "timestamp": time.time(),
                "fichier": resultat.get("fichier", "inconnu"),
                "radiance": resultat.get("radiance", 0),
                "masse_harmonique": round(mat.calculer_masse_harmonique(), 4),
                "coherence_c_bit": round(mat.calculer_coherence(), 2),
                "coords_maat": mat.transmuter(),
                "vecteur": mat.vecteur,
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
        """Retourne les dernières annales."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [dict(e) for e in data.get("annales", [])[-limite:]]
        except Exception:
            return []

    def trouver_similitude(self, dictionnaire_cible: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Recherche par proximité holographique (> 0.98 de gnose)."""
        cible_mat = MatriceHolographique(dictionnaire_cible)
        annales = self.consulter_historique(500)
        
        meilleure_entree = None
        max_sim = 0.98
        
        for entry in annales:
            if "vecteur" not in entry:
                continue
            if entry["fichier"] == dictionnaire_cible.get("fichier"):
                continue
            
            # Reconstruction de la matrice pour comparaison
            pseudo_dict = {axe: val for axe, val in zip(cible_mat.axes, entry["vecteur"])}
            mat_compare = MatriceHolographique(pseudo_dict)
            mat_compare.vecteur = entry["vecteur"]
            
            sim = cible_mat.calculer_similitude(mat_compare)
            if sim > max_sim:
                max_sim = sim
                meilleure_entree = entry
                
        return meilleure_entree
