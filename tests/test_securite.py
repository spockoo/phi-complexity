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
    JournalConflits,
    generer_sbom,
    exporter_sbom,
    construire_audit_securite,
    exporter_audit_securite,
    journaliser_conflit_audit,
    resoudre_conflit_par_consensus,
    verifier_politique_securite,
    _est_finding_securite,
)

CODE_C_VULNERABLE = """\
#include <stdio.h>
void f(char *x) {
    printf(x);
}
"""

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


class TestJournalConflits:
    def test_enregistrer_conflit_genere_un_consensus(self):
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalConflits(workspace_root=workspace)
            evenement = journal.enregistrer_conflit(
                "ci-gate",
                {
                    "radiance": 91.0,
                    "lilith_variance": 12.0,
                    "blocking_findings": 0,
                },
                sorties={
                    "stderr": "would reformat tests/test_backends.py\nblack --check ."
                },
            )
            assert evenement["source"] == "ci-gate"
            assert evenement["resolution"]["decision"] in {
                "AUTO_RESOLVE",
                "REVIEW",
            }
            assert evenement["resolution"]["actions"]
            entries = journal.lire_journal()
            assert len(entries) == 1
        finally:
            shutil.rmtree(workspace)

    def test_consensus_detecte_actions_black_pytest(self):
        resolution = resoudre_conflit_par_consensus(
            {
                "radiance": 82.0,
                "lilith_variance": 0.0,
                "blocking_findings": 0,
            },
            {
                "stdout": "pytest --cov=phi_complexity --cov-fail-under=89",
                "stderr": "would reformat tests/test_backends.py",
                "errors": ["black --check . failed"],
            },
        )
        actions = " ".join(resolution["actions"]).lower()
        assert "black" in actions
        assert "pytest" in actions or "couverture" in actions
        assert resolution["consensus_score"] >= 45.0

    def test_journaliser_conflit_audit_extrait_les_invariants(self):
        workspace = tempfile.mkdtemp()
        try:
            audit = {
                "summary": {
                    "security_score": 64.0,
                    "findings_total": 2,
                    "blocking_findings": 1,
                    "out_of_scope_findings": 0,
                    "status": "FAIL",
                },
                "findings": [
                    {"rule_id": "LILITH", "severity": "high"},
                    {"rule_id": "CWE-134", "severity": "critical"},
                ],
                "errors": ["pytest failed"],
            }
            evenement = journaliser_conflit_audit(
                audit=audit,
                sorties={"stderr": "pytest failed\ncoverage below threshold"},
                workspace_root=workspace,
            )
            assert evenement["source"] == "phi-shield"
            assert evenement["invariants"]["blocking_findings"] == 1
            assert evenement["invariants"]["lilith_variance"] > 0.0
            assert evenement["resolution"]["decision"] in {"REVIEW", "ESCALATE"}
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


