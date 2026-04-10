"""
tests/test_autosuture.py — Tests de l'Auto-Suture autonome (Phase 12).
"""

import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

from phi_complexity.autosuture import AutoSuture

CODE_HARMONIEUX = '''\
def ajouter(a: float, b: float) -> float:
    """Additionne deux nombres."""
    return a + b

def multiplier(a: float, b: float) -> float:
    """Multiplie deux nombres."""
    return a * b
'''

CODE_CHAOTIQUE = """\
def f(x,y,z,w,v):
    r=0
    for i in range(x):
        for j in range(y):
            for k in range(z):
                for l in range(w):
                    for m in range(v):
                        r+=i*j*k*l*m
    return r
"""


def _creer_fichier(contenu: str) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    )
    f.write(contenu)
    f.close()
    return f.name


class TestAutoSuture:

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ──────────────── _extraire_code() ────────────────

    def test_extraire_code_bloc_python(self):
        """Extrait le code d'un bloc ```python ... ```."""
        autosuture = AutoSuture.__new__(AutoSuture)
        reponse = "Texte\n```python\nx = 1\n```\nFin"
        code = autosuture._extraire_code(reponse)
        assert code == "x = 1"

    def test_extraire_code_bloc_generique(self):
        """Extrait le code d'un bloc ``` ... ``` sans langage."""
        autosuture = AutoSuture.__new__(AutoSuture)
        reponse = "Texte\n```\ny = 2\n```\nFin"
        code = autosuture._extraire_code(reponse)
        assert code == "y = 2"

    def test_extraire_code_aucun_bloc(self):
        """Retourne None si aucun bloc de code n'est trouvé."""
        autosuture = AutoSuture.__new__(AutoSuture)
        code = autosuture._extraire_code("Pas de code ici.")
        assert code is None

    def test_extraire_code_prend_le_plus_long(self):
        """S'il y a plusieurs blocs, prend le plus long."""
        autosuture = AutoSuture.__new__(AutoSuture)
        reponse = "```python\ncourt\n```\n```python\nbloc beaucoup plus long ici\n```"
        code = autosuture._extraire_code(reponse)
        assert code == "bloc beaucoup plus long ici"

    # ──────────────── guerir() — radiance élevée ────────────────

    def test_guerir_radiance_elevee_sans_force(self):
        """Si la radiance >= 85 et force=False, pas de guérison."""
        fichier = _creer_fichier(CODE_HARMONIEUX)
        try:
            with (
                patch("phi_complexity.autosuture.SutureAgent") as MockAgent,
                patch("phi_complexity.autosuture.SecuriteMaat") as MockSec,
            ):
                mock_agent = MagicMock()
                MockAgent.return_value = mock_agent
                mock_sec = MagicMock()
                MockSec.return_value = mock_sec

                # Forcer une radiance haute en mockant l'analyseur
                with patch("phi_complexity.autosuture.AnalyseurPhi") as MockAnalyseur:
                    mock_res = MagicMock()
                    mock_res.radiance = 90.0
                    mock_res.resistance = 0.1
                    mock_res.fonctions = []
                    mock_res.annotations = []
                    MockAnalyseur.return_value.analyser.return_value = mock_res

                    autosuture = AutoSuture()
                    verdict = autosuture.guerir(fichier, force=False)

                assert "STABLE" in verdict or "Aucune guérison" in verdict
        finally:
            os.unlink(fichier)

    def test_guerir_radiance_elevee_avec_force(self):
        """Avec force=True, la guérison est tentée même si la radiance est haute."""
        fichier = _creer_fichier(CODE_HARMONIEUX)
        try:
            with (
                patch("phi_complexity.autosuture.SutureAgent") as MockAgent,
                patch("phi_complexity.autosuture.SecuriteMaat") as MockSec,
                patch("phi_complexity.autosuture.AnalyseurPhi") as MockAnalyseur,
            ):

                mock_res = MagicMock()
                mock_res.radiance = 90.0
                mock_res.resistance = 0.1
                mock_res.fonctions = []
                mock_res.annotations = []
                MockAnalyseur.return_value.analyser.return_value = mock_res

                mock_agent = MagicMock()
                mock_agent.suturer.return_value = ""  # Aucun code valide
                MockAgent.return_value = mock_agent

                mock_sec = MagicMock()
                MockSec.return_value = mock_sec

                autosuture = AutoSuture()
                verdict = autosuture.guerir(fichier, force=True)

            # La suture retourne "ÉCHEC DE SUTURE" car pas de code valide
            assert "ÉCHEC" in verdict or "SUTURE" in verdict or "GUÉRISON" in verdict
        finally:
            os.unlink(fichier)

    def test_guerir_suture_invalide_retourne_echec(self):
        """Si l'IA ne renvoie pas de code valide, le verdict est ÉCHEC."""
        fichier = _creer_fichier(CODE_CHAOTIQUE)
        try:
            with (
                patch("phi_complexity.autosuture.SutureAgent") as MockAgent,
                patch("phi_complexity.autosuture.SecuriteMaat") as MockSec,
                patch("phi_complexity.autosuture.AnalyseurPhi") as MockAnalyseur,
                patch(
                    "phi_complexity.autosuture.calculer_sync_index", return_value=0.5
                ),
            ):

                mock_res = MagicMock()
                mock_res.radiance = 40.0
                mock_res.resistance = 0.8
                mock_res.fonctions = [MagicMock()]
                mock_res.annotations = []
                MockAnalyseur.return_value.analyser.return_value = mock_res

                mock_agent = MagicMock()
                mock_agent.suturer.return_value = "Aucun bloc de code."
                MockAgent.return_value = mock_agent

                mock_sec = MagicMock()
                MockSec.return_value = mock_sec

                autosuture = AutoSuture()
                verdict = autosuture.guerir(fichier, force=False)

            assert "ÉCHEC" in verdict
        finally:
            os.unlink(fichier)

    def test_guerir_transaction_rejet_si_pas_de_gain(self):
        """Le candidat est rejeté si le gain de synchronicité est nul/négatif."""
        fichier = _creer_fichier(CODE_CHAOTIQUE)
        with open(fichier, encoding="utf-8") as f:
            contenu_initial = f.read()
        try:
            with (
                patch("phi_complexity.autosuture.SutureAgent") as MockAgent,
                patch("phi_complexity.autosuture.SecuriteMaat") as MockSec,
                patch("phi_complexity.autosuture.AnalyseurPhi") as MockAnalyseur,
                patch(
                    "phi_complexity.autosuture.calculer_sync_index",
                    side_effect=[0.6, 0.5],
                ),
            ):
                avant = MagicMock()
                avant.radiance = 40.0
                avant.resistance = 0.7
                avant.fonctions = [MagicMock()]
                avant.annotations = []

                candidat = MagicMock()
                candidat.radiance = 39.0
                candidat.resistance = 0.8
                candidat.fonctions = [MagicMock()]
                candidat.annotations = []

                MockAnalyseur.return_value.analyser.side_effect = [avant, candidat]

                mock_agent = MagicMock()
                mock_agent.suturer.return_value = (
                    "```python\n"
                    "def f(x):\n"
                    "    return x\n"
                    "```"
                )
                MockAgent.return_value = mock_agent

                mock_sec = MagicMock()
                MockSec.return_value = mock_sec

                autosuture = AutoSuture()
                verdict = autosuture.guerir(fichier, force=False)

            with open(fichier, encoding="utf-8") as f:
                contenu_final = f.read()
            assert "SUTURE REJETÉE" in verdict
            assert contenu_final == contenu_initial
            mock_sec.restaurer_dernier.assert_called_once_with(fichier)
        finally:
            os.unlink(fichier)

    def test_guerir_transaction_commit_si_gain(self):
        """Le candidat est remplacé atomiquement si le gain est positif."""
        fichier = _creer_fichier(CODE_CHAOTIQUE)
        try:
            with (
                patch("phi_complexity.autosuture.SutureAgent") as MockAgent,
                patch("phi_complexity.autosuture.SecuriteMaat") as MockSec,
                patch("phi_complexity.autosuture.AnalyseurPhi") as MockAnalyseur,
                patch(
                    "phi_complexity.autosuture.calculer_sync_index",
                    side_effect=[0.4, 0.7, 0.8],
                ),
            ):
                avant = MagicMock()
                avant.radiance = 40.0
                avant.resistance = 0.9
                avant.fonctions = [MagicMock()]
                avant.annotations = []

                candidat = MagicMock()
                candidat.radiance = 65.0
                candidat.resistance = 0.4
                candidat.fonctions = [MagicMock()]
                candidat.annotations = []

                apres = MagicMock()
                apres.radiance = 70.0
                apres.resistance = 0.2
                apres.fonctions = [MagicMock()]
                apres.annotations = []

                MockAnalyseur.return_value.analyser.side_effect = [avant, candidat, apres]

                code_final = (
                    "def f(x):\n"
                    '    """Version guérie."""\n'
                    "    return x + 1\n"
                )
                mock_agent = MagicMock()
                mock_agent.suturer.return_value = f"```python\n{code_final}```"
                MockAgent.return_value = mock_agent

                mock_sec = MagicMock()
                MockSec.return_value = mock_sec

                autosuture = AutoSuture()
                verdict = autosuture.guerir(fichier, force=False)

            assert "GUÉRISON RÉUSSIE" in verdict
            mock_sec.restaurer_dernier.assert_not_called()
            with open(fichier, encoding="utf-8") as f:
                contenu_final = f.read()
            assert "Version guérie" in contenu_final
        finally:
            os.unlink(fichier)
