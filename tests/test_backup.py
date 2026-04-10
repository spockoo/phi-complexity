"""
tests/test_backup.py — Tests du système de Sécurité Maât (backup avant mutation).
"""

import os
import shutil
import tempfile

from phi_complexity.backup import SecuriteMaat


class TestSecuriteMaat:

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.securite = SecuriteMaat(workspace_root=self.tmpdir)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _creer_fichier(self, contenu: str = "x = 1\n") -> str:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        )
        f.write(contenu)
        f.close()
        return f.name

    # ──────────────── Initialisation ────────────────

    def test_initialise_dossiers(self):
        assert os.path.isdir(self.securite.phi_dir)
        assert os.path.isdir(self.securite.backup_dir)

    # ──────────────── sauvegarder() ────────────────

    def test_sauvegarder_cree_fichier_bak(self):
        fichier = self._creer_fichier("code original\n")
        try:
            chemin_bak = self.securite.sauvegarder(fichier)
            assert chemin_bak != ""
            assert os.path.exists(chemin_bak)
            assert chemin_bak.endswith(".bak")
        finally:
            os.unlink(fichier)

    def test_sauvegarder_contenu_identique(self):
        fichier = self._creer_fichier("contenu spécial 42\n")
        try:
            chemin_bak = self.securite.sauvegarder(fichier)
            with open(chemin_bak, encoding="utf-8") as f:
                assert f.read() == "contenu spécial 42\n"
        finally:
            os.unlink(fichier)

    def test_sauvegarder_fichier_inexistant(self):
        """sauvegarder() retourne '' si le fichier n'existe pas."""
        chemin = self.securite.sauvegarder("/chemin/inexistant.py")
        assert chemin == ""

    def test_sauvegarder_plusieurs_fois(self):
        """Plusieurs sauvegardes génèrent plusieurs .bak (timestamps distincts)."""
        from unittest.mock import patch

        fichier = self._creer_fichier("v1\n")
        try:
            with patch("phi_complexity.backup.time.time", side_effect=[1000.0, 2000.0]):
                self.securite.sauvegarder(fichier)
                self.securite.sauvegarder(fichier)
            nom_base = os.path.basename(fichier)
            backups = self.securite._lister_backups(nom_base)
            assert len(backups) == 2
        finally:
            os.unlink(fichier)

    # ──────────────── restaurer_dernier() ────────────────

    def test_restaurer_dernier_restaure_contenu(self):
        fichier = self._creer_fichier("contenu original\n")
        try:
            self.securite.sauvegarder(fichier)
            # Modifier le fichier
            with open(fichier, "w", encoding="utf-8") as f:
                f.write("contenu modifié\n")
            ok = self.securite.restaurer_dernier(fichier)
            assert ok is True
            with open(fichier, encoding="utf-8") as f:
                assert f.read() == "contenu original\n"
        finally:
            os.unlink(fichier)

    def test_restaurer_dernier_sans_backup(self):
        """Sans backup, restaurer_dernier retourne False."""
        fichier = self._creer_fichier()
        try:
            ok = self.securite.restaurer_dernier(fichier)
            assert ok is False
        finally:
            os.unlink(fichier)

    def test_restaurer_dernier_prend_le_plus_recent(self):
        """Restaure bien la sauvegarde la plus récente."""
        from unittest.mock import patch

        fichier = self._creer_fichier("v1\n")
        try:
            with patch("phi_complexity.backup.time.time", side_effect=[1000.0, 2000.0]):
                self.securite.sauvegarder(fichier)  # sauvegarde v1 → ts=1000
                with open(fichier, "w", encoding="utf-8") as f:
                    f.write("v2\n")
                self.securite.sauvegarder(fichier)  # sauvegarde v2 → ts=2000
            # Restauration → doit donner v2 (le dernier backup)
            with open(fichier, "w", encoding="utf-8") as f:
                f.write("v3\n")
            self.securite.restaurer_dernier(fichier)
            with open(fichier, encoding="utf-8") as f:
                assert f.read() == "v2\n"
        finally:
            os.unlink(fichier)

    # ──────────────── _purger_anciens_backups() ────────────────

    def test_purger_anciens_backups(self):
        """La purge garde au maximum `limite` fichiers."""
        from unittest.mock import patch

        fichier = self._creer_fichier()
        try:
            timestamps = [float(1000 + i) for i in range(12)]
            with patch("phi_complexity.backup.time.time", side_effect=timestamps):
                for _ in range(12):
                    self.securite.sauvegarder(fichier)
            nom_base = os.path.basename(fichier)
            backups = self.securite._lister_backups(nom_base)
            assert len(backups) <= 10
        finally:
            os.unlink(fichier)
