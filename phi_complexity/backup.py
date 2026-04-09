import os
import shutil
import time
from typing import List

class SecuriteMaat:
    """
    Système de Sécurité et de Backup de Phidélia.
    Garantit que l'Auto-Suture ne brise pas l'intention humaine.
    """

    def __init__(self, workspace_root: str = "."):
        self.phi_dir = os.path.join(workspace_root, ".phi")
        self.backup_dir = os.path.join(self.phi_dir, "backups")
        self._initialiser_espace()

    def _initialiser_espace(self) -> None:
        if not os.path.exists(self.phi_dir):
            os.makedirs(self.phi_dir)
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def sauvegarder(self, chemin_fichier: str) -> str:
        """Crée une sauvegarde horodatée du fichier."""
        if not os.path.exists(chemin_fichier):
            return ""
            
        nom_base = os.path.basename(chemin_fichier)
        ts = int(time.time())
        nom_backup = f"{nom_base}.{ts}.bak"
        chemin_backup = os.path.join(self.backup_dir, nom_backup)
        
        shutil.copy2(chemin_fichier, chemin_backup)
        self._purger_anciens_backups(nom_base)
        return chemin_backup

    def restaurer_dernier(self, chemin_fichier: str) -> bool:
        """Restaure la sauvegarde la plus récente pour un fichier donné."""
        nom_base = os.path.basename(chemin_fichier)
        backups = self._lister_backups(nom_base)
        if not backups:
            return False
            
        dernier = os.path.join(self.backup_dir, backups[-1])
        shutil.copy2(dernier, chemin_fichier)
        return True

    def _lister_backups(self, nom_base: str) -> List[str]:
        """Retourne la liste triée des backups pour un fichier."""
        tous = os.listdir(self.backup_dir)
        backups = [f for f in tous if f.startswith(nom_base) and f.endswith(".bak")]
        # Tri par timestamp (partie centrale du nom)
        return sorted(backups)

    def _purger_anciens_backups(self, nom_base: str, limite: int = 10) -> None:
        """Garde seulement les 'limite' derniers backups."""
        backups = self._lister_backups(nom_base)
        if len(backups) > limite:
            pour_suppression = backups[:-limite]
            for f in pour_suppression:
                os.remove(os.path.join(self.backup_dir, f))
