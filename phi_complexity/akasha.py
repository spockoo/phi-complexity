from __future__ import annotations
import os
import json
import time
from typing import Dict, Any, List, Optional

class RegistreAkashique:
    """
    Gestionnaire souverain des Annales Akashiques.
    Enregistre les audits et permet l'apprentissage de forme.
    """
    
    def __init__(self, workspace_root: str = ".") -> None:
        self.phi_dir = os.path.join(workspace_root, ".phi")
        self.db_path = os.path.join(self.phi_dir, "akasha.json")
        self._initialiser_espace()

    def _initialiser_espace(self) -> None:
        """S'assure que le sanctuaire .phi existe."""
        if not os.path.exists(self.phi_dir):
            os.makedirs(self.phi_dir)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({"annales": [], "version": "1.0"}, f)

    def enregistrer(self, resultat: Dict[str, Any]) -> None:
        """Enregistre un événement d'audit dans les annales."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            evenement = {
                "timestamp": time.time(),
                "fichier": resultat.get("fichier", "inconnu"),
                "radiance": resultat.get("radiance", 0),
                "resistance": resultat.get("resistance", 0),
                "pole_alpha": resultat.get("pole_alpha"),
                "pole_omega": resultat.get("pole_omega"),
                "signature": self._generer_signature(resultat)
            }
            
            data["annales"].append(evenement)
            # Limiter à 1000 entrées pour la souveraineté de l'espace
            if len(data["annales"]) > 1000:
                data["annales"] = data["annales"][-1000:]
                
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠ Erreur Akashique : Impossible d'enregistrer l'événement ({e})")

    def _generer_signature(self, r: Dict[str, Any]) -> str:
        """Génère une signature gnostique simplifiée (Variance + Entropie + Phi)."""
        v = r.get("lilith_variance", 0)
        e = r.get("shannon_entropy", 0)
        p = r.get("phi_ratio", 0)
        return f"v{v:.2f}_e{e:.2f}_p{p:.2f}"

    def consulter_historique(self, limite: int = 7) -> List[Dict[str, Any]]:
        """Récupère les derniers événements enregistrés."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data["annales"][-limite:]
        except Exception:
            return []

    def trouver_similitude(self, resultat: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cherche un pattern similaire dans les annales."""
        sig = self._generer_signature(resultat)
        annales = self.consulter_historique(100)
        for entry in reversed(annales):
            if entry["signature"] == sig and entry["fichier"] != resultat.get("fichier"):
                return entry
        return None
