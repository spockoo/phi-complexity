"""
tests/test_search.py — Tests du Phi Search (Phase 18).
"""

import json
import os
import tempfile
import shutil

from phi_complexity.search import PhiSearch, _similitude_cosinus


def _creer_search_temp():
    """Crée un environnement de recherche temporaire."""
    workspace = tempfile.mkdtemp()
    phi_dir = os.path.join(workspace, ".phi")
    vault_dir = os.path.join(phi_dir, "vault")
    os.makedirs(vault_dir)
    return PhiSearch(workspace_root=workspace), workspace


def _peupler_index(workspace, fichiers):
    """Remplit l'index du vault avec des fichiers de test."""
    index_path = os.path.join(workspace, ".phi", "vault", "index.json")
    notes = {}
    for fichier, radiance, statut in fichiers:
        notes[fichier] = {
            "note": f"{fichier.replace('.', '_')}.md",
            "radiance": radiance,
            "statut": statut,
            "timestamp": 1234567890,
        }
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"notes": notes, "version": "16.0"}, f)


def _peupler_harvest(workspace, vecteurs):
    """Remplit le fichier harvest avec des vecteurs de test."""
    harvest_path = os.path.join(workspace, ".phi", "harvest.jsonl")
    with open(harvest_path, "w", encoding="utf-8") as f:
        for v in vecteurs:
            f.write(json.dumps(v) + "\n")


# ────────────────────────────────────────────────────────
# TESTS — Similitude Cosinus
# ────────────────────────────────────────────────────────


class TestSimilitudeCosinus:
    def test_vecteurs_identiques(self):
        assert abs(_similitude_cosinus([1, 0, 0], [1, 0, 0]) - 1.0) < 0.001

    def test_vecteurs_orthogonaux(self):
        assert abs(_similitude_cosinus([1, 0, 0], [0, 1, 0])) < 0.001

    def test_vecteur_nul(self):
        assert _similitude_cosinus([0, 0, 0], [1, 2, 3]) == 0.0

    def test_vecteurs_similaires(self):
        sim = _similitude_cosinus([0.8, 0.1, 0.3], [0.9, 0.1, 0.2])
        assert sim > 0.9


# ────────────────────────────────────────────────────────
# TESTS — Recherche par Radiance
# ────────────────────────────────────────────────────────


class TestRechercheParRadiance:
    def test_recherche_vide(self):
        search, workspace = _creer_search_temp()
        try:
            resultats = search.chercher_par_radiance(0, 100)
            assert resultats == []
        finally:
            shutil.rmtree(workspace)

    def test_recherche_filtre_par_intervalle(self):
        search, workspace = _creer_search_temp()
        try:
            _peupler_index(
                workspace,
                [
                    ("a.py", 90.0, "HERMÉTIQUE ✦"),
                    ("b.py", 60.0, "EN ÉVEIL ◈"),
                    ("c.py", 30.0, "DORMANT ░"),
                ],
            )
            resultats = search.chercher_par_radiance(50, 100)
            assert len(resultats) == 2
            fichiers = [r["fichier"] for r in resultats]
            assert "a.py" in fichiers
            assert "b.py" in fichiers
        finally:
            shutil.rmtree(workspace)

    def test_recherche_trie_par_radiance_desc(self):
        search, workspace = _creer_search_temp()
        try:
            _peupler_index(
                workspace,
                [
                    ("a.py", 60.0, "EN ÉVEIL ◈"),
                    ("b.py", 90.0, "HERMÉTIQUE ✦"),
                ],
            )
            resultats = search.chercher_par_radiance(0, 100)
            assert resultats[0]["radiance"] >= resultats[-1]["radiance"]
        finally:
            shutil.rmtree(workspace)


# ────────────────────────────────────────────────────────
# TESTS — Recherche par Statut
# ────────────────────────────────────────────────────────


