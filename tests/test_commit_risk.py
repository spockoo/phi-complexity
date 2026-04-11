"""
tests/test_commit_risk.py — Tests pour phi_complexity/commit_risk.py

Couvre :
    - Extraction des features (mock git)
    - Scoring bayésien (cas limites + cas normaux)
    - Classification des niveaux
    - Identification des facteurs dominants
    - Rapport console
    - CLI (main())
    - Gestion des erreurs
"""

from __future__ import annotations

import json
import math
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from phi_complexity.commit_risk import (
    FeaturesCommit,
    RapportRisque,
    _classifier_niveau,
    _compter_mots_suspects,
    _est_chemin_sensible,
    _identifier_facteurs_dominants,
    analyser_commit,
    extraire_features,
    main,
    rapport_console,
    scorer_commit,
)


class TestCheminsSensibles(unittest.TestCase):
    """Tests pour _est_chemin_sensible."""

    def test_github_workflow(self):
        self.assertTrue(_est_chemin_sensible(".github/workflows/ci.yml"))

    def test_pyproject(self):
        self.assertTrue(_est_chemin_sensible("pyproject.toml"))

    def test_requirements(self):
        self.assertTrue(_est_chemin_sensible("requirements.txt"))

    def test_cle_pem(self):
        self.assertTrue(_est_chemin_sensible("deploy.pem"))

    def test_cle_key(self):
        self.assertTrue(_est_chemin_sensible("private.key"))

    def test_credentials(self):
        self.assertTrue(_est_chemin_sensible("credentials.json"))

    def test_fichier_python_ordinaire(self):
        self.assertFalse(_est_chemin_sensible("phi_complexity/core.py"))

    def test_fichier_tests(self):
        self.assertFalse(_est_chemin_sensible("tests/test_core.py"))

    def test_auth_dans_chemin(self):
        self.assertTrue(_est_chemin_sensible("config/auth.py"))

    def test_dockerfile(self):
        self.assertTrue(_est_chemin_sensible("Dockerfile"))

    def test_setup_py(self):
        self.assertTrue(_est_chemin_sensible("setup.py"))


class TestMotsSuspects(unittest.TestCase):
    """Tests pour _compter_mots_suspects."""

    def test_message_propre(self):
        self.assertEqual(_compter_mots_suspects("fix: add unit tests for oracle"), 0)

    def test_bypass(self):
        count = _compter_mots_suspects("bypass security check")
        self.assertGreater(count, 0)

    def test_skip_ci(self):
        count = _compter_mots_suspects("update readme [skip ci]")
        self.assertGreater(count, 0)

    def test_password(self):
        count = _compter_mots_suspects("remove hardcoded password from config")
        self.assertGreater(count, 0)

    def test_multiple_suspects(self):
        # bypass + disable + skip ci = 3 occurrences
        count = _compter_mots_suspects("bypass auth, disable check, skip ci")
        self.assertGreaterEqual(count, 3)

    def test_insensible_casse(self):
        count = _compter_mots_suspects("BYPASS auth")
        self.assertGreater(count, 0)

    def test_vide(self):
        self.assertEqual(_compter_mots_suspects(""), 0)


class TestScorerCommit(unittest.TestCase):
    """Tests pour scorer_commit (modèle bayésien)."""

    def test_commit_risque_faible(self):
        """Un commit léger et propre doit avoir un score bas."""
        features = FeaturesCommit(
            sha="abc123",
            message="docs: fix typo in README",
            lignes_ajoutees=3,
            lignes_supprimees=2,
            fichiers_changes=1,
            chemins_sensibles=0,
            mots_suspects_count=0,
            hors_heures_bureau=False,
            est_weekend=False,
        )
        score, details = scorer_commit(features)
        self.assertLess(score, 0.50)
        self.assertIn("diff_size", details)
        self.assertIn("chemins_sensibles", details)

    def test_commit_risque_eleve(self):
        """Un commit massif avec fichiers sensibles doit scorer haut."""
        features = FeaturesCommit(
            sha="def456",
            message="bypass security check [skip ci]",
            lignes_ajoutees=1200,
            lignes_supprimees=800,
            fichiers_changes=50,
            chemins_sensibles=5,
            mots_suspects_count=4,
            fichiers_binaires=3,
            hors_heures_bureau=True,
            est_weekend=True,
        )
        score, details = scorer_commit(features)
        self.assertGreater(score, 0.60)

    def test_score_dans_intervalle(self):
        """Le score doit toujours être dans [0, 1]."""
        for lignes in [0, 10, 100, 1000, 10000]:
            features = FeaturesCommit(lignes_ajoutees=lignes)
            score, _ = scorer_commit(features)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_contributions_toutes_presentes(self):
        """Toutes les clés de contribution doivent être dans details."""
        features = FeaturesCommit()
        _, details = scorer_commit(features)
        cles_attendues = [
            "diff_size", "fichiers_changes", "chemins_sensibles",
            "mots_suspects", "fichiers_binaires", "hors_heures_bureau", "weekend"
        ]
        for cle in cles_attendues:
            self.assertIn(cle, details)

    def test_hors_heures_incremente_score(self):
        """Commit hors heures doit augmenter le score."""
        base = FeaturesCommit(hors_heures_bureau=False)
        hors = FeaturesCommit(hors_heures_bureau=True)
        score_base, _ = scorer_commit(base)
        score_hors, _ = scorer_commit(hors)
        self.assertGreater(score_hors, score_base)

    def test_weekend_incremente_score(self):
        """Commit le week-end doit augmenter le score."""
        base = FeaturesCommit(est_weekend=False)
        weekend = FeaturesCommit(est_weekend=True)
        score_base, _ = scorer_commit(base)
        score_weekend, _ = scorer_commit(weekend)
        self.assertGreater(score_weekend, score_base)


