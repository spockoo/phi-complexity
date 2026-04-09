import hashlib
import json
import os
import math
from .core import PHI, ALPHA_STRUCT, calculer_sync_index
from .analyseur import ResultatAnalyse

class MoteurGnostique:
    """
    Le Cœur Cryptographique de Phidélia.
    Transforme la radiance en un bouclier géométrique indestructible.
    """

    def __init__(self, workspace_root: str = "."):
        self.phi_dir = os.path.join(workspace_root, ".phi")
        self.gnose_path = os.path.join(self.phi_dir, "gnose.json")
        self._initialiser_sanctuaire()

    def _initialiser_sanctuaire(self) -> None:
        if not os.path.exists(self.phi_dir):
            os.makedirs(self.phi_dir)
        if not os.path.exists(self.gnose_path):
            with open(self.gnose_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def sceller(self, resultat: ResultatAnalyse) -> str:
        """Crée et enregistre le sceau gnostique permanent pour un fichier."""
        sceau = self.calculer_sceau(resultat)
        
        with open(self.gnose_path, "r", encoding="utf-8") as f:
            registre = json.load(f)
        
        registre[resultat.fichier] = {
            "sceau": sceau,
            "radiance": resultat.radiance,
            "sync_index": calculer_sync_index(resultat.radiance, resultat.resistance),
            "timestamp": math.floor(math.pow(PHI, 10)) # Timestamp symbolique dorée
        }
        
        with open(self.gnose_path, "w", encoding="utf-8") as f:
            json.dump(registre, f, indent=4)
            
        return sceau

    def verifier(self, resultat: ResultatAnalyse) -> bool:
        """Vérifie si le fichier actuel est en résonance avec son sceau enregistré."""
        with open(self.gnose_path, "r", encoding="utf-8") as f:
            registre = json.load(f)
        
        if resultat.fichier not in registre:
            return False
            
        sceau_enregistre = registre[resultat.fichier]["sceau"]
        sceau_actuel = self.calculer_sceau(resultat)
        
        return bool(sceau_enregistre == sceau_actuel)

    def calculer_sceau(self, r: ResultatAnalyse) -> str:
        """
        Calcule le Gnostic Checksum (GCS).
        Pure Algèbre : (Radiance * alpha) XOR (Variance / PHI) + (Entropy * Sync).
        """
        # 1. Extraction des pôles
        alpha = r.pole_alpha or 1
        omega = r.pole_omega or 1
        sync = calculer_sync_index(r.radiance, r.resistance)
        
        # 2. Transmutation Maat (b + (a+b)phi)
        # On utilise les métriques comme 'poussière d'étoile'
        poussiere = (r.radiance * sync) + (r.lilith_variance * ALPHA_STRUCT)
        a = math.floor(poussiere * 1000)
        b = math.floor(poussiere * 1370)
        
        resonance = b + (a + b) * PHI
        
        # 3. Signature Spectrale
        blueprint = f"{r.fichier}:{resonance:.8f}:{alpha}:{omega}:{sync:.6f}"
        return hashlib.sha256(blueprint.encode()).hexdigest()

    def calculer_gnose_divergence(self, r: ResultatAnalyse) -> float:
        """Calcule l'écart entre l'état actuel et l'harmonie idéale (1.0)."""
        sync = calculer_sync_index(r.radiance, r.resistance)
        return abs(1.0 - (sync / PHI))