class TestRechercheParStatut:
    def test_recherche_hermetique(self):
        search, workspace = _creer_search_temp()
        try:
            _peupler_index(
                workspace,
                [
                    ("a.py", 90.0, "HERMÉTIQUE ✦"),
                    ("b.py", 30.0, "DORMANT ░"),
                ],
            )
            resultats = search.chercher_par_statut("HERMÉTIQUE")
            assert len(resultats) == 1
            assert resultats[0]["fichier"] == "a.py"
        finally:
            shutil.rmtree(workspace)

    def test_recherche_dormant(self):
        search, workspace = _creer_search_temp()
        try:
            _peupler_index(
                workspace,
                [
                    ("a.py", 90.0, "HERMÉTIQUE ✦"),
                    ("b.py", 30.0, "DORMANT ░"),
                ],
            )
            resultats = search.chercher_par_statut("DORMANT")
            assert len(resultats) == 1
            assert resultats[0]["fichier"] == "b.py"
        finally:
            shutil.rmtree(workspace)

    def test_recherche_insensible_casse(self):
        search, workspace = _creer_search_temp()
        try:
            _peupler_index(
                workspace,
                [("a.py", 30.0, "DORMANT ░")],
            )
            resultats = search.chercher_par_statut("dormant")
            assert len(resultats) == 1
        finally:
            shutil.rmtree(workspace)


# ────────────────────────────────────────────────────────
# TESTS — Recherche par Similarité
# ────────────────────────────────────────────────────────


class TestRechercheParSimilarite:
    def test_recherche_similarite_vide(self):
        search, workspace = _creer_search_temp()
        try:
            resultats = search.chercher_par_similarite([0.5, 0.2, 0.3, 0.1, 0.4])
            assert resultats == []
        finally:
            shutil.rmtree(workspace)

    def test_recherche_similarite_trouve(self):
        search, workspace = _creer_search_temp()
        try:
            _peupler_harvest(
                workspace,
                [
                    {
                        "radiance": 80.0,
                        "vecteur_phi": [0.8, 0.1, 0.3, 0.05, 0.6],
                        "lilith_variance": 50.0,
                        "shannon_entropy": 2.0,
                        "labels": {"LILITH": 1},
                    }
                ],
            )
            resultats = search.chercher_par_similarite(
                [0.8, 0.1, 0.3, 0.05, 0.6], seuil=0.9
            )
            assert len(resultats) >= 1
        finally:
            shutil.rmtree(workspace)


# ────────────────────────────────────────────────────────
# TESTS — Recherche par Annotations
# ────────────────────────────────────────────────────────


class TestRechercheAnnotations:
    def test_recherche_annotations_vide(self):
        search, workspace = _creer_search_temp()
        try:
            resultats = search.chercher_annotations("LILITH")
            assert resultats == []
        finally:
            shutil.rmtree(workspace)

    def test_recherche_annotations_lilith(self):
        search, workspace = _creer_search_temp()
        try:
            _peupler_harvest(
                workspace,
                [
                    {
                        "radiance": 60.0,
                        "labels": {"LILITH": 3, "SUTURE": 0},
                        "nb_critiques": 1,
                        "timestamp": 123456,
                    },
                    {
                        "radiance": 90.0,
                        "labels": {"LILITH": 0, "SUTURE": 0},
                        "nb_critiques": 0,
                        "timestamp": 123457,
                    },
                ],
            )
            resultats = search.chercher_annotations("LILITH")
            assert len(resultats) == 1
            assert resultats[0]["radiance"] == 60.0
        finally:
            shutil.rmtree(workspace)


# ────────────────────────────────────────────────────────
# TESTS — Rapport de Recherche
# ────────────────────────────────────────────────────────


class TestRapportRecherche:
    def test_rapport_vide(self):
        search, workspace = _creer_search_temp()
        try:
            rapport = search.rapport_recherche([], "Test")
            assert "Aucun résultat" in rapport
        finally:
            shutil.rmtree(workspace)

    def test_rapport_avec_resultats(self):
        search, workspace = _creer_search_temp()
        try:
            resultats = [
                {"fichier": "a.py", "radiance": 90.0, "statut": "HERMÉTIQUE ✦"}
            ]
            rapport = search.rapport_recherche(resultats, "Radiance")
            assert "a.py" in rapport
            assert "90.0" in rapport
        finally:
            shutil.rmtree(workspace)