class TestClassifierNiveau(unittest.TestCase):
    """Tests pour _classifier_niveau."""

    def test_faible(self):
        self.assertEqual(_classifier_niveau(0.10), "FAIBLE")
        self.assertEqual(_classifier_niveau(0.29), "FAIBLE")

    def test_modere(self):
        self.assertEqual(_classifier_niveau(0.30), "MODÉRÉ")
        self.assertEqual(_classifier_niveau(0.59), "MODÉRÉ")

    def test_eleve(self):
        self.assertEqual(_classifier_niveau(0.60), "ÉLEVÉ")
        self.assertEqual(_classifier_niveau(0.79), "ÉLEVÉ")

    def test_critique(self):
        self.assertEqual(_classifier_niveau(0.80), "CRITIQUE")
        self.assertEqual(_classifier_niveau(1.00), "CRITIQUE")

    def test_zero(self):
        self.assertEqual(_classifier_niveau(0.0), "FAIBLE")


class TestFacteursDominants(unittest.TestCase):
    """Tests pour _identifier_facteurs_dominants."""

    def test_diff_volumineux_detecte(self):
        features = FeaturesCommit(lignes_ajoutees=300, lignes_supprimees=200)
        details = {"diff_size": 1.0, "fichiers_changes": 0.0, "chemins_sensibles": 0.0,
                   "mots_suspects": 0.0, "fichiers_binaires": 0.0,
                   "hors_heures_bureau": 0.0, "weekend": 0.0}
        facteurs = _identifier_facteurs_dominants(features, details)
        self.assertTrue(any("diff" in f.lower() or "lignes" in f.lower() for f in facteurs))

    def test_chemin_sensible_detecte(self):
        features = FeaturesCommit(chemins_sensibles=3)
        details = {"diff_size": 0.0, "fichiers_changes": 0.0, "chemins_sensibles": 1.0,
                   "mots_suspects": 0.0, "fichiers_binaires": 0.0,
                   "hors_heures_bureau": 0.0, "weekend": 0.0}
        facteurs = _identifier_facteurs_dominants(features, details)
        self.assertTrue(any("sensible" in f.lower() for f in facteurs))

    def test_aucun_facteur_si_tout_faible(self):
        features = FeaturesCommit()
        details = {k: 0.0 for k in ["diff_size", "fichiers_changes", "chemins_sensibles",
                                      "mots_suspects", "fichiers_binaires",
                                      "hors_heures_bureau", "weekend"]}
        facteurs = _identifier_facteurs_dominants(features, details)
        self.assertEqual(facteurs, [])

    def test_hors_heures_bureau_detecte(self):
        features = FeaturesCommit(hors_heures_bureau=True, heure=3)
        details = {k: 0.0 for k in ["diff_size", "fichiers_changes", "chemins_sensibles",
                                      "mots_suspects", "fichiers_binaires",
                                      "hors_heures_bureau", "weekend"]}
        facteurs = _identifier_facteurs_dominants(features, details)
        self.assertTrue(any("heure" in f.lower() or "bureau" in f.lower() for f in facteurs))


