"""
tests/test_suture.py — Tests de l'agent Phidélia (SutureAgent — suture.py).
"""

import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from io import BytesIO

from phi_complexity.suture import SutureAgent
from phi_complexity.analyseur import ResultatAnalyse, MetriqueFonction


def _resultat_simple(fichier: str = "test.py") -> ResultatAnalyse:
    r = ResultatAnalyse(fichier=fichier)
    r.radiance = 55.0
    r.resistance = 0.5
    r.lilith_variance = 400.0
    r.shannon_entropy = 2.2
    r.phi_ratio = 1.4
    r.pole_alpha = 1
    r.pole_omega = 20
    f = MetriqueFonction(
        nom="chaotique",
        ligne=5,
        complexite=30,
        nb_args=3,
        nb_lignes=25,
        profondeur_max=4,
        distance_fib=2.5,
        phi_ratio=1.8,
    )
    r.fonctions = [f]
    r.oudjat = f
    return r


class TestSutureAgent:

    # ──────────────── generer_prompt() ────────────────

    def test_generer_prompt_contient_contexte(self):
        agent = SutureAgent()
        r = _resultat_simple()
        prompt = agent.generer_prompt(r)
        assert "PHIDÉLIA" in prompt
        assert r.fichier in prompt

    def test_generer_prompt_contient_oudjat(self):
        agent = SutureAgent()
        r = _resultat_simple()
        prompt = agent.generer_prompt(r)
        assert "chaotique" in prompt

    def test_generer_prompt_sans_oudjat(self):
        """Sans fonction oudjat, le prompt mentionne 'Global'."""
        agent = SutureAgent()
        r = _resultat_simple()
        r.oudjat = None
        r.fonctions = []
        prompt = agent.generer_prompt(r)
        assert "Global" in prompt

    def test_generer_prompt_avec_fichier_existant(self):
        """Le prompt intègre un extrait de code si le fichier existe."""
        code = "def chaotique(a, b, c):\n    for i in range(a):\n        pass\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            chemin = f.name
        try:
            agent = SutureAgent()
            r = _resultat_simple(fichier=chemin)
            r.fonctions[0].ligne = 1
            r.fonctions[0].nb_lignes = 3
            prompt = agent.generer_prompt(r)
            assert len(prompt) > 100
        finally:
            os.unlink(chemin)

    # ──────────────── invoquer_phidelia() ────────────────

    def test_invoquer_phidelia_url_error(self):
        """En cas d'erreur de connexion, retourne un message d'erreur."""
        import urllib.error

        agent = SutureAgent()
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
            resultat = agent.invoquer_phidelia("test prompt")
        assert "ERREUR" in resultat

    def test_invoquer_phidelia_exception_generique(self):
        """En cas d'exception générique, retourne un message d'erreur."""
        agent = SutureAgent()
        with patch("urllib.request.urlopen", side_effect=RuntimeError("anomalie")):
            resultat = agent.invoquer_phidelia("test prompt")
        assert "ERREUR" in resultat

    def test_invoquer_phidelia_succes(self):
        """Simule une réponse JSON valide du LLM."""
        agent = SutureAgent()
        payload = {
            "choices": [{"message": {"content": "Code suturé avec succès."}}]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(payload).encode("utf-8")
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_response):
            resultat = agent.invoquer_phidelia("test prompt")
        assert resultat == "Code suturé avec succès."

    # ──────────────── suturer() ────────────────

    def test_suturer_fichier_sans_annotations(self):
        """Un fichier sans annotations ni fonctions → 'RADIANCE PARFAITE'."""
        agent = SutureAgent()
        r = _resultat_simple()
        r.fonctions = []
        r.annotations = []
        resultat = agent.suturer(r)
        assert "RADIANCE PARFAITE" in resultat

    def test_suturer_appelle_invoquer(self):
        """suturer() appelle bien invoquer_phidelia() quand il y a des fonctions."""
        agent = SutureAgent()
        r = _resultat_simple()
        with patch.object(agent, "invoquer_phidelia", return_value="mock response") as mock_inv:
            with patch.object(agent, "generer_prompt", return_value="mock prompt") as mock_gen:
                resultat = agent.suturer(r)
        mock_gen.assert_called_once_with(r)
        mock_inv.assert_called_once_with("mock prompt")
        assert resultat == "mock response"
