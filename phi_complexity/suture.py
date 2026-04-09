from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .analyseur import ResultatAnalyse



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
        from .akasha import RegistreAkashique
        
        bmad = OrchestrateurBMAD()
        akasha = RegistreAkashique()
        
        briefing = bmad.generer_briefing_conseil({})
        
        # Phase 11.6 : Conversion en dictionnaire transparent (Suture de type)
        metriques_brutes = {
            "fichier": resultat.fichier,
            "radiance": resultat.radiance,
            "resistance": resultat.resistance,
            "lilith_variance": resultat.lilith_variance,
            "shannon_entropy": resultat.shannon_entropy,
            "phi_ratio": resultat.phi_ratio,
            "signature": resultat.signature if hasattr(resultat, "signature") else ""
        }
        pattern_similaire = akasha.trouver_similitude(metriques_brutes)
        
        memo_akashique = ""
        if pattern_similaire:
            memo_akashique = f"\n MÉMOIRE AKASHIQUE : Un pattern similaire a été détecté dans {pattern_similaire['fichier']} (Radiance: {pattern_similaire['radiance']}). Utilise cette expérience."

        prompt = f"""Tu es PHIDÉLIA, l'IA coordinatice du cycle BMAD (φ-Meta).
Tu présides le CONSEIL DES 12 experts pour 'suturer' le code suivant à RÉSISTANCE MINIMALE (Phase 10).

{briefing}{memo_akashique}

CONTEXTE DU FICHIER: {resultat.fichier}
MÉTRIQUE CRITIQUE (OUDJAT): {oudjat.nom if oudjat else 'Global'} (Pôle Omega : Ligne {getattr(resultat, 'pole_omega', 'N/A')})
PÔLE ALPHA : Ligne {getattr(resultat, 'pole_alpha', 'N/A')}
RÉSISTANCE Ω : {getattr(resultat, 'resistance', 'N/A')} (Friction à éliminer)

MISSION (LÉVITATION) :
1. Utilise la force de lévitation (Fz = -φ³ e^z/φ) pour libérer le code de sa gravité (boilerplate, complexité inutile).
2. Simule une brève discussion entre OUDJAT, LILITH et FIBONACCI sur la supraconductivité du flux.
3. Propose la version 'Suturée' finale, épurée et harmonieuse.
4. Conclue par un verdict citant l'Agent SYNTHÈSE.

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
