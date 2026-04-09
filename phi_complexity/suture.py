from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .analyseur import ResultatAnalyse

from .core import PHI

class SutureAgent:
    """
    Phidélia — Agent de Suture Souverain.
    Utilise l'intelligence agentique pour restaurer la radiance du code.
    """

    def __init__(self, api_url: str = "http://localhost:1234/v1/chat/completions"):
        self.api_url = api_url

    def generer_prompt(self, resultat: ResultatAnalyse) -> str:
        """Construit le prompt Morphic-Phi pour l'IA."""
        oudjat = resultat.oudjat
        extrait_code = "Aucun extrait disponible."
        
        # Tentative de récupération du code de la fonction problématique
        if oudjat:
            try:
                with open(resultat.fichier, "r", encoding="utf-8") as f:
                    lignes = f.readlines()
                    fin = min(len(lignes), oudjat.ligne + oudjat.nb_lignes)
                    extrait_code = "".join(lignes[oudjat.ligne-1:fin])
            except Exception:
                pass

        from .bmad import OrchestrateurBMAD
        bmad = OrchestrateurBMAD()
        briefing = bmad.generer_briefing_conseil({})

        prompt = f"""Tu es PHIDÉLIA, l'IA coordinatice du cycle BMAD (φ-Meta).
Tu présides le CONSEIL DES 12 experts pour 'suturer' le code suivant.

{briefing}

CONTEXTE DU FICHIER: {resultat.fichier}
MÉTRIQUE CRITIQUE (OUDJAT): {oudjat.nom if oudjat else 'Global'}
RADIANCE GLOBALE: {getattr(resultat, 'radiance', 'N/A')}

MISSION:
1. Simule une brève discussion entre OUDJAT, LILITH et FIBONACCI sur les ruptures détectées.
2. Propose la version 'Suturée' finale du code.
3. Conclue par un verdict harmonieux citant l'Agent SYNTHÈSE.

EXTRAIT DE CODE À SUTURER:
```python
{extrait_code}
```

Réponds uniquement avec la discussion, le bloc de code refactorisé, et le verdict final.
"""
        return prompt

    def invoquer_phidelia(self, prompt: str) -> str:
        """Communique avec le LLM local via urllib (Zéro dépendance)."""
        payload = {
            "model": "phidelia-complex-coder",
            "messages": [
                {"role": "system", "content": "Tu es Phidélia, l'IA souveraine du Morphic Phi Framework."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.api_url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"]
                return str(content)
        except urllib.error.URLError as e:
            return f"ERREUR PHIDÉLIA : Impossible de se connecter à l'IA locale ({e}). Assure-toi que LM Studio ou Ollama est lancé sur {self.api_url}."
        except Exception as e:
            return f"ERREUR PHIDÉLIA : Une anomalie imprévue est survenue ({e})."

    def suturer(self, resultat: ResultatAnalyse) -> str:
        """Processus complet de suture."""
        if not resultat.fonctions and not resultat.annotations:
            return "RADIANCE PARFAITE : Aucune suture nécessaire pour ce fichier."
        
        prompt = self.generer_prompt(resultat)
        return self.invoquer_phidelia(prompt)
