"""
tests/test_cli.py — Tests de la CLI via subprocess et fonctions internes.
"""

import os
import sys
import json
import shutil
import tempfile
import textwrap
import subprocess
from phi_complexity.cli import (
    _collecter_fichiers,
    _nom_rapport,
    _executer_check_json,
    _executer_check,
    _executer_report,
    _executer_oracle,
    _executer_harvest,
    _executer_spiral,
    _executer_shield,
    _executer_memory,
    _executer_fund,
    _afficher_bmad,
    _auditer_un_fichier,
    _construire_parseur,
)

CODE_TEST = """
def ajouter(a: float, b: float) -> float:
    return a + b

def multiplier(a: float, b: float) -> float:
    return a * b
"""


def creer_fichier(code: str) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(textwrap.dedent(code))
        return f.name


class TestCollecterFichiers:
    """Tests de la fonction de collecte de fichiers (sans subprocess)."""

    def test_fichier_python_direct(self):
        """Un fichier .py seul est retourné tel quel."""
        fichier = creer_fichier(CODE_TEST)
        try:
            resultat = _collecter_fichiers(fichier)
            assert resultat == [fichier]
        finally:
            os.unlink(fichier)

    def test_fichier_non_python(self):
        """Un fichier non-.py retourne une liste vide."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"hello")
            chemin = f.name
        try:
            assert _collecter_fichiers(chemin) == []
        finally:
            os.unlink(chemin)

    def test_chemin_inexistant(self):
        """Un chemin inexistant retourne une liste vide."""
        assert _collecter_fichiers("/chemin/inexistant/fichier.py") == []

    def test_dossier_collecte_recursif(self):
        """Un dossier retourne tous les .py récursivement."""
        dossier = tempfile.mkdtemp()
        f1 = os.path.join(dossier, "a.py")
        f2 = os.path.join(dossier, "b.txt")
        sous = os.path.join(dossier, "sub")
        os.makedirs(sous)
        f3 = os.path.join(sous, "c.py")
        for f in [f1, f3]:
            with open(f, "w") as fh:
                fh.write("x = 1")
        with open(f2, "w") as fh:
            fh.write("pas python")
        try:
            resultat = _collecter_fichiers(dossier)
            assert f1 in resultat
            assert f3 in resultat
            assert f2 not in resultat
        finally:
            import shutil

            shutil.rmtree(dossier)


class TestFonctionsInternesCLI:
    """Tests des fonctions CLI internes (sans subprocess) pour maximiser la couverture."""

    def _args_check(
        self,
        fichier: str = "/dummy.py",
        fmt: str = "console",
        min_rad: float = 0.0,
        bmad: bool = False,
    ):
        parser = _construire_parseur()
        a = parser.parse_args(
            ["check", fichier, "--format", fmt, "--min-radiance", str(min_rad)]
        )
        a.bmad = bmad
        return a

    def _args_report(self, fichier: str = "/dummy.py", output=None):
        parser = _construire_parseur()
        args = parser.parse_args(["report", fichier])
        args.output = output
        return args

    def _args_oracle(
        self, fichier: str = "/dummy.py", min_rad: float = 70.0, nb_tests: int = 0
    ):
        parser = _construire_parseur()
        return parser.parse_args(
            [
                "oracle",
                fichier,
                "--min-radiance",
                str(min_rad),
                "--nb-tests",
                str(nb_tests),
            ]
        )

    def _args_harvest(
        self, fichier: str = "/dummy.py", output: str = "/tmp/test.jsonl"
    ):
        parser = _construire_parseur()
        return parser.parse_args(["harvest", fichier, "--output", output])

    def _args_shield(
        self,
        fichier: str = "/dummy.py",
        output: str = "/tmp/security.json",
        min_security_score: float = 70.0,
    ):
        parser = _construire_parseur()
        return parser.parse_args(
            [
                "shield",
                fichier,
                "--output",
                output,
                "--min-security-score",
                str(min_security_score),
            ]
        )

    # ──────────────── _auditer_un_fichier() ────────────────

    def test_auditer_un_fichier_console(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            args = self._args_check(fichier)
            code = _auditer_un_fichier(fichier, args)
            out = capsys.readouterr().out
            assert "RADIANCE" in out
            assert code == 0
        finally:
            os.unlink(fichier)

    def test_auditer_un_fichier_min_radiance_echec(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            args = self._args_check(fichier, min_rad=101.0)
            code = _auditer_un_fichier(fichier, args)
            assert code == 1
        finally:
            os.unlink(fichier)

    def test_auditer_un_fichier_inexistant(self, capsys):
        args = self._args_check("/inexistant/file.py")
        code = _auditer_un_fichier("/inexistant/file.py", args)
        out = capsys.readouterr().out
        assert code == 1
        assert "Erreur" in out

    def test_auditer_un_fichier_bmad(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            args = self._args_check(fichier, bmad=True)
            code = _auditer_un_fichier(fichier, args)
            out = capsys.readouterr().out
            assert code == 0
            assert "BMAD" in out or "RADIANCE" in out
        finally:
            os.unlink(fichier)

    # ──────────────── _executer_check() ────────────────

    def test_executer_check_console(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            args = self._args_check(fichier)
            code = _executer_check(args, [fichier])
            assert code == 0
        finally:
            os.unlink(fichier)

    def test_executer_check_json_route(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            args = self._args_check(fichier, fmt="json")
            code = _executer_check(args, [fichier])
            out = capsys.readouterr().out
            assert code == 0
            assert "radiance" in json.loads(out)
        finally:
            os.unlink(fichier)

    # ──────────────── _afficher_bmad() ────────────────

    def test_afficher_bmad(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            _afficher_bmad(fichier)
            out = capsys.readouterr().out
            assert "BMAD" in out or "RÉSISTANCE" in out or "SUPRACONDUCTIVITÉ" in out
        finally:
            os.unlink(fichier)

    # ──────────────── _executer_report() ────────────────

    def test_executer_report(self, capsys, tmp_path):
        fichier = creer_fichier(CODE_TEST)
        sortie = str(tmp_path / "rapport.md")
        try:
            args = self._args_report(fichier, output=sortie)
            code = _executer_report(args, [fichier])
            assert code == 0
            assert os.path.exists(sortie)
        finally:
            os.unlink(fichier)

    def test_executer_report_erreur(self, capsys):
        args = self._args_report("/inexistant.py", output="/tmp/r.md")
        code = _executer_report(args, ["/inexistant.py"])
        assert code == 1

    # ──────────────── _executer_oracle() ────────────────

    def test_executer_oracle(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            args = self._args_oracle(fichier, min_rad=0.0, nb_tests=10)
            _executer_oracle(args, [fichier])
            out = capsys.readouterr().out
            assert "ORACLE" in out or "RADIANCE" in out
        finally:
            os.unlink(fichier)

    # ──────────────── _executer_harvest() ────────────────

    def test_executer_harvest(self, capsys, tmp_path):
        fichier = creer_fichier(CODE_TEST)
        sortie = str(tmp_path / "harvest.jsonl")
        try:
            args = self._args_harvest(fichier, output=sortie)
            code = _executer_harvest(args, [fichier])
            assert code == 0
        finally:
            os.unlink(fichier)

    def test_executer_harvest_fichier_invalide(self, capsys, tmp_path):
        sortie = str(tmp_path / "harvest.jsonl")
        args = self._args_harvest("/inexistant.py", output=sortie)
        code = _executer_harvest(args, ["/inexistant.py"])
        assert code == 1

    # ──────────────── _executer_spiral() ────────────────

    def test_executer_spiral(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            code = _executer_spiral([fichier])
            out = capsys.readouterr().out
            assert code == 0
            assert "SPIRALE" in out or "radiance" in out.lower()
        finally:
            os.unlink(fichier)

    def test_executer_spiral_fichier_invalide(self, capsys):
        code = _executer_spiral(["/inexistant.py"])
        assert code == 1

    # ──────────────── _executer_shield() ────────────────

    def test_executer_shield(self, capsys, tmp_path):
        fichier = creer_fichier(CODE_TEST)
        sortie = str(tmp_path / "security.json")
        try:
            args = self._args_shield(fichier, output=sortie, min_security_score=0.0)
            code = _executer_shield(args, [fichier])
            out = capsys.readouterr().out
            assert code == 0
            assert os.path.exists(sortie)
            assert "Shield" in out
        finally:
            os.unlink(fichier)

    def test_executer_shield_echec_seuil(self, capsys, tmp_path):
        fichier = creer_fichier(CODE_TEST)
        sortie = str(tmp_path / "security.json")
        try:
            args = self._args_shield(fichier, output=sortie, min_security_score=101.0)
            code = _executer_shield(args, [fichier])
            assert code == 1
        finally:
            os.unlink(fichier)

    # ──────────────── _executer_memory() ────────────────

    def test_executer_memory(self, capsys):
        code = _executer_memory()
        out = capsys.readouterr().out
        assert code == 0
        assert "AKASHIQUE" in out or "Akasha" in out

    # ──────────────── _executer_fund() ────────────────

    def test_executer_fund(self, capsys):
        _executer_fund()
        out = capsys.readouterr().out
        assert "SOUVERAINE" in out or "SOUTENIR" in out


class TestExecuterCheckJson:
    """Tests unitaires de _executer_check_json (sans subprocess)."""

    def _args(self, min_radiance: float = 0.0):
        parser = _construire_parseur()
        return parser.parse_args(
            ["check", __file__, "--format", "json", "--min-radiance", str(min_radiance)]
        )

    def test_un_fichier_retourne_objet(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            args = self._args()
            code = _executer_check_json(args, [fichier])
            out = capsys.readouterr().out
            data = json.loads(out)
            assert isinstance(data, dict)
            assert "radiance" in data
            assert code == 0
        finally:
            os.unlink(fichier)

    def test_plusieurs_fichiers_retourne_liste(self, capsys):
        f1 = creer_fichier(CODE_TEST)
        f2 = creer_fichier(CODE_TEST)
        try:
            args = self._args()
            code = _executer_check_json(args, [f1, f2])
            out = capsys.readouterr().out
            data = json.loads(out)
            assert isinstance(data, list)
            assert len(data) == 2
            assert code == 0
        finally:
            os.unlink(f1)
            os.unlink(f2)

    def test_min_radiance_trop_haute_exit1(self, capsys):
        fichier = creer_fichier(CODE_TEST)
        try:
            args = self._args(min_radiance=101.0)
            code = _executer_check_json(args, [fichier])
            assert code == 1
        finally:
            os.unlink(fichier)

    def test_fichier_invalide_json_contient_erreur(self, capsys):
        """Un fichier non-Python renvoie un objet avec 'erreur' dans le JSON."""
        args = self._args()
        code = _executer_check_json(args, ["/fichier/inexistant.py"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "erreur" in data or (isinstance(data, dict) and data.get("erreur"))
        assert code == 1


class TestNomRapport:

    def test_sortie_specifiee(self):
        assert _nom_rapport("mon_script.py", "mon_rapport.md") == "mon_rapport.md"

    def test_sortie_automatique(self):
        """Sans sortie spécifiée, génère RAPPORT_PHI_<nom>.md."""
        assert _nom_rapport("mon_script.py", None) == "RAPPORT_PHI_mon_script.md"

    def test_sortie_avec_chemin(self):
        """Le chemin absolu du fichier source est bien géré."""
        resultat = _nom_rapport("/home/user/src/mon_script.py", None)
        assert resultat == "RAPPORT_PHI_mon_script.md"


class TestCLISubprocess:
    """Tests de la CLI via subprocess — valide le point d'entrée réel."""

    def _phi(self, *args) -> subprocess.CompletedProcess:
        """Lance phi via 'python -m phi_complexity' (cross-platform fiable)."""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "-m", "phi_complexity"] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

    def test_version(self):
        """phi --version retourne la version."""
        res = self._phi("--version")
        assert "phi-complexity" in res.stdout or "phi-complexity" in res.stderr

    def test_check_fichier_simple(self):
        """phi check <fichier> retourne exit code 0 et affiche RADIANCE."""
        fichier = creer_fichier(CODE_TEST)
        try:
            res = self._phi("check", fichier)
            assert res.returncode == 0
            assert "RADIANCE" in res.stdout
        finally:
            os.unlink(fichier)

    def test_check_format_json(self):
        """phi check --format json retourne du JSON valide."""
        fichier = creer_fichier(CODE_TEST)
        try:
            res = self._phi("check", fichier, "--format", "json")
            assert res.returncode == 0
            data = json.loads(res.stdout)
            assert "radiance" in data
        finally:
            os.unlink(fichier)

    def test_check_min_radiance_passe(self):
        """Un fichier harmonieux avec seuil bas → exit 0."""
        fichier = creer_fichier(CODE_TEST)
        try:
            res = self._phi("check", fichier, "--min-radiance", "40")
            assert res.returncode == 0
        finally:
            os.unlink(fichier)

    def test_check_min_radiance_echoue(self):
        """Seuil impossible (101) → exit 1 car radiance <= 100 toujours."""
        fichier = creer_fichier(CODE_TEST)
        try:
            res = self._phi("check", fichier, "--min-radiance", "101")
            assert res.returncode == 1
        finally:
            os.unlink(fichier)

    def test_report_genere_fichier(self):
        """phi report <fichier> génère un .md."""
        fichier = creer_fichier(CODE_TEST)
        fd, sortie = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        os.unlink(sortie)  # phi report doit créer le fichier lui-même
        try:
            res = self._phi("report", fichier, "--output", sortie)
            assert res.returncode == 0
            assert os.path.exists(sortie)
            with open(sortie, encoding="utf-8") as f:
                assert "RADIANCE" in f.read()
        finally:
            os.unlink(fichier)
            if os.path.exists(sortie):
                os.unlink(sortie)

    def test_check_format_json_multifichiers(self):
        """phi check --format json sur plusieurs fichiers → tableau JSON."""
        f1 = creer_fichier(CODE_TEST)
        f2 = creer_fichier(CODE_TEST)
        dossier = tempfile.mkdtemp()
        try:
            shutil.copy(f1, os.path.join(dossier, "a.py"))
            shutil.copy(f2, os.path.join(dossier, "b.py"))
            res = self._phi("check", dossier, "--format", "json")
            assert res.returncode == 0
            data = json.loads(res.stdout)
            assert isinstance(data, list)
            assert len(data) == 2
            assert all("radiance" in item for item in data)
        finally:
            os.unlink(f1)
            os.unlink(f2)
            shutil.rmtree(dossier)

    def test_check_aucun_fichier_supporte(self):
        """phi check sur un dossier vide → exit 1."""
        dossier = tempfile.mkdtemp()
        try:
            # Dossier sans fichiers .py
            res = self._phi("check", dossier)
            assert res.returncode == 1
        finally:
            shutil.rmtree(dossier)

    def test_fund_commande(self):
        """phi fund affiche le message de soutien."""
        res = self._phi("fund")
        assert res.returncode == 0
        assert "SOUVERAINE" in res.stdout or "SOUTENIR" in res.stdout

    def test_spiral_commande(self):
        """phi spiral <fichier> affiche la spirale dorée."""
        fichier = creer_fichier(CODE_TEST)
        try:
            res = self._phi("spiral", fichier)
            assert res.returncode == 0
            assert "SPIRALE" in res.stdout or "radiance" in res.stdout.lower()
        finally:
            os.unlink(fichier)

    def test_spiral_aucun_fichier(self):
        """phi spiral sur un chemin inexistant → exit 1."""
        res = self._phi("spiral", "/chemin/inexistant.py")
        assert res.returncode == 1

    def test_oracle_commande(self):
        """phi oracle <fichier> retourne un rapport d'oracle."""
        fichier = creer_fichier(CODE_TEST)
        try:
            res = self._phi("oracle", fichier)
            assert "ORACLE" in res.stdout or "RADIANCE" in res.stdout
        finally:
            os.unlink(fichier)

    def test_harvest_commande(self):
        """phi harvest <fichier> collecte les vecteurs AST."""
        fichier = creer_fichier(CODE_TEST)
        fd, sortie = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            res = self._phi("harvest", fichier, "--output", sortie)
            assert res.returncode == 0
            assert "vecteur" in res.stdout.lower() or "collecté" in res.stdout
        finally:
            os.unlink(fichier)
            if os.path.exists(sortie):
                os.unlink(sortie)

    def test_memory_commande(self):
        """phi memory n'échoue pas (annales vides ou non)."""
        res = self._phi("memory")
        assert res.returncode == 0
        assert "AKASHIQUE" in res.stdout or "Akasha" in res.stdout

    def test_check_bmad(self):
        """phi check --bmad affiche la résonance des agents."""
        fichier = creer_fichier(CODE_TEST)
        try:
            res = self._phi("check", fichier, "--bmad")
            assert res.returncode == 0
            assert "BMAD" in res.stdout or "RADIANCE" in res.stdout
        finally:
            os.unlink(fichier)

    def test_sans_commande_affiche_aide(self):
        """phi sans argument affiche l'aide et retourne exit 0."""
        res = self._phi()
        assert res.returncode == 0
        assert "phi" in res.stdout.lower() or "phi" in res.stderr.lower()

    def test_check_min_radiance_json(self):
        """phi check --format json --min-radiance 101 → exit 1."""
        fichier = creer_fichier(CODE_TEST)
        try:
            res = self._phi(
                "check", fichier, "--format", "json", "--min-radiance", "101"
            )
            assert res.returncode == 1
            data = json.loads(res.stdout)
            assert "radiance" in data
        finally:
            os.unlink(fichier)
