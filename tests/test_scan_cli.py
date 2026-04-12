"""
tests/test_scan_cli.py — Tests pour la commande 'phi scan' (Phase 24).

Couvre :
    - Construction du parseur avec sous-commande scan
    - Collecte de fichiers scan (source + binaire)
    - Exécution du scan en mode console et JSON
    - Intégration avec le harvest fingerprint
    - Affichage du résumé de scan
"""

from __future__ import annotations

import json
import os
import struct
import sys
import tempfile
import textwrap
from unittest.mock import patch

import pytest

from phi_complexity.cli import (
    _construire_parseur,
    _collecter_fichiers_scan,
    _executer_scan,
    _afficher_scan_console,
    _afficher_scan_resume,
)
from phi_complexity.fingerprint import PhiFingerprint


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────


def _safe_unlink(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


CODE_SIMPLE = """
def hello(name):
    return f"Hello, {name}"
"""


def _creer_fichier_temp(code: str, suffix: str = ".py") -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    ) as f:
        f.write(textwrap.dedent(code))
        return f.name


def _creer_bin_temp(donnees: bytes, suffix: str = ".bin") -> str:
    fd, chemin = tempfile.mkstemp(suffix=suffix)
    os.write(fd, donnees)
    os.close(fd)
    return chemin


# ──────────────────────────────────────────────
# TESTS DU PARSEUR
# ──────────────────────────────────────────────


class TestParseurScan:
    def test_scan_subcommande_existe(self):
        """Le parseur a une sous-commande 'scan'."""
        parser = _construire_parseur()
        args = parser.parse_args(["scan", "test.py"])
        assert args.commande == "scan"
        assert args.cible == "test.py"

    def test_scan_format_json(self):
        parser = _construire_parseur()
        args = parser.parse_args(["scan", "test.py", "--format", "json"])
        assert args.format == "json"

    def test_scan_format_console(self):
        parser = _construire_parseur()
        args = parser.parse_args(["scan", "test.py", "--format", "console"])
        assert args.format == "console"

    def test_scan_harvest_flag(self):
        parser = _construire_parseur()
        args = parser.parse_args(["scan", "test.py", "--harvest"])
        assert args.harvest is True

    def test_scan_output_defaut(self):
        parser = _construire_parseur()
        args = parser.parse_args(["scan", "test.py"])
        assert args.output == ".phi/harvest.jsonl"


# ──────────────────────────────────────────────
# TESTS DE LA COLLECTE DE FICHIERS
# ──────────────────────────────────────────────


class TestCollecterFichiersScan:
    def test_fichier_python(self):
        f = _creer_fichier_temp(CODE_SIMPLE)
        try:
            result = _collecter_fichiers_scan(f)
            assert f in result
        finally:
            _safe_unlink(f)

    def test_fichier_binaire(self):
        f = _creer_bin_temp(b"\x7fELF" + b"\x00" * 100, suffix=".elf")
        try:
            result = _collecter_fichiers_scan(f)
            assert f in result
        finally:
            _safe_unlink(f)

    def test_fichier_quelconque_accepte(self):
        """Un fichier sans extension connue est quand même accepté (scan direct)."""
        f = _creer_bin_temp(b"\x00" * 10, suffix=".xyz")
        try:
            result = _collecter_fichiers_scan(f)
            assert f in result
        finally:
            _safe_unlink(f)

    def test_dossier_avec_mix(self, tmp_path):
        """Un dossier avec mix de fichiers source et binaires."""
        (tmp_path / "hello.py").write_text("def f(): pass")
        (tmp_path / "lib.so").write_bytes(b"\x7fELF" + b"\x00" * 100)
        (tmp_path / "readme.txt").write_text("doc")
        result = _collecter_fichiers_scan(str(tmp_path))
        noms = [os.path.basename(f) for f in result]
        assert "hello.py" in noms
        assert "lib.so" in noms
        assert "readme.txt" not in noms

    def test_dossier_inexistant(self):
        result = _collecter_fichiers_scan("/tmp/phi_dossier_inexistant_xyz")
        assert result == []


# ──────────────────────────────────────────────
# TESTS DE L'EXÉCUTION SCAN
# ──────────────────────────────────────────────


class TestExecuterScan:
    def test_scan_console_python(self, capsys):
        """Le scan d'un fichier Python affiche le résultat en console."""
        f = _creer_fichier_temp(CODE_SIMPLE)
        try:
            parser = _construire_parseur()
            args = parser.parse_args(["scan", f])
            code = _executer_scan(args, [f])
            captured = capsys.readouterr()
            assert "SAIN" in captured.out or "SUSPECT" in captured.out
            assert code == 0 or code == 1
        finally:
            _safe_unlink(f)

    def test_scan_json_python(self, capsys):
        """Le scan en mode JSON retourne un JSON valide."""
        f = _creer_fichier_temp(CODE_SIMPLE)
        try:
            parser = _construire_parseur()
            args = parser.parse_args(["scan", f, "--format", "json"])
            _executer_scan(args, [f])
            captured = capsys.readouterr()
            data = json.loads(captured.out)
            assert "vecteur" in data
            assert "classification" in data
            assert "score_anomalie" in data
        finally:
            _safe_unlink(f)

    def test_scan_fichier_inexistant(self, capsys):
        """Le scan d'un fichier inexistant affiche une erreur."""
        parser = _construire_parseur()
        args = parser.parse_args(["scan", "/tmp/phi_inexistant.py"])
        _executer_scan(args, ["/tmp/phi_inexistant.py"])
        captured = capsys.readouterr()
        assert "erreur" in captured.out.lower() or "❌" in captured.out

    def test_scan_resume_affiche(self, capsys):
        """Le résumé final est affiché en mode console."""
        f = _creer_fichier_temp(CODE_SIMPLE)
        try:
            parser = _construire_parseur()
            args = parser.parse_args(["scan", f])
            _executer_scan(args, [f])
            captured = capsys.readouterr()
            assert "SCAN ANTIVIRAL" in captured.out
        finally:
            _safe_unlink(f)


