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
        """enregistrer_magics enregistre les 3 commandes."""
        pytest.importorskip("IPython")
        registered = self._setup_magics()
        assert len(registered) == 3

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
