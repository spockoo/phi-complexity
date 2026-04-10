"""
tests/test_gnose.py — Tests du Moteur Gnostique (GCS — Phase 12).
"""

import os
import shutil
import tempfile

from phi_complexity.gnose import MoteurGnostique
from phi_complexity.analyseur import ResultatAnalyse, MetriqueFonction


def _resultat_simple(fichier: str = "test.py") -> ResultatAnalyse:
    """Crée un ResultatAnalyse minimal pour les tests."""
    r = ResultatAnalyse(fichier=fichier)
    r.radiance = 75.0
    r.resistance = 0.3
    r.lilith_variance = 200.0
    r.shannon_entropy = 2.0
    r.phi_ratio = 1.6
    r.pole_alpha = 1
    r.pole_omega = 10
    return r


class TestMoteurGnostique:

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.gnose = MoteurGnostique(workspace_root=self.tmpdir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # ──────────────── Initialisation ────────────────

    def test_initialise_gnose_json(self):
        assert os.path.exists(self.gnose.gnose_path)
        import json
        with open(self.gnose.gnose_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    # ──────────────── calculer_sceau() ────────────────

    def test_calculer_sceau_retourne_sha256(self):
        r = _resultat_simple()
        sceau = self.gnose.calculer_sceau(r)
        assert isinstance(sceau, str)
        assert len(sceau) == 64  # sha256 hexdigest

    def test_calculer_sceau_deterministe(self):
        """Le même résultat produit toujours le même sceau."""
        r = _resultat_simple()
        assert self.gnose.calculer_sceau(r) == self.gnose.calculer_sceau(r)

    def test_calculer_sceau_sensible_aux_donnees(self):
        """Un changement de radiance change le sceau."""
        r1 = _resultat_simple()
        r2 = _resultat_simple()
        r2.radiance = 60.0
        assert self.gnose.calculer_sceau(r1) != self.gnose.calculer_sceau(r2)

    def test_calculer_sceau_poles_none(self):
        """Fonctionne même si pole_alpha et pole_omega sont None."""
        r = _resultat_simple()
        r.pole_alpha = None
        r.pole_omega = None
        sceau = self.gnose.calculer_sceau(r)
        assert len(sceau) == 64

    # ──────────────── sceller() ────────────────

    def test_sceller_enregistre_dans_registre(self):
        import json
        r = _resultat_simple()
        sceau = self.gnose.sceller(r)
        with open(self.gnose.gnose_path) as f:
            registre = json.load(f)
        assert r.fichier in registre
        assert registre[r.fichier]["sceau"] == sceau

    def test_sceller_retourne_sha256(self):
        r = _resultat_simple()
        sceau = self.gnose.sceller(r)
        assert len(sceau) == 64

    # ──────────────── verifier() ────────────────

    def test_verifier_apres_scellement(self):
        """Un fichier scellé sans modification doit être vérifié à True."""
        r = _resultat_simple()
        self.gnose.sceller(r)
        assert self.gnose.verifier(r) is True

    def test_verifier_sans_sceau_retourne_false(self):
        """Un fichier jamais scellé retourne False."""
        r = _resultat_simple(fichier="inconnu.py")
        assert self.gnose.verifier(r) is False

    def test_verifier_apres_modification_retourne_false(self):
        """Après modification des métriques, le sceau est brisé."""
        r = _resultat_simple()
        self.gnose.sceller(r)
        r.radiance = 99.0  # Modification
        assert self.gnose.verifier(r) is False

    # ──────────────── calculer_gnose_divergence() ────────────────

    def test_gnose_divergence_retourne_float(self):
        r = _resultat_simple()
        div = self.gnose.calculer_gnose_divergence(r)
        assert isinstance(div, float)
        assert div >= 0.0
