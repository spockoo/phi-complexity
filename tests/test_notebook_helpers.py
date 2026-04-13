"""Tests for phi_complexity.notebook_helpers module."""

from __future__ import annotations

import importlib
import json
import os
from typing import Any, Dict
from unittest import mock

import pytest

from phi_complexity.notebook_helpers import (
    charger_metriques,
    charger_harvest,
    matrice_interactions_zero,
    tableau_zero_morphogenetique,
)

# ────────────────────────────────────────────────────────
# FIXTURES
# ────────────────────────────────────────────────────────

FICHIER_SIMPLE = """
def bonjour():
    return "Bonjour le monde"

def additionner(a, b):
    return a + b
"""


@pytest.fixture()
def fichier_py(tmp_path: Any) -> str:
    """Crée un fichier Python temporaire minimal."""
    chemin = os.path.join(str(tmp_path), "test_nb.py")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(FICHIER_SIMPLE)
    return chemin


@pytest.fixture()
def dossier_py(tmp_path: Any) -> str:
    """Crée un dossier avec plusieurs fichiers Python."""
    for nom in ("alpha.py", "beta.py"):
        chemin = os.path.join(str(tmp_path), nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(FICHIER_SIMPLE)
    # Aussi un fichier __init__.py qui doit être ignoré
    init = os.path.join(str(tmp_path), "__init__.py")
    with open(init, "w", encoding="utf-8") as f:
        f.write("")
    return str(tmp_path)


@pytest.fixture()
def fichier_harvest(tmp_path: Any) -> str:
    """Crée un fichier JSONL de harvest."""
    chemin = os.path.join(str(tmp_path), "harvest.jsonl")
    vecteurs = [
        {"radiance": 85.0, "vecteur_phi": [0.85, 0.1, 0.5, 0.02, 0.7]},
        {"radiance": 60.0, "vecteur_phi": [0.60, 0.3, 0.8, 0.15, 0.5]},
    ]
    with open(chemin, "w", encoding="utf-8") as f:
        for v in vecteurs:
            f.write(json.dumps(v) + "\n")
    return chemin


# ────────────────────────────────────────────────────────
# TESTS — charger_metriques
# ────────────────────────────────────────────────────────


class TestChargerMetriques:
    def test_fichier_unique(self, fichier_py: str) -> None:
        resultats = charger_metriques(fichier_py)
        assert len(resultats) == 1
        assert "radiance" in resultats[0]
        assert "phi_ratio" in resultats[0]

    def test_dossier(self, dossier_py: str) -> None:
        resultats = charger_metriques(dossier_py)
        assert len(resultats) == 2  # alpha.py et beta.py (pas __init__.py)

    def test_chemin_inexistant(self) -> None:
        resultats = charger_metriques("/tmp/inexistant_xyz_123.py")
        assert resultats == []

    def test_dossier_vide(self, tmp_path: Any) -> None:
        resultats = charger_metriques(str(tmp_path))
        assert resultats == []

    def test_fichier_invalide_dans_dossier(self, tmp_path: Any) -> None:
        """Un .py invalide ne fait pas crasher le parcours (lignes 56-57)."""
        bon = os.path.join(str(tmp_path), "bon.py")
        with open(bon, "w", encoding="utf-8") as f:
            f.write(FICHIER_SIMPLE)
        mauvais = os.path.join(str(tmp_path), "mauvais.py")
        with open(mauvais, "w", encoding="utf-8") as f:
            f.write("def (\n")  # SyntaxError
        resultats = charger_metriques(str(tmp_path))
        assert len(resultats) == 1  # Seul bon.py passe


# ────────────────────────────────────────────────────────
# TESTS — charger_harvest
# ────────────────────────────────────────────────────────


class TestChargerHarvest:
    def test_chargement_jsonl(self, fichier_harvest: str) -> None:
        vecteurs = charger_harvest(fichier_harvest)
        assert len(vecteurs) == 2
        assert vecteurs[0]["radiance"] == 85.0
        assert vecteurs[1]["radiance"] == 60.0

    def test_fichier_inexistant(self) -> None:
        vecteurs = charger_harvest("/tmp/inexistant_harvest_xyz.jsonl")
        assert vecteurs == []

    def test_fichier_vide(self, tmp_path: Any) -> None:
        chemin = os.path.join(str(tmp_path), "empty.jsonl")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("")
        vecteurs = charger_harvest(chemin)
        assert vecteurs == []

    def test_lignes_vides_ignorees(self, tmp_path: Any) -> None:
        chemin = os.path.join(str(tmp_path), "sparse.jsonl")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write('{"a": 1}\n\n\n{"b": 2}\n')
        vecteurs = charger_harvest(chemin)
        assert len(vecteurs) == 2


class TestBoucleZeroNotebookHelpers:
    def test_matrice_interactions_zero(self) -> None:
        matrice = matrice_interactions_zero()
        assert len(matrice) == 4
        assert any(item["formulation"] == "Z_phi" for item in matrice)

    def test_tableau_zero_morphogenetique(self) -> None:
        metriques = [
            {
                "zero_morphogenetic_state": "PRE_ZERO",
                "quasicrystal_coherence": 0.3,
            },
            {
                "zero_morphogenetic_state": "POST_RENAISSANCE",
                "quasicrystal_coherence": 0.85,
            },
        ]
        tableau = tableau_zero_morphogenetique(metriques)
        assert "PRE_ZERO" in tableau
        assert "POST_RENAISSANCE" in tableau


# ────────────────────────────────────────────────────────
# TESTS — Visualisations (sans matplotlib)
# ────────────────────────────────────────────────────────


class TestVisualisationsSansMatplotlib:
    """Test que les fonctions lèvent ImportError sans matplotlib."""

    def test_radar_radiance_import_error(self) -> None:
        metriques: Dict[str, Any] = {"radiance": 80, "resistance": 0.5}
        with mock.patch.dict(
            "sys.modules", {"matplotlib": None, "matplotlib.pyplot": None}
        ):
            import phi_complexity.notebook_helpers as nh

            importlib.reload(nh)
            with pytest.raises(ImportError, match="matplotlib"):
                nh.radar_radiance(metriques)

    def test_carte_heisenberg_import_error(self) -> None:
        with mock.patch.dict(
            "sys.modules", {"matplotlib": None, "matplotlib.pyplot": None}
        ):
            import phi_complexity.notebook_helpers as nh

            importlib.reload(nh)
            with pytest.raises(ImportError, match="matplotlib"):
                nh.carte_heisenberg([])

    def test_spirale_doree_import_error(self) -> None:
        with mock.patch.dict(
            "sys.modules", {"matplotlib": None, "matplotlib.pyplot": None}
        ):
            import phi_complexity.notebook_helpers as nh

            importlib.reload(nh)
            with pytest.raises(ImportError, match="matplotlib"):
                nh.spirale_doree(75.0)


# ────────────────────────────────────────────────────────
# TESTS — Visualisations (avec matplotlib si disponible)
# ────────────────────────────────────────────────────────


class TestVisualisationsAvecMatplotlib:
    """Test les fonctions de visualisation si matplotlib est installé."""

    @pytest.fixture(autouse=True)
    def _check_matplotlib(self) -> None:
        pytest.importorskip("matplotlib")
        pytest.importorskip("numpy")

    def _metriques_exemple(self) -> Dict[str, Any]:
        return {
            "fichier": "test.py",
            "radiance": 82.0,
            "resistance": 0.45,
            "lilith_variance": 120.0,
            "shannon_entropy": 2.1,
            "phi_ratio": 1.62,
            "phi_ratio_delta": 0.002,
            "fibonacci_entropy": 2.5,
            "heisenberg_tension": 0.8,
        }

    def test_radar_radiance(self) -> None:
        import matplotlib

        matplotlib.use("Agg")

        from phi_complexity.notebook_helpers import radar_radiance

        ax = radar_radiance(self._metriques_exemple())
        assert ax is not None

    def test_radar_radiance_with_ax(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from phi_complexity.notebook_helpers import radar_radiance

        fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
        result = radar_radiance(self._metriques_exemple(), ax=ax)
        assert result is ax
        plt.close(fig)

    def test_carte_heisenberg(self) -> None:
        import matplotlib

        matplotlib.use("Agg")

        from phi_complexity.notebook_helpers import carte_heisenberg

        metriques_list = [self._metriques_exemple()]
        ax = carte_heisenberg(metriques_list)
        assert ax is not None

    def test_carte_heisenberg_empty(self) -> None:
        import matplotlib

        matplotlib.use("Agg")

        from phi_complexity.notebook_helpers import carte_heisenberg

        ax = carte_heisenberg([])
        assert ax is not None

    def test_carte_heisenberg_zero_variance(self) -> None:
        import matplotlib

        matplotlib.use("Agg")

        from phi_complexity.notebook_helpers import carte_heisenberg

        m = self._metriques_exemple()
        m["lilith_variance"] = 0
        m["fibonacci_entropy"] = 0
        ax = carte_heisenberg([m])
        assert ax is not None

    def test_spirale_doree(self) -> None:
        import matplotlib

        matplotlib.use("Agg")

        from phi_complexity.notebook_helpers import spirale_doree

        ax = spirale_doree(85.0)
        assert ax is not None

    def test_spirale_doree_with_ax(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from phi_complexity.notebook_helpers import spirale_doree

        fig, ax = plt.subplots()
        result = spirale_doree(75.0, ax=ax)
        assert result is ax
        plt.close(fig)


# ────────────────────────────────────────────────────────
# TESTS — Magic commands
# ────────────────────────────────────────────────────────


class TestMagicCommands:
    def test_enregistrer_sans_ipython(self) -> None:
        """enregistrer_magics ne fait rien sans IPython."""
        with mock.patch.dict(
            "sys.modules",
            {
                "IPython": None,
                "IPython.core": None,
                "IPython.core.magic": None,
            },
        ):
            import phi_complexity.notebook_helpers as nh

            importlib.reload(nh)
            nh.enregistrer_magics()

    def test_enregistrer_ipython_get_none(self) -> None:
        """enregistrer_magics ne fait rien si get_ipython() retourne None."""
        pytest.importorskip("IPython")
        import phi_complexity.notebook_helpers as nh

        importlib.reload(nh)
        with mock.patch("IPython.get_ipython", return_value=None):
            nh.enregistrer_magics()

    def _setup_magics(self) -> list[Any]:
        """Helper: enregistre les magics et retourne la liste des fonctions."""
        import IPython.core.magic as ipm

        registered: list[Any] = []

        import phi_complexity.notebook_helpers as nh

        importlib.reload(nh)
        with mock.patch("IPython.get_ipython", return_value=mock.MagicMock()):
            with mock.patch.object(
                ipm,
                "register_line_magic",
                lambda f: registered.append(f) or f,
            ):
                nh.enregistrer_magics()
        return registered

    def test_enregistrer_avec_ipython_actif(self) -> None:
        """enregistrer_magics enregistre les 4 commandes."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        assert len(registered) == 4

    def test_phi_check_magic_vide(self, capsys: Any) -> None:
        """phi_check sans argument affiche l'usage."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        registered[0]("")
        assert "Usage" in capsys.readouterr().out

    def test_phi_check_magic_fichier(self, fichier_py: str, capsys: Any) -> None:
        """phi_check sur un fichier valide affiche la radiance."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        registered[0](fichier_py)
        assert "R=" in capsys.readouterr().out

    def test_phi_check_magic_inexistant(self, capsys: Any) -> None:
        """phi_check sur un chemin inexistant affiche un message."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        registered[0]("/tmp/inexistant_xyz_abc.py")
        assert "Aucun fichier" in capsys.readouterr().out

    def test_phi_report_magic_vide(self, capsys: Any) -> None:
        """phi_report sans argument affiche l'usage."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        registered[1]("")
        assert "Usage" in capsys.readouterr().out

    def test_phi_spiral_magic_vide(self, capsys: Any) -> None:
        """phi_spiral sans argument affiche l'usage."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        registered[2]("")
        assert "Usage" in capsys.readouterr().out

    def test_phi_spiral_magic_erreur(self, capsys: Any) -> None:
        """phi_spiral sur fichier inexistant affiche l'erreur."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        registered[2]("/tmp/inexistant_xyz_spiral.py")
        assert "Erreur" in capsys.readouterr().out

    def test_enregistrer_avec_ipython_4_magics(self) -> None:
        """enregistrer_magics enregistre 4 commandes (check, report, spiral, sentinel)."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        assert len(registered) == 4

    def test_phi_sentinel_magic_default(self, capsys: Any) -> None:
        """phi_sentinel sans argument exécute le diagnostic."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        registered[3]("")
        out = capsys.readouterr().out
        assert "PHI-SENTINEL" in out or "Score" in out


# ────────────────────────────────────────────────────────
# TESTS — diagnostic_systeme
# ────────────────────────────────────────────────────────


class TestDiagnosticSysteme:
    """Tests pour la fonction diagnostic_systeme."""

    def test_diagnostic_sans_code(self) -> None:
        from phi_complexity.notebook_helpers import diagnostic_systeme

        result = diagnostic_systeme()
        assert "events" in result
        assert "traces" in result
        assert "stats_telemetrie" in result
        assert "signaux" in result
        assert "score" in result
        assert "alertes" in result
        assert "rapport_console" in result
        assert "metriques" in result
        assert "politique" in result
        assert result["metriques"] == []

    def test_diagnostic_avec_code(self, fichier_py: str) -> None:
        from phi_complexity.notebook_helpers import diagnostic_systeme

        result = diagnostic_systeme(cible_code=fichier_py)
        assert len(result["metriques"]) == 1
        assert "radiance" in result["metriques"][0]

    def test_diagnostic_avec_score_commit(self) -> None:
        from phi_complexity.notebook_helpers import diagnostic_systeme

        result = diagnostic_systeme(score_commit=0.5)
        assert result["score"].score_commit == 0.5

    def test_diagnostic_rapport_console(self) -> None:
        from phi_complexity.notebook_helpers import diagnostic_systeme

        result = diagnostic_systeme()
        assert isinstance(result["rapport_console"], str)
        assert "PHI-SENTINEL" in result["rapport_console"]

    def test_diagnostic_politique(self) -> None:
        from phi_complexity.notebook_helpers import diagnostic_systeme

        result = diagnostic_systeme()
        politique = result["politique"]
        assert "bloquer_pr" in politique
        assert "escalader" in politique
        assert "isoler" in politique
        assert "notifier" in politique

    def test_diagnostic_stats_telemetrie(self) -> None:
        from phi_complexity.notebook_helpers import diagnostic_systeme

        result = diagnostic_systeme()
        stats = result["stats_telemetrie"]
        assert "total" in stats
        assert "info" in stats


# ────────────────────────────────────────────────────────
# TESTS — tableau_diagnostic
# ────────────────────────────────────────────────────────


class TestTableauDiagnostic:
    """Tests pour la fonction tableau_diagnostic."""

    def test_tableau_complet(self) -> None:
        from phi_complexity.notebook_helpers import (
            diagnostic_systeme,
            tableau_diagnostic,
        )

        diag = diagnostic_systeme()
        rapport = tableau_diagnostic(diag)
        assert "PHI-SENTINEL" in rapport
        assert "DIAGNOSTIC SYSTÈME COMPLET" in rapport
        assert "Télémétrie" in rapport

    def test_tableau_vide(self) -> None:
        from phi_complexity.notebook_helpers import tableau_diagnostic

        rapport = tableau_diagnostic({})
        assert "PHI-SENTINEL" in rapport
        assert "Télémétrie" in rapport

    def test_tableau_avec_politique_actions(self) -> None:
        from phi_complexity.notebook_helpers import tableau_diagnostic

        diag = {
            "score": None,
            "stats_telemetrie": {
                "total": 0,
                "info": 0,
                "attention": 0,
                "suspect": 0,
                "critique": 0,
            },
            "alertes": [],
            "signaux": [],
            "politique": {
                "bloquer_pr": True,
                "escalader": True,
                "isoler": False,
                "notifier": True,
            },
        }
        rapport = tableau_diagnostic(diag)
        assert "BLOQUER PR" in rapport
        assert "ESCALADER" in rapport


# ────────────────────────────────────────────────────────
# TESTS — radar_menaces
# ────────────────────────────────────────────────────────


class TestRadarMenaces:
    """Tests pour la visualisation radar_menaces."""

    @pytest.fixture(autouse=True)
    def _check_matplotlib(self) -> None:
        pytest.importorskip("matplotlib")
        pytest.importorskip("numpy")

    def test_radar_liste_vide(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        from phi_complexity.notebook_helpers import radar_menaces

        ax = radar_menaces([])
        assert ax is not None

    def test_radar_avec_signaux(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        from phi_complexity.sentinel import SignalComportemental, TypeBehavior
        from phi_complexity.notebook_helpers import radar_menaces

        signaux = [
            SignalComportemental(
                type=TypeBehavior.C2,
                confiance=0.75,
                description="Test C2",
                traces_source=["test"],
                mitre_technique="T1071",
            ),
        ]
        ax = radar_menaces(signaux)
        assert ax is not None

    def test_radar_depuis_diagnostic(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        from phi_complexity.notebook_helpers import radar_menaces

        diag = {"signaux": []}
        ax = radar_menaces(diag)
        assert ax is not None

    def test_radar_avec_ax(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from phi_complexity.notebook_helpers import radar_menaces

        fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
        result = radar_menaces([], ax=ax)
        assert result is ax
        plt.close(fig)

    def test_radar_import_error(self) -> None:
        with mock.patch.dict(
            "sys.modules", {"matplotlib": None, "matplotlib.pyplot": None}
        ):
            import phi_complexity.notebook_helpers as nh

            importlib.reload(nh)
            with pytest.raises(ImportError, match="matplotlib"):
                nh.radar_menaces([])


# ────────────────────────────────────────────────────────
# TESTS — carte_entropie_penrose
# ────────────────────────────────────────────────────────


class TestCarteEntropiePenrose:
    """Tests pour la visualisation carte_entropie_penrose."""

    @pytest.fixture(autouse=True)
    def _check_matplotlib(self) -> None:
        pytest.importorskip("matplotlib")

    def _metriques_exemple(self) -> list[Dict[str, Any]]:
        return [
            {
                "fichier": "alpha.py",
                "radiance": 82.0,
                "fibonacci_entropy": 2.1,
                "phi_ratio_delta": 0.05,
            },
            {
                "fichier": "beta.py",
                "radiance": 55.0,
                "fibonacci_entropy": 3.5,
                "phi_ratio_delta": 1.2,
            },
        ]

    def test_carte_basique(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        from phi_complexity.notebook_helpers import carte_entropie_penrose

        ax = carte_entropie_penrose(self._metriques_exemple())
        assert ax is not None

    def test_carte_liste_vide(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        from phi_complexity.notebook_helpers import carte_entropie_penrose

        ax = carte_entropie_penrose([])
        assert ax is not None

    def test_carte_avec_ax(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from phi_complexity.notebook_helpers import carte_entropie_penrose

        fig, ax = plt.subplots()
        result = carte_entropie_penrose(self._metriques_exemple(), ax=ax)
        assert result is ax
        plt.close(fig)

    def test_carte_phi_delta_zero(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        from phi_complexity.notebook_helpers import carte_entropie_penrose

        metriques = [
            {
                "fichier": "z.py",
                "radiance": 70,
                "fibonacci_entropy": 1.0,
                "phi_ratio_delta": 0.0,
            },
        ]
        ax = carte_entropie_penrose(metriques)
        assert ax is not None

    def test_carte_import_error(self) -> None:
        with mock.patch.dict(
            "sys.modules", {"matplotlib": None, "matplotlib.pyplot": None}
        ):
            import phi_complexity.notebook_helpers as nh

            importlib.reload(nh)
            with pytest.raises(ImportError, match="matplotlib"):
                nh.carte_entropie_penrose([{"fichier": "x.py"}])
