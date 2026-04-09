import re
from typing import Optional
from .analyseur import AnalyseurPhi
from .suture import SutureAgent
from .backup import SecuriteMaat
from .core import calculer_sync_index

class AutoSuture:
    """
    Le Guérisseur de Phidélia (Phase 12).
    Orchestre l'auto-réparation souveraine du code.
    """

    def __init__(self, api_url: Optional[str] = None):
        self.agent = SutureAgent(api_url) if api_url else SutureAgent()
        self.securite = SecuriteMaat()

    def guerir(self, fichier: str, force: bool = False) -> str:
        """
        Tente de soigner un fichier en améliorant son Sync_index.
        """
        # 1. État des lieux (Avant)
        analyseur = AnalyseurPhi(fichier)
        r_avant = analyseur.analyser()
        sync_avant = calculer_sync_index(r_avant.radiance, r_avant.resistance)
        
        if r_avant.radiance >= 85 and not force:
             return f"RÉSONANCE STABLE ({r_avant.radiance:.1f}) : Aucune guérison requise."

        # 2. Sécurité Maât (Backup)
        self.securite.sauvegarder(fichier)
        
        # 3. Invocation du Conseil des 12
        reponse_ia = self.agent.suturer(r_avant)
        nouveau_code = self._extraire_code(reponse_ia)
        
        if not nouveau_code:
            return "ÉCHEC DE SUTURE : Phidélia n'a pas renvoyé de code valide."

        # 4. Injection (Suture Physique)
        # Pour cette version, on remplace tout le fichier si Phidélia a renvoyé 
        # une version complète, ou on tente une injection ciblée.
        # Ici on privilégie le remplacement prudent.
        try:
            with open(fichier, "w", encoding="utf-8") as f:
                f.write(nouveau_code)
        except Exception as e:
            self.securite.restaurer_dernier(fichier)
            return f"ERREUR D'INJECTION : {e}"

        # 5. Validation (Après)
        try:
            r_apres = analyseur.analyser()
            sync_apres = calculer_sync_index(r_apres.radiance, r_apres.resistance)
        except Exception:
            self.securite.restaurer_dernier(fichier)
            return "ALERTE ENTROPIE : Le nouveau code est invalide (SyntaxError). Restauration effectuée."

        # 6. Verdict final
        gain = sync_apres - sync_avant
        if gain > 0 or force:
            return f"GUÉRISON RÉUSSIE : Radiance {r_avant.radiance:.1f} ⮕ {r_apres.radiance:.1f} | Sync Index Gain: +{gain:.4f}"
        else:
            # Si le code n'est pas meilleur, on restaure pour ne pas dégrader la radiance
            self.securite.restaurer_dernier(fichier)
            return "SUTURE REJETÉE : La proposition n'améliore pas la synchronicité. Restauration du backup."

    def _extraire_code(self, reponse: str) -> Optional[str]:
        """Extrait le bloc de code markdown de la réponse de l'IA."""
        # Regex pour capturer le contenu entre ```python ... ``` ou ``` ... ```
        pattern = r"```(?:python)?\n(.*?)\n```"
        matches = re.findall(pattern, reponse, re.DOTALL)
        if matches:
            # On prend le bloc le plus long (souvent le code final)
            return max(matches, key=len)
        return None