class TestRapportConsole(unittest.TestCase):
    """Tests pour rapport_console."""

    def test_rapport_faible(self):
        rapport = RapportRisque(sha="abc123def456", score=0.10, niveau="FAIBLE")
        sortie = rapport_console(rapport)
        self.assertIn("PHI-SENTINEL", sortie)
        self.assertIn("FAIBLE", sortie)
        self.assertIn("abc123def456", sortie)

    def test_rapport_critique(self):
        rapport = RapportRisque(
            sha="deadbeef1234",
            score=0.95,
            niveau="CRITIQUE",
            facteurs_dominants=["Diff volumineux : 2000 lignes", "Fichiers sensibles : 5"],
        )
        sortie = rapport_console(rapport)
        self.assertIn("CRITIQUE", sortie)
        self.assertIn("Diff volumineux", sortie)

    def test_rapport_sans_facteurs(self):
        rapport = RapportRisque(sha="aabb", score=0.05, niveau="FAIBLE")
        sortie = rapport_console(rapport)
        self.assertIn("Aucun facteur", sortie)


class TestRapportRisqueToDict(unittest.TestCase):
    """Tests pour RapportRisque.to_dict()."""

    def test_serialisation_complete(self):
        rapport = RapportRisque(
            sha="test123",
            score=0.42,
            niveau="MODÉRÉ",
            facteurs_dominants=["Factor A"],
            features={"message": "test"},
            details={"diff_size": 0.3},
        )
        d = rapport.to_dict()
        self.assertEqual(d["sha"], "test123")
        self.assertAlmostEqual(float(d["score"]), 0.42, places=2)
        self.assertEqual(d["niveau"], "MODÉRÉ")
        self.assertIn("Factor A", d["facteurs_dominants"])

    def test_valeurs_par_defaut(self):
        rapport = RapportRisque(sha="x", score=0.0, niveau="FAIBLE")
        d = rapport.to_dict()
        self.assertEqual(d["features"], {})
        self.assertEqual(d["details"], {})


class TestExtraireFeatures(unittest.TestCase):
    """Tests pour extraire_features avec mocks git."""

    def _mock_run_git(self, resultats: dict):
        """Crée un patch de _run_git retournant des résultats prédéfinis selon les args."""
        def side_effect(args, cwd=None):
            key = " ".join(args)
            for pattern, val in resultats.items():
                if pattern in key:
                    return val
            return ""
        return side_effect

    @patch("phi_complexity.commit_risk._run_git")
    def test_extraction_basique(self, mock_git):
        mock_git.side_effect = self._mock_run_git({
            "log -1 --format=%s": "feat: add new feature",
            "log -1 --format=%an": "Alice",
            "log -1 --format=%ai": "2024-01-15 14:30:00 +0000",
            "log -1 --format=%ad": "1",
            "diff --numstat": "10\t5\tsrc/main.py\n3\t1\tdocs/readme.md",
        })
        features = extraire_features("abc123")
        self.assertEqual(features.sha, "abc123")
        self.assertEqual(features.message, "feat: add new feature")
        self.assertEqual(features.auteur, "Alice")
        self.assertEqual(features.heure, 14)
        self.assertEqual(features.lignes_ajoutees, 13)
        self.assertEqual(features.lignes_supprimees, 6)
        self.assertEqual(features.fichiers_changes, 2)

    @patch("phi_complexity.commit_risk._run_git")
    def test_extraction_chemin_sensible(self, mock_git):
        mock_git.side_effect = self._mock_run_git({
            "log -1 --format=%s": "update ci",
            "log -1 --format=%an": "Bob",
            "log -1 --format=%ai": "2024-01-15 02:00:00 +0000",
            "log -1 --format=%ad": "0",
            "diff --numstat": "5\t2\t.github/workflows/ci.yml",
        })
        features = extraire_features("def456")
        self.assertEqual(features.chemins_sensibles, 1)
        self.assertTrue(features.hors_heures_bureau)  # heure 2 = nuit

    @patch("phi_complexity.commit_risk._run_git")
    def test_extraction_fichier_binaire(self, mock_git):
        mock_git.side_effect = self._mock_run_git({
            "log -1 --format=%s": "add binary",
            "log -1 --format=%an": "Bob",
            "log -1 --format=%ai": "2024-01-15 10:00:00 +0000",
            "log -1 --format=%ad": "2",
            "diff --numstat": "-\t-\timage.png",
        })
        features = extraire_features("ghi789")
        self.assertEqual(features.fichiers_binaires, 1)

    @patch("phi_complexity.commit_risk._run_git")
    def test_extraction_git_silencieux_sur_erreur(self, mock_git):
        mock_git.return_value = ""
        features = extraire_features("zzz999")
        self.assertEqual(features.sha, "zzz999")
        self.assertEqual(features.fichiers_changes, 0)

    @patch("phi_complexity.commit_risk._run_git")
    def test_timestamp_malformate(self, mock_git):
        mock_git.side_effect = self._mock_run_git({
            "log -1 --format=%ai": "not-a-date",
        })
        features = extraire_features("malformed")
        self.assertEqual(features.heure, 12)  # Valeur par défaut

    @patch("phi_complexity.commit_risk._run_git")
    def test_weekend_samedi(self, mock_git):
        mock_git.side_effect = self._mock_run_git({
            "log -1 --format=%ad": "6",  # samedi
        })
        features = extraire_features("sat123")
        self.assertTrue(features.est_weekend)

    @patch("phi_complexity.commit_risk._run_git")
    def test_weekend_dimanche(self, mock_git):
        mock_git.side_effect = self._mock_run_git({
            "log -1 --format=%ad": "0",  # dimanche
        })
        features = extraire_features("sun123")
        self.assertTrue(features.est_weekend)

    @patch("phi_complexity.commit_risk._run_git")
    def test_diff_numstat_malformee(self, mock_git):
        mock_git.side_effect = self._mock_run_git({
            "diff --numstat": "malformed_line_without_tabs",
        })
        features = extraire_features("bad123")
        self.assertEqual(features.lignes_ajoutees, 0)

    @patch("phi_complexity.commit_risk._run_git")
    def test_diff_numstat_valeurs_non_entiers(self, mock_git):
        mock_git.side_effect = self._mock_run_git({
            "diff --numstat": "abc\txyz\tfile.py",
        })
        features = extraire_features("nonint")
        self.assertEqual(features.lignes_ajoutees, 0)


