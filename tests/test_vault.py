"""
tests/test_vault.py — Tests du Phi Vault (Phase 16).
"""

import json
import os
import tempfile
import shutil

from phi_complexity.vault import PhiVault


def _creer_vault_temp():
    """Crée un vault temporaire pour les tests."""
    workspace = tempfile.mkdtemp()
    return PhiVault(workspace_root=workspace), workspace


def _metriques_test(fichier="test_file.py", radiance=82.4):
    """Retourne des métriques de test."""
    return {
        "fichier": fichier,
        "radiance": radiance,
        "lilith_variance": 120.3,
        "shannon_entropy": 2.1,
        "phi_ratio": 1.623,
        "zeta_score": 0.654,
        "fibonacci_distance": 1.2,
        "resistance": 0.05,
        "fonctions": [
            {"nom": "process_data", "complexite": 28, "ligne": 42},
            {"nom": "load_config", "complexite": 12, "ligne": 10},
        ],
        "oudjat": {"nom": "process_data", "complexite": 28, "ligne": 42},
        "annotations": [
            {
                "categorie": "LILITH",
                "message": "Boucle imbriquée profondeur 3",
                "ligne": 45,
                "niveau": "WARNING",
            }
        ],
        "nb_lignes_total": 150,
    }


class TestPhiVaultInit:
    def test_initialisation_cree_structure(self):
        vault, workspace = _creer_vault_temp()
        try:
            assert os.path.isdir(vault.vault_dir)
            assert os.path.isdir(vault.journal_dir)
            assert os.path.isfile(vault.index_path)
        finally:
            shutil.rmtree(workspace)

    def test_index_initial_vide(self):
        vault, workspace = _creer_vault_temp()
        try:
            index = vault.consulter_index()
            assert index["notes"] == {}
            assert index["version"] == "16.0"
        finally:
            shutil.rmtree(workspace)


class TestPhiVaultEnregistrement:
    def test_enregistrer_audit_cree_note(self):
        vault, workspace = _creer_vault_temp()
        try:
            metriques = _metriques_test()
            note_path = vault.enregistrer_audit(metriques)
            assert os.path.isfile(note_path)
            assert note_path.endswith(".md")
        finally:
            shutil.rmtree(workspace)

    def test_enregistrer_audit_met_a_jour_index(self):
        vault, workspace = _creer_vault_temp()
        try:
            metriques = _metriques_test()
            vault.enregistrer_audit(metriques)
            index = vault.consulter_index()
            assert "test_file.py" in index["notes"]
            assert index["notes"]["test_file.py"]["radiance"] == 82.4
        finally:
            shutil.rmtree(workspace)

    def test_enregistrer_audit_ecrit_journal(self):
        vault, workspace = _creer_vault_temp()
        try:
            metriques = _metriques_test()
            vault.enregistrer_audit(metriques)
            # Vérifier qu'un fichier journal existe
            journaux = os.listdir(vault.journal_dir)
            assert len(journaux) >= 1
            assert journaux[0].endswith(".md")
        finally:
            shutil.rmtree(workspace)

    def test_note_contient_wikilinks(self):
        vault, workspace = _creer_vault_temp()
        try:
            metriques = _metriques_test()
            vault.enregistrer_audit(metriques)
            contenu = vault.lire_note("test_file.py")
            assert contenu is not None
            assert "[[process_data]]" in contenu
            assert "[[load_config]]" in contenu
        finally:
            shutil.rmtree(workspace)

    def test_note_contient_metriques(self):
        vault, workspace = _creer_vault_temp()
        try:
            metriques = _metriques_test()
            vault.enregistrer_audit(metriques)
            contenu = vault.lire_note("test_file.py")
            assert contenu is not None
            assert "82.4" in contenu or "82.40" in contenu
            assert "Radiance" in contenu
        finally:
            shutil.rmtree(workspace)


class TestPhiVaultLecture:
    def test_lire_note_inexistante(self):
        vault, workspace = _creer_vault_temp()
        try:
            assert vault.lire_note("inexistant.py") is None
        finally:
            shutil.rmtree(workspace)

    def test_lire_note_existante(self):
        vault, workspace = _creer_vault_temp()
        try:
            metriques = _metriques_test()
            vault.enregistrer_audit(metriques)
            contenu = vault.lire_note("test_file.py")
            assert contenu is not None
            assert "test_file" in contenu
        finally:
            shutil.rmtree(workspace)


class TestPhiVaultRegressions:
    def test_pas_de_regression_premier_audit(self):
        vault, workspace = _creer_vault_temp()
        try:
            metriques = _metriques_test()
            regressions = vault.detecter_regressions(metriques)
            assert len(regressions) == 0
        finally:
            shutil.rmtree(workspace)

    def test_regression_detectee(self):
        vault, workspace = _creer_vault_temp()
        try:
            # Premier audit avec haute radiance
            metriques1 = _metriques_test(radiance=85.0)
            vault.enregistrer_audit(metriques1)
            # Second audit avec radiance en baisse
            metriques2 = _metriques_test(radiance=70.0)
            regressions = vault.detecter_regressions(metriques2)
            assert len(regressions) == 1
            assert "RÉGRESSION" in regressions[0]
        finally:
            shutil.rmtree(workspace)

    def test_pas_de_regression_amelioration(self):
        vault, workspace = _creer_vault_temp()
        try:
            metriques1 = _metriques_test(radiance=70.0)
            vault.enregistrer_audit(metriques1)
            metriques2 = _metriques_test(radiance=85.0)
            regressions = vault.detecter_regressions(metriques2)
            assert len(regressions) == 0
        finally:
            shutil.rmtree(workspace)


class TestPhiVaultGraph:
    def test_graph_ascii_vault_vide(self):
        vault, workspace = _creer_vault_temp()
        try:
            graph = vault.generer_graph_ascii()
            assert "vide" in graph.lower() or "vault" in graph.lower()
        finally:
            shutil.rmtree(workspace)

    def test_graph_ascii_avec_donnees(self):
        vault, workspace = _creer_vault_temp()
        try:
            vault.enregistrer_audit(_metriques_test("a.py", 90.0))
            vault.enregistrer_audit(_metriques_test("b.py", 50.0))
            graph = vault.generer_graph_ascii()
            assert "a.py" in graph
            assert "b.py" in graph
            assert "█" in graph
        finally:
            shutil.rmtree(workspace)

    def test_graph_dot_format(self):
        vault, workspace = _creer_vault_temp()
        try:
            vault.enregistrer_audit(_metriques_test("x.py", 80.0))
            dot = vault.generer_graph()
            assert "digraph" in dot
            assert "x.py" in dot
        finally:
            shutil.rmtree(workspace)

    def test_graph_dot_couleurs_statut(self):
        vault, workspace = _creer_vault_temp()
        try:
            vault.enregistrer_audit(_metriques_test("green.py", 90.0))
            vault.enregistrer_audit(_metriques_test("red.py", 30.0))
            dot = vault.generer_graph()
            assert "#2ecc71" in dot  # vert pour HERMÉTIQUE
            assert "#e74c3c" in dot  # rouge pour DORMANT
        finally:
            shutil.rmtree(workspace)
