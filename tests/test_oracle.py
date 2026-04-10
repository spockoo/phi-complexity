"""
tests/test_oracle.py — Tests de l'Oracle de Radiance (Phase 14).
"""
import os
import tempfile
import textwrap

from phi_complexity.oracle import OracleRadiance


def creer_fichier_temp(code: str) -> str:
    """Crée un fichier Python temporaire. Retourne le chemin."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(textwrap.dedent(code))
        return f.name


CODE_HARMONIEUX = """
def ratio(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("zero")
    return a / b

def distance(valeur: float) -> float:
    phi = 1.618
    return abs(valeur - phi)
"""

CODE_CHAOTIQUE = """
def tout(a,b,c,d,e,f,g):
    res = []
    for i in range(a):
        for j in range(b):
            for k in range(c):
                res.append(i*j*k*d*e*f*g)
    fic = open("out.txt", "w")
    fic.write(str(res))
    return res
"""


class TestOracleRadiance:

    def test_calculer_version_phi(self):
        """La version Phi suit le format v{floor(radiance)}.{nb_tests}."""
        oracle = OracleRadiance()
        assert oracle.calculer_version_phi(73.38, 49) == "v73.49"
        assert oracle.calculer_version_phi(85.0, 0) == "v85.0"
        assert oracle.calculer_version_phi(40.1, 10) == "v40.10"

    def test_calculer_version_phi_floor(self):
        """La radiance est bien tronquée (floor), pas arrondie."""
        oracle = OracleRadiance()
        assert oracle.calculer_version_phi(73.99, 5) == "v73.5"

    def test_radiance_globale_vide(self):
        """La radiance globale est 0.0 pour une liste vide."""
        oracle = OracleRadiance()
        assert oracle.calculer_radiance_globale([]) == 0.0

    def test_radiance_globale_un_fichier(self):
        """Avec un seul fichier, la radiance globale est sa propre radiance."""
        oracle = OracleRadiance()
        audits = [{"fichier": "f.py", "radiance": 75.0}]
        resultat = oracle.calculer_radiance_globale(audits)
        assert abs(resultat - 75.0) < 1e-6

    def test_radiance_globale_ponderation_phi(self):
        """Les fichiers à haute radiance pèsent plus dans la moyenne φ."""
        oracle = OracleRadiance()
        audits = [
            {"fichier": "a.py", "radiance": 90.0},
            {"fichier": "b.py", "radiance": 40.0},
        ]
        globale = oracle.calculer_radiance_globale(audits)
        # La moyenne simple serait 65.0 — la φ-pondération tire vers le haut
        assert globale > 65.0

    def test_valider_release_acceptee(self):
        """Une release est acceptée si la radiance globale dépasse le seuil."""
        fichier = creer_fichier_temp(CODE_HARMONIEUX)
        try:
            oracle = OracleRadiance()
            verdict = oracle.valider_release([fichier], seuil=40.0, nb_tests=5)
            assert verdict["nb_fichiers"] == 1
            assert verdict["nb_tests"] == 5
            assert verdict["seuil"] == 40.0
            assert "version_phi" in verdict
            assert verdict["radiance_globale"] >= 40.0
            assert verdict["acceptee"] is True
        finally:
            os.unlink(fichier)

    def test_valider_release_bloquee(self):
        """Une release est bloquée si la radiance est sous le seuil."""
        fichier = creer_fichier_temp(CODE_CHAOTIQUE)
        try:
            oracle = OracleRadiance()
            verdict = oracle.valider_release([fichier], seuil=99.0, nb_tests=0)
            assert verdict["acceptee"] is False
            assert len(verdict["fichiers_sous_seuil"]) == 1
        finally:
            os.unlink(fichier)

    def test_rapport_oracle_accepte(self):
        """Le rapport d'une release acceptée contient les marqueurs visuels."""
        oracle = OracleRadiance()
        verdict = {
            "acceptee": True,
            "radiance_globale": 75.0,
            "seuil": 70.0,
            "version_phi": "v75.49",
            "nb_fichiers": 3,
            "nb_tests": 49,
            "fichiers_sous_seuil": [],
        }
        rapport = oracle.rapport_oracle(verdict)
        assert "RELEASE AUTORISÉE" in rapport
        assert "v75.49" in rapport
        assert "49" in rapport

    def test_rapport_oracle_bloque(self):
        """Le rapport d'une release bloquée signale les fichiers défaillants."""
        oracle = OracleRadiance()
        verdict = {
            "acceptee": False,
            "radiance_globale": 55.0,
            "seuil": 70.0,
            "version_phi": "v55.10",
            "nb_fichiers": 2,
            "nb_tests": 10,
            "fichiers_sous_seuil": ["src/chaos.py"],
        }
        rapport = oracle.rapport_oracle(verdict)
        assert "RELEASE BLOQUÉE" in rapport
        assert "chaos.py" in rapport

    def test_auditer_fichiers_erreur(self):
        """Un fichier inexistant produit radiance=0 sans lever d'exception."""
        import tempfile
        inexistant = os.path.join(tempfile.gettempdir(), "phi_oracle_n_existe_pas_test.py")
        oracle = OracleRadiance()
        resultats = oracle.auditer_fichiers([inexistant])
        assert len(resultats) == 1
        assert resultats[0]["radiance"] == 0.0
        assert "erreur" in resultats[0]
