"""
tests/test_canvas.py — Tests du Phi Canvas (Phase 17).
"""

import json
import os
import tempfile
import shutil

from phi_complexity.canvas import PhiCanvas, _generer_id, _couleur_statut


def _metriques_test(fichier="test_file.py", radiance=82.4):
    """Retourne des métriques de test."""
    return {
        "fichier": fichier,
        "radiance": radiance,
        "nb_lignes_total": 150,
        "fonctions": [
            {"nom": "process_data", "complexite": 28, "ligne": 42},
            {"nom": "load_config", "complexite": 12, "ligne": 10},
        ],
        "oudjat": {"nom": "process_data", "complexite": 28, "ligne": 42},
    }


class TestCouleurStatut:
    def test_hermetique_vert(self):
        assert _couleur_statut(90.0) == "4"

    def test_en_eveil_jaune(self):
        assert _couleur_statut(70.0) == "5"

    def test_dormant_rouge(self):
        assert _couleur_statut(30.0) == "1"


class TestGenererId:
    def test_id_deterministe(self):
        id1 = _generer_id("test")
        id2 = _generer_id("test")
        assert id1 == id2

    def test_id_longueur(self):
        assert len(_generer_id("test")) == 12

    def test_id_different_pour_textes_differents(self):
        assert _generer_id("a") != _generer_id("b")


class TestPhiCanvasInit:
    def test_canvas_vide(self):
        canvas = PhiCanvas()
        assert len(canvas.nodes) == 0
        assert len(canvas.edges) == 0


class TestPhiCanvasAjoutFichier:
    def test_ajouter_fichier_cree_noeud(self):
        canvas = PhiCanvas()
        node_id = canvas.ajouter_fichier(_metriques_test())
        assert len(canvas.nodes) >= 1
        assert isinstance(node_id, str)
        assert len(node_id) == 12

    def test_ajouter_fichier_avec_fonctions(self):
        canvas = PhiCanvas()
        canvas.ajouter_fichier(_metriques_test())
        # 1 nœud fichier + 2 nœuds fonctions
        assert len(canvas.nodes) == 3
        # 2 arêtes fichier→fonction
        assert len(canvas.edges) == 2

    def test_ajouter_plusieurs_fichiers(self):
        canvas = PhiCanvas()
        canvas.ajouter_fichier(_metriques_test("a.py", 90.0))
        canvas.ajouter_fichier(_metriques_test("b.py", 60.0))
        # 2 fichiers × (1 + 2 fonctions) = 6 nœuds
        assert len(canvas.nodes) == 6


class TestPhiCanvasDependance:
    def test_ajouter_dependance(self):
        canvas = PhiCanvas()
        canvas.ajouter_fichier(_metriques_test("source.py"))
        canvas.ajouter_fichier(_metriques_test("cible.py"))
        canvas.ajouter_dependance("source.py", "cible.py")
        # 2 × (1+2) nœuds = 6, 2 × 2 arêtes fichier→fn + 1 dep = 5
        assert len(canvas.edges) == 5


class TestPhiCanvasExport:
    def test_exporter_json(self):
        canvas = PhiCanvas()
        canvas.ajouter_fichier(_metriques_test())
        json_str = canvas.exporter_json()
        data = json.loads(json_str)
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 3

    def test_exporter_fichier(self):
        canvas = PhiCanvas()
        canvas.ajouter_fichier(_metriques_test())
        tmpdir = tempfile.mkdtemp()
        try:
            chemin = os.path.join(tmpdir, "test.canvas")
            contenu = canvas.exporter(chemin)
            assert os.path.isfile(chemin)
            data = json.loads(contenu)
            assert len(data["nodes"]) == 3
        finally:
            shutil.rmtree(tmpdir)

    def test_exporter_cree_dossier_si_necessaire(self):
        canvas = PhiCanvas()
        canvas.ajouter_fichier(_metriques_test())
        tmpdir = tempfile.mkdtemp()
        try:
            chemin = os.path.join(tmpdir, "sub", "test.canvas")
            canvas.exporter(chemin)
            assert os.path.isfile(chemin)
        finally:
            shutil.rmtree(tmpdir)


class TestPhiCanvasContenu:
    def test_noeud_contient_radiance(self):
        canvas = PhiCanvas()
        canvas.ajouter_fichier(_metriques_test(radiance=85.0))
        # Le premier nœud est le fichier
        texte_fichier = canvas.nodes[0]["text"]
        assert "85.0" in texte_fichier
        assert "Radiance" in texte_fichier

    def test_noeud_couleur_statut(self):
        canvas = PhiCanvas()
        canvas.ajouter_fichier(_metriques_test(radiance=90.0))
        assert canvas.nodes[0]["color"] == "4"  # vert HERMÉTIQUE

    def test_noeud_fonction_couleur_complexite(self):
        canvas = PhiCanvas()
        metriques = _metriques_test()
        metriques["fonctions"] = [{"nom": "simple", "complexite": 10, "ligne": 1}]
        canvas.ajouter_fichier(metriques)
        fn_node = canvas.nodes[1]
        assert fn_node["color"] == "4"  # complexité <= 21 → vert