# ──────────────────────────────────────────────
# TESTS DES FONCTIONS D'AFFICHAGE
# ──────────────────────────────────────────────


class TestAffichageScan:
    def test_afficher_scan_console(self, capsys):
        fp = PhiFingerprint(
            vecteur=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            score_anomalie=0.35,
            classification="SAIN",
            nb_sections=5,
            format_source="python",
        )
        _afficher_scan_console("test.py", fp)
        captured = capsys.readouterr()
        assert "test.py" in captured.out
        assert "SAIN" in captured.out
        assert "python" in captured.out

    def test_afficher_scan_console_suspect(self, capsys):
        fp = PhiFingerprint(
            vecteur=[0.9] * 8,
            score_anomalie=0.75,
            classification="SUSPECT",
            nb_sections=10,
            format_source="elf",
        )
        _afficher_scan_console("malware.elf", fp)
        captured = capsys.readouterr()
        assert "SUSPECT" in captured.out

    def test_afficher_scan_console_malveillant(self, capsys):
        fp = PhiFingerprint(
            vecteur=[1.0] * 8,
            score_anomalie=0.95,
            classification="MALVEILLANT",
            nb_sections=20,
            format_source="pe",
        )
        _afficher_scan_console("virus.exe", fp)
        captured = capsys.readouterr()
        assert "MALVEILLANT" in captured.out

    def test_afficher_resume_sans_suspects(self, capsys):
        _afficher_scan_resume(5, 0)
        captured = capsys.readouterr()
        assert "Aucune menace" in captured.out
        assert "5" in captured.out

    def test_afficher_resume_avec_suspects(self, capsys):
        _afficher_scan_resume(10, 3)
        captured = capsys.readouterr()
        assert "3" in captured.out
        assert "7" in captured.out  # 10 - 3 = 7 sains


# ──────────────────────────────────────────────
# TEST HARVEST FINGERPRINT
# ──────────────────────────────────────────────


class TestHarvestFingerprint:
    def test_collecter_fingerprint(self):
        """HarvestEngine.collecter_fingerprint inclut le fingerprint."""
        from phi_complexity.harvest import HarvestEngine

        code_file = _creer_fichier_temp(CODE_SIMPLE)
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
            tmp.close()
            engine = HarvestEngine(sortie=tmp.name)
            try:
                vecteur = engine.collecter_fingerprint(code_file)
                assert "fingerprint" in vecteur
                fp = vecteur["fingerprint"]
                assert "vecteur" in fp
                assert "classification" in fp
                assert "score_anomalie" in fp
            finally:
                _safe_unlink(tmp.name)
        finally:
            _safe_unlink(code_file)

    def test_collecter_et_exporter_fingerprint(self):
        """collecter_et_exporter_fingerprint persiste dans JSONL."""
        from phi_complexity.harvest import HarvestEngine

        code_file = _creer_fichier_temp(CODE_SIMPLE)
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
            tmp.close()
            engine = HarvestEngine(sortie=tmp.name)
            try:
                engine.collecter_et_exporter_fingerprint(code_file)
                vecteurs = engine.charger_vecteurs()
                assert len(vecteurs) == 1
                assert "fingerprint" in vecteurs[0]
            finally:
                _safe_unlink(tmp.name)
        finally:
            _safe_unlink(code_file)


# ──────────────────────────────────────────────
# TEST BAYESIAN AVEC FINGERPRINT
# ──────────────────────────────────────────────


class TestBayesianFingerprint:
    def test_score_avec_fingerprint(self):
        """Le corrélateur accepte score_fingerprint sans erreur."""
        from phi_complexity.sentinel.bayesian import BayesianCorrelator

        corr = BayesianCorrelator()
        score = corr.calculer_score(score_fingerprint=0.5)
        assert score.score_final > 0.0

    def test_fingerprint_augmente_score(self):
        """Un fingerprint élevé augmente le score de menace."""
        from phi_complexity.sentinel.bayesian import BayesianCorrelator

        corr = BayesianCorrelator()
        score_sans = corr.calculer_score()
        score_avec = corr.calculer_score(score_fingerprint=0.8)
        assert score_avec.score_final > score_sans.score_final

    def test_fingerprint_dans_facteurs(self):
        """Un score fingerprint élevé apparaît dans les facteurs."""
        from phi_complexity.sentinel.bayesian import BayesianCorrelator

        corr = BayesianCorrelator()
        score = corr.calculer_score(score_fingerprint=0.5)
        # With score >= 0.30, fingerprint should appear in facteurs
        facteurs_text = " ".join(score.facteurs)
        assert "Fingerprint" in facteurs_text or "fingerprint" in facteurs_text.lower()
