"""
tests/test_securite.py — Tests du module de sécurité (Phase 20).
"""

import json
import os
import tempfile
import shutil

from phi_complexity.securite import (
    signer_rapport,
    verifier_signature,
    valider_chemin_fichier,
    sanitiser_contenu_asm,
    JournalAudit,
    generer_sbom,
    exporter_sbom,
)

# ────────────────────────────────────────────────────────
# TESTS — Signature des rapports
# ────────────────────────────────────────────────────────


class TestSignatureRapport:
    def test_signer_rapport(self):
        contenu = "Radiance: 85.0"
        signature = signer_rapport(contenu)
        assert "sha256" in signature
        assert "timestamp" in signature
        assert "taille" in signature
        assert len(signature["sha256"]) == 64  # SHA-256 hex

    def test_verifier_signature_valide(self):
        contenu = "Radiance: 85.0"
        signature = signer_rapport(contenu)
        assert verifier_signature(contenu, signature) is True

    def test_verifier_signature_invalide(self):
        contenu = "Radiance: 85.0"
        signature = signer_rapport(contenu)
        assert verifier_signature("Radiance: 90.0", signature) is False

    def test_verifier_signature_timestamp_different(self):
        contenu = "Radiance: 85.0"
        signature = signer_rapport(contenu)
        signature["timestamp"] = "2020-01-01T00:00:00Z"
        assert verifier_signature(contenu, signature) is False


# ────────────────────────────────────────────────────────
# TESTS — Validation des chemins
# ────────────────────────────────────────────────────────


class TestValidationChemin:
    def test_chemin_valide(self):
        f = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
        f.write(b"x = 1\n")
        f.close()
        try:
            assert valider_chemin_fichier(f.name) is True
        finally:
            os.unlink(f.name)

    def test_chemin_inexistant(self):
        assert valider_chemin_fichier("/tmp/inexistant_xyz.py") is False

    def test_chemin_extension_invalide(self):
        f = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
        f.write(b"hello\n")
        f.close()
        try:
            assert valider_chemin_fichier(f.name) is False
        finally:
            os.unlink(f.name)

    def test_chemin_avec_traversal(self):
        assert valider_chemin_fichier("../../etc/passwd") is False

    def test_chemin_avec_null(self):
        assert valider_chemin_fichier("file\x00.py") is False

    def test_extension_asm_valide(self):
        f = tempfile.NamedTemporaryFile(suffix=".asm", delete=False)
        f.write(b"mov eax, 1\n")
        f.close()
        try:
            assert valider_chemin_fichier(f.name) is True
        finally:
            os.unlink(f.name)

    def test_extension_s_valide(self):
        f = tempfile.NamedTemporaryFile(suffix=".s", delete=False)
        f.write(b"mov eax, 1\n")
        f.close()
        try:
            assert valider_chemin_fichier(f.name) is True
        finally:
            os.unlink(f.name)


# ────────────────────────────────────────────────────────
# TESTS — Sanitisation ASM
# ────────────────────────────────────────────────────────


class TestSanitisationASM:
    def test_contenu_normal_inchange(self):
        contenu = "mov eax, 1\nret\n"
        assert sanitiser_contenu_asm(contenu) == contenu

    def test_supprime_caracteres_nuls(self):
        contenu = "mov eax\x00, 1"
        resultat = sanitiser_contenu_asm(contenu)
        assert "\x00" not in resultat

    def test_supprime_caracteres_controle(self):
        contenu = "mov eax\x01\x02\x03, 1"
        resultat = sanitiser_contenu_asm(contenu)
        assert "\x01" not in resultat
        assert "\x02" not in resultat

    def test_preserve_tabulations_et_newlines(self):
        contenu = "\tmov eax, 1\n\tret\n"
        assert sanitiser_contenu_asm(contenu) == contenu


# ────────────────────────────────────────────────────────
# TESTS — Journal d'Audit
# ────────────────────────────────────────────────────────


class TestJournalAudit:
    def test_enregistrer_evenement(self):
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            journal.enregistrer("AUDIT", {"fichier": "test.py", "radiance": 85.0})
            entries = journal.lire_journal()
            assert len(entries) == 1
            assert entries[0]["operation"] == "AUDIT"
        finally:
            shutil.rmtree(workspace)

    def test_journal_append_only(self):
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            journal.enregistrer("AUDIT_1", {"radiance": 80.0})
            journal.enregistrer("AUDIT_2", {"radiance": 90.0})
            entries = journal.lire_journal()
            assert len(entries) == 2
            assert entries[0]["operation"] == "AUDIT_1"
            assert entries[1]["operation"] == "AUDIT_2"
        finally:
            shutil.rmtree(workspace)

    def test_journal_integrite(self):
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            journal.enregistrer("AUDIT", {"radiance": 85.0})
            assert journal.verifier_integrite() is True
        finally:
            shutil.rmtree(workspace)

    def test_journal_vide_integre(self):
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            assert journal.verifier_integrite() is True
        finally:
            shutil.rmtree(workspace)

    def test_lire_journal_limite(self):
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            for i in range(10):
                journal.enregistrer(f"OP_{i}", {"i": i})
            entries = journal.lire_journal(limite=3)
            assert len(entries) == 3
        finally:
            shutil.rmtree(workspace)


# ────────────────────────────────────────────────────────
# TESTS — SBOM
# ────────────────────────────────────────────────────────


class TestSBOM:
    def test_generer_sbom_structure(self):
        sbom = generer_sbom()
        assert sbom["bomFormat"] == "CycloneDX"
        assert "metadata" in sbom
        assert "components" in sbom
        assert sbom["metadata"]["component"]["name"] == "phi-complexity"

    def test_generer_sbom_composants(self):
        sbom = generer_sbom()
        noms = [c["name"] for c in sbom["components"]]
        assert "ast" in noms
        assert "math" in noms
        assert "json" in noms
        assert "hashlib" in noms

    def test_generer_sbom_zero_deps_externes(self):
        sbom = generer_sbom()
        assert sbom["externalDependencies"] == []
        assert sbom["dependencies"] == []

    def test_exporter_sbom_fichier(self):
        tmpdir = tempfile.mkdtemp()
        try:
            chemin = os.path.join(tmpdir, "sbom.json")
            contenu = exporter_sbom(chemin)
            assert os.path.isfile(chemin)
            data = json.loads(contenu)
            assert data["bomFormat"] == "CycloneDX"
        finally:
            shutil.rmtree(tmpdir)

    def test_exporter_sbom_cree_dossier(self):
        tmpdir = tempfile.mkdtemp()
        try:
            chemin = os.path.join(tmpdir, "sub", "sbom.json")
            exporter_sbom(chemin)
            assert os.path.isfile(chemin)
        finally:
            shutil.rmtree(tmpdir)
