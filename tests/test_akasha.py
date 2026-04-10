"""
tests/test_akasha.py — Tests du moteur holographique akashique (Phase 11.6).
"""

import json
import os
import tempfile
import shutil

from phi_complexity.akasha import MatriceHolographique, RegistreAkashique


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

METRIQUES_SIMPLES = {
    "radiance": 80.0,
    "resistance": 0.2,
    "lilith_variance": 300.0,
    "shannon_entropy": 2.5,
    "phi_ratio": 1.618,
    "fichier": "test.py",
}


class TestMatriceHolographique:

    def test_init_calcule_vecteur(self):
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        assert len(mat.vecteur) == 5
        assert 0.0 <= mat.vecteur[0] <= 1.0  # radiance / 100

    def test_vecteur_radiance_normalise(self):
        mat = MatriceHolographique({"radiance": 50.0})
        assert abs(mat.vecteur[0] - 0.5) < 1e-9

    def test_vecteur_valeurs_bornees(self):
        """Toutes les composantes du vecteur sont dans [0, 1]."""
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        for v in mat.vecteur:
            assert 0.0 <= v <= 1.0, f"Composante hors bornes : {v}"

    def test_transmuter_retourne_coords(self):
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        coords = mat.transmuter()
        assert len(coords) == 5
        for c in coords:
            assert "a" in c and "b" in c

    def test_transmuter_valeurs_numeriques(self):
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        coords = mat.transmuter()
        for c in coords:
            assert isinstance(c["a"], float)
            assert isinstance(c["b"], float)

    def test_calculer_masse_harmonique(self):
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        masse = mat.calculer_masse_harmonique()
        assert isinstance(masse, float)
        assert masse >= 0.0

    def test_calculer_coherence_retourne_float(self):
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        c = mat.calculer_coherence()
        assert isinstance(c, float)

    def test_calculer_similitude_identique(self):
        """La similitude d'une matrice avec elle-même est 1.0."""
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        assert abs(mat.calculer_similitude(mat) - 1.0) < 1e-9

    def test_calculer_similitude_zero_vector(self):
        """Similitude avec un vecteur nul retourne 0.0."""
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        zero_mat = MatriceHolographique({})
        zero_mat.vecteur = [0.0] * 5
        assert mat.calculer_similitude(zero_mat) == 0.0

    def test_vers_grille_contient_axes(self):
        mat = MatriceHolographique(METRIQUES_SIMPLES)
        grille = mat.vers_grille()
        assert "radiance" in grille
        assert "resistance" in grille

    def test_init_donnees_vides(self):
        """Données vides → vecteur de zéros, pas d'erreur."""
        mat = MatriceHolographique({})
        assert len(mat.vecteur) == 5
        assert mat.vecteur[0] == 0.0


class TestRegistreAkashique:

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.akasha = RegistreAkashique(workspace_root=self.tmpdir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_initialise_fichier_db(self):
        assert os.path.exists(self.akasha.db_path)
        with open(self.akasha.db_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "annales" in data

    def test_enregistrer_ajoute_entree(self):
        self.akasha.enregistrer(METRIQUES_SIMPLES)
        annales = self.akasha.consulter_historique()
        assert len(annales) == 1
        assert annales[0]["fichier"] == "test.py"
        assert annales[0]["radiance"] == 80.0

    def test_enregistrer_plusieurs_entrees(self):
        for i in range(3):
            m = dict(METRIQUES_SIMPLES, fichier=f"file_{i}.py", radiance=float(60 + i))
            self.akasha.enregistrer(m)
        annales = self.akasha.consulter_historique(10)
        assert len(annales) == 3

    def test_consulter_historique_limite(self):
        for i in range(5):
            m = dict(METRIQUES_SIMPLES, fichier=f"f{i}.py")
            self.akasha.enregistrer(m)
        assert len(self.akasha.consulter_historique(2)) == 2

    def test_enregistrer_resilient_aux_erreurs(self):
        """enregistrer() ne lève pas d'exception si le fichier db est corrompu."""
        with open(self.akasha.db_path, "w") as f:
            f.write("NOT JSON")
        # Ne doit pas lever d'exception
        self.akasha.enregistrer(METRIQUES_SIMPLES)

    def test_consulter_historique_db_corrompue(self):
        """Retourne une liste vide si la base est corrompue."""
        with open(self.akasha.db_path, "w") as f:
            f.write("INVALID")
        assert self.akasha.consulter_historique() == []

    def test_trouver_similitude_aucun_match(self):
        """Sans annales, trouver_similitude retourne None."""
        resultat = self.akasha.trouver_similitude(METRIQUES_SIMPLES)
        assert resultat is None

    def test_trouver_similitude_meme_fichier_ignore(self):
        """Un fichier ne peut pas être similaire à lui-même."""
        self.akasha.enregistrer(METRIQUES_SIMPLES)
        resultat = self.akasha.trouver_similitude(METRIQUES_SIMPLES)
        assert resultat is None

    def test_trouver_similitude_fichier_different(self):
        """Deux métriques quasi-identiques mais noms différents → similitude détectée."""
        self.akasha.enregistrer(METRIQUES_SIMPLES)
        cible = dict(METRIQUES_SIMPLES, fichier="autre.py")
        # Similitude cosinus sera très proche de 1 (> 0.98)
        resultat = self.akasha.trouver_similitude(cible)
        assert resultat is not None
        assert resultat["fichier"] == "test.py"

    def test_annales_plafonnees_1000(self):
        """La base est plafonnée à 1000 entrées."""
        for i in range(1005):
            m = dict(METRIQUES_SIMPLES, fichier=f"f{i}.py")
            self.akasha.enregistrer(m)
        annales = self.akasha.consulter_historique(2000)
        assert len(annales) <= 1000