class TestAuditSecurite:
    def test_audit_securite_phi_detecte_cwe134(self):
        tmpdir = tempfile.mkdtemp()
        try:
            chemin = os.path.join(tmpdir, "vuln.c")
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(CODE_C_VULNERABLE)
            audit = construire_audit_securite([chemin])
            assert audit["summary"]["findings_total"] == 1
            assert audit["summary"]["blocking_findings"] == 1
            assert audit["findings"][0]["rule_id"] == "CWE-134"
            assert audit["findings"][0]["severity"] == "critical"
        finally:
            shutil.rmtree(tmpdir)

    def test_audit_securite_exclut_demo_par_defaut(self):
        tmpdir = tempfile.mkdtemp()
        try:
            examples_dir = os.path.join(tmpdir, "examples")
            os.makedirs(examples_dir)
            chemin = os.path.join(examples_dir, "demo.c")
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(CODE_C_VULNERABLE)
            audit = construire_audit_securite([chemin], include_demo=False)
            assert audit["summary"]["findings_total"] == 0
        finally:
            shutil.rmtree(tmpdir)

    def test_audit_securite_sarif_normalise(self):
        tmpdir = tempfile.mkdtemp()
        try:
            sarif_path = os.path.join(tmpdir, "scan.sarif")
            payload = {
                "runs": [
                    {
                        "tool": {"driver": {"name": "Flawfinder"}},
                        "results": [
                            {
                                "ruleId": "CWE-134",
                                "level": "error",
                                "message": {"text": "Potential format string problem"},
                                "locations": [
                                    {
                                        "physicalLocation": {
                                            "artifactLocation": {"uri": "src/main.c"},
                                            "region": {"startLine": 12},
                                        }
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
            with open(sarif_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            audit = construire_audit_securite([], sarif_path=sarif_path)
            assert audit["summary"]["findings_total"] == 1
            finding = audit["findings"][0]
            assert finding["source"] == "Flawfinder"
            assert finding["severity"] == "high"
        finally:
            shutil.rmtree(tmpdir)

    def test_exporter_audit_securite_et_politique(self):
        tmpdir = tempfile.mkdtemp()
        try:
            audit = {
                "summary": {
                    "security_score": 84.0,
                    "findings_total": 0,
                    "blocking_findings": 0,
                }
            }
            chemin = os.path.join(tmpdir, "security", "audit.json")
            exporter_audit_securite(audit, chemin)
            assert os.path.isfile(chemin)
            assert verifier_politique_securite(audit, 70.0) is True
            assert verifier_politique_securite(audit, 90.0) is False
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_c_scanner_python_file_out_of_scope(self):
        """Flawfinder (C scanner) findings on Python files must be out-of-scope
        and non-blocking so they do not tank the security score."""
        tmpdir = tempfile.mkdtemp()
        try:
            sarif_path = os.path.join(tmpdir, "flawfinder.sarif")
            payload = {
                "runs": [
                    {
                        "tool": {"driver": {"name": "Flawfinder"}},
                        "results": [
                            # Python file — should be out_of_scope, not blocking
                            {
                                "ruleId": "FF1009",
                                "level": "error",
                                "message": {"text": "open(): Check when opening files"},
                                "locations": [
                                    {
                                        "physicalLocation": {
                                            "artifactLocation": {
                                                "uri": "phi_complexity/cli.py"
                                            },
                                            "region": {"startLine": 10},
                                        }
                                    }
                                ],
                            },
                            # C file — should remain blocking (in scope for Flawfinder)
                            {
                                "ruleId": "CWE-134",
                                "level": "error",
                                "message": {"text": "Format string problem"},
                                "locations": [
                                    {
                                        "physicalLocation": {
                                            "artifactLocation": {"uri": "src/engine.c"},
                                            "region": {"startLine": 5},
                                        }
                                    }
                                ],
                            },
                        ],
                    }
                ]
            }
            with open(sarif_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            audit = construire_audit_securite([], sarif_path=sarif_path)
            findings = audit["findings"]
            py_finding = next(f for f in findings if f["path"].endswith(".py"))
            c_finding = next(f for f in findings if f["path"].endswith(".c"))

            # Python file: out-of-scope, not blocking, does not reduce score
            assert py_finding["out_of_scope"] is True
            assert py_finding["blocking"] is False

            # C file: in-scope, blocking (production surface, high severity)
            assert c_finding.get("out_of_scope") is False
            assert c_finding["blocking"] is True

            # Score should only be penalised for the C finding
            s = audit["summary"]
            assert s["out_of_scope_findings"] == 1
            assert s["blocking_findings"] == 1
            assert s["security_score"] < 100.0
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_c_scanner_python_only_scan_passes_gate(self):
        """When Flawfinder scans only Python files (e.g. ./phi_complexity),
        all findings are out-of-scope → score=100, status=PASS."""
        tmpdir = tempfile.mkdtemp()
        try:
            sarif_path = os.path.join(tmpdir, "flawfinder.sarif")
            results = [
                {
                    "ruleId": "FF1009",
                    "level": "error",
                    "message": {"text": "open() check"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": f"phi_complexity/mod{i}.py"
                                },
                                "region": {"startLine": i * 10},
                            }
                        }
                    ],
                }
                for i in range(12)
            ]
            payload = {
                "runs": [
                    {"tool": {"driver": {"name": "Flawfinder"}}, "results": results}
                ]
            }
            with open(sarif_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)

            audit = construire_audit_securite([], sarif_path=sarif_path)
            s = audit["summary"]
            assert s["blocking_findings"] == 0
            assert s["out_of_scope_findings"] == 12
            assert s["security_score"] == 100.0
            assert s["status"] == "PASS"
        finally:
            shutil.rmtree(tmpdir)

    def test_phi_quality_annotations_excluded_from_security_gate(self):
        """Les annotations qualité phi (ex: CYCLOMATIQUE) ne doivent pas
        être traitées comme vulnérabilités bloquantes."""
        tmpdir = tempfile.mkdtemp()
        try:
            file_path = os.path.join(tmpdir, "complexe.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(
                    """def f(a, b, c):
    if a:
        if b:
            if c:
                return 1
    if not a and b:
        return 2
    if a and not b:
        return 3
    if a and b and c:
        return 4
    if (a and b) or (b and c) or (a and c):
        return 5
    return 0
"""
                )

            audit = construire_audit_securite([file_path])
            summary = audit["summary"]
            non_security = [
                f for f in audit["findings"] if not f.get("security_relevant", True)
            ]

            assert non_security
            assert summary["blocking_findings"] == 0
            assert summary["security_score"] == 100.0
            assert summary["status"] == "PASS"
        finally:
            shutil.rmtree(tmpdir)

    def test_est_finding_securite_prioritize_security_relevant(self):
        assert _est_finding_securite({"security_relevant": True}) is True
        assert _est_finding_securite({"security_relevant": False}) is False
        assert (
            _est_finding_securite(
                {
                    "security_relevant": False,
                    "source": "phi-complexity",
                    "rule_id": "CWE-134",
                }
            )
            is False
        )

    def test_est_finding_securite_fallback_par_source(self):
        assert (
            _est_finding_securite({"source": "phi-complexity", "rule_id": "CWE-134"})
            is True
        )
        assert (
            _est_finding_securite(
                {"source": "phi-complexity", "rule_id": "CYCLOMATIQUE"}
            )
            is False
        )
        assert (
            _est_finding_securite({"source": "Flawfinder", "rule_id": "FF1009"}) is True
        )