class TestAnalyserCommit(unittest.TestCase):
    """Tests pour analyser_commit (pipeline complet)."""

    @patch("phi_complexity.commit_risk._run_git")
    def test_pipeline_complet(self, mock_git):
        mock_git.side_effect = lambda args, cwd=None: {
            "log -1 --format=%s": "fix: minor correction",
            "log -1 --format=%an": "Alice",
            "log -1 --format=%ai": "2024-03-20 10:00:00 +0000",
            "log -1 --format=%ad": "3",
        }.get(" ".join(args), "")

        rapport = analyser_commit("abc123")
        self.assertIsInstance(rapport, RapportRisque)
        self.assertEqual(rapport.sha, "abc123")
        self.assertGreaterEqual(rapport.score, 0.0)
        self.assertLessEqual(rapport.score, 1.0)
        self.assertIn(rapport.niveau, ["FAIBLE", "MODÉRÉ", "ÉLEVÉ", "CRITIQUE"])
        self.assertIsInstance(rapport.facteurs_dominants, list)


class TestMainCLI(unittest.TestCase):
    """Tests pour le point d'entrée CLI main()."""

    @patch("phi_complexity.commit_risk.analyser_commit")
    def test_cli_format_console(self, mock_analyser):
        mock_analyser.return_value = RapportRisque(
            sha="abc123", score=0.15, niveau="FAIBLE"
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            code = main(["--sha", "abc123", "--format", "console"])
        self.assertEqual(code, 0)

    @patch("phi_complexity.commit_risk.analyser_commit")
    def test_cli_format_json_stdout(self, mock_analyser):
        mock_analyser.return_value = RapportRisque(
            sha="abc123",
            score=0.42,
            niveau="MODÉRÉ",
            features={},
            details={},
        )
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            code = main(["--sha", "abc123", "--format", "json"])
        self.assertEqual(code, 0)

    @patch("phi_complexity.commit_risk.analyser_commit")
    def test_cli_output_fichier(self, mock_analyser, tmp_path=None):
        import tempfile
        mock_analyser.return_value = RapportRisque(
            sha="abc123",
            score=0.1,
            niveau="FAIBLE",
            features={},
            details={},
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            chemin = f.name
        try:
            code = main(["--sha", "abc123", "--output", chemin])
            self.assertEqual(code, 0)
            with open(chemin) as f:
                data = json.load(f)
            self.assertEqual(data["sha"], "abc123")
        finally:
            import os
            if os.path.exists(chemin):
                os.unlink(chemin)

    def test_cli_sans_sha_echoue(self):
        """Le CLI doit échouer si --sha est absent."""
        with self.assertRaises(SystemExit):
            main([])


if __name__ == "__main__":
    unittest.main()
