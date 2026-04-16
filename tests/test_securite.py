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
    signer_attestation,
    verifier_attestation,
    RegistreClesAttestation,
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
    construire_dossier_preuve,
    calculer_score_risque_global,
    evaluer_politique_gouvernance,
    detecter_drift_heuristique,
    construire_dossier_preuve,
    _extraire_cwe,
    classer_finding,
    classer_findings,
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

    def test_journal_chainage_prev_hash(self):
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            journal.enregistrer("A", {"x": 1})
            journal.enregistrer("B", {"x": 2})
            entries = journal.lire_journal()
            assert entries[0]["prev_hash"] == ""
            assert entries[1]["prev_hash"] == entries[0]["hash"]
            assert journal.verifier_integrite() is True
        finally:
            shutil.rmtree(workspace)

    def test_journal_chainage_corrompu(self):
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            for i in range(4):
                journal.enregistrer(f"OP_{i}", {"i": i})
            entries = journal.lire_journal(limite=10)
            entries[2]["prev_hash"] = "tampered"
            with open(journal.journal_path, "w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            assert journal.verifier_integrite() is False
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
                sorties={"stderr": "would reformat example.py\nblack --check ."},
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
        assert "pytest" in actions
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
                    # Keep one LILITH finding here to verify non-zero variance extraction.
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


# ────────────────────────────────────────────────────────
# TESTS — Couverture des branches manquantes
# ────────────────────────────────────────────────────────


class TestValidationCheminBranches:
    """Tests couvrant les branches non-couvertes de valider_chemin_fichier."""

    def test_symlink_vers_non_fichier(self):
        """Symlink vers un répertoire → False (lignes 85-86)."""
        tmpdir = tempfile.mkdtemp()
        try:
            link_path = os.path.join(tmpdir, "link.py")
            os.symlink(tmpdir, link_path)
            assert valider_chemin_fichier(link_path) is False
        finally:
            shutil.rmtree(tmpdir)

    def test_repertoire_pas_un_fichier(self):
        """Un répertoire existant → False (ligne 90)."""
        tmpdir = tempfile.mkdtemp()
        try:
            assert valider_chemin_fichier(tmpdir) is False
        finally:
            shutil.rmtree(tmpdir)


class TestJournalAuditBranches:
    """Tests couvrant les branches non-couvertes du JournalAudit."""

    def test_lire_journal_corrompu(self):
        """Journal JSONL corrompu → retourne [] (lignes 161-162)."""
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            with open(journal.journal_path, "w") as f:
                f.write("{invalid json\n")
            assert journal.lire_journal() == []
        finally:
            shutil.rmtree(workspace)

    def test_verifier_integrite_corrompue(self):
        """Journal avec hash modifié → False (ligne 173)."""
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalAudit(workspace_root=workspace)
            journal.enregistrer("OP", {"v": 1})
            with open(journal.journal_path, "r") as f:
                content = f.read()
            content = content.replace('"v": 1', '"v": 999')
            with open(journal.journal_path, "w") as f:
                f.write(content)
            assert journal.verifier_integrite() is False
        finally:
            shutil.rmtree(workspace)


class TestNormalisationSortieCapturee:
    """Tests couvrant _normaliser_sortie_capturee (lignes 224, 232)."""

    def test_sequence_en_entree(self):
        """Séquence non-string → join (ligne 224)."""
        from phi_complexity.securite import _normaliser_sortie_capturee

        result = _normaliser_sortie_capturee(["err1", "err2"])
        assert "err1" in result
        assert "err2" in result

    def test_valeur_numerique(self):
        """Entier en entrée → str() (ligne 232)."""
        from phi_complexity.securite import _normaliser_sortie_capturee

        result = _normaliser_sortie_capturee(42)
        assert result == "42"


class TestConsensusConflitBranches:
    """Tests couvrant les branches de resoudre_conflit_par_consensus."""

    def test_decision_escalate(self):
        """Consensus bas → ESCALATE (ligne 312)."""
        resolution = resoudre_conflit_par_consensus(
            {"radiance": 10.0, "blocking_findings": 5, "lilith_variance": 100.0},
            {"stderr": "critical failure\n" * 20, "errors": ["fail"] * 10},
        )
        assert resolution["decision"] == "ESCALATE"

    def test_actions_blocking_findings(self):
        """Findings bloquants sans actions → action spécifique (lignes 314-315)."""
        resolution = resoudre_conflit_par_consensus(
            {"radiance": 50.0, "blocking_findings": 3},
            {"stdout": ""},
        )
        assert any("findings bloquants" in a.lower() for a in resolution["actions"])

    def test_actions_erreurs_sans_motifs(self):
        """Erreurs sans motifs reconnus → action de rejeu (lignes 316-319)."""
        resolution = resoudre_conflit_par_consensus(
            {"radiance": 50.0, "blocking_findings": 0},
            {"stdout": "", "stderr": "", "errors": ["unknown error: xyz"]},
        )
        assert any("rejouer" in a.lower() for a in resolution["actions"])

    def test_errors_raw_string(self):
        """errors_raw est un string → converti en liste (lignes 273-274)."""
        resolution = resoudre_conflit_par_consensus(
            {"radiance": 80.0},
            {"errors": "une erreur simple"},
        )
        assert resolution["consensus_score"] >= 0

    def test_errors_raw_vide(self):
        """errors_raw vide (falsy) → liste vide (lignes 275-276)."""
        resolution = resoudre_conflit_par_consensus(
            {"radiance": 80.0},
            {"errors": ""},
        )
        assert resolution["consensus_score"] >= 0

    def test_action_dedup(self):
        """Actions dédupliquées si même motif apparaît 2× (ligne 244)."""
        resolution = resoudre_conflit_par_consensus(
            {"radiance": 80.0},
            {"stdout": "black --check . black --check ."},
        )
        black_actions = [a for a in resolution["actions"] if "black" in a.lower()]
        assert len(black_actions) <= 1


class TestJournalConflitsBranches:
    """Tests couvrant les branches de JournalConflits."""

    def test_lire_journal_inexistant(self):
        """Journal inexistant → [] (ligne 373)."""
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalConflits(workspace_root=workspace)
            assert journal.lire_journal() == []
        finally:
            shutil.rmtree(workspace)

    def test_lire_journal_corrompu(self):
        """Journal corrompu → [] (lignes 378-379)."""
        workspace = tempfile.mkdtemp()
        try:
            journal = JournalConflits(workspace_root=workspace)
            with open(journal.journal_path, "w") as f:
                f.write("not json at all\n")
            assert journal.lire_journal() == []
        finally:
            shutil.rmtree(workspace)


class TestFindingFromPhiBranches:
    """Tests couvrant _finding_from_phi branches."""

    def test_rule_id_non_string_in_journaliser(self):
        """rule_id non-string → str() (ligne 396)."""
        # The rule_id conversion happens in journaliser_conflit_audit
        workspace = tempfile.mkdtemp()
        try:
            audit = {
                "summary": {"security_score": 80.0},
                "findings": [
                    {"rule_id": 134, "severity": "high"},
                ],
                "errors": [],
            }
            evenement = journaliser_conflit_audit(
                audit=audit,
                workspace_root=workspace,
            )
            assert evenement["resolution"]["consensus_score"] >= 0
        finally:
            shutil.rmtree(workspace)


class TestAttestationEtGouvernance:
    def test_signer_et_verifier_attestation(self):
        payload = {"run_id": 1, "score": 92.1}
        attestation = signer_attestation(payload, "secret-test", key_id="k1")
        assert attestation["algorithm"] == "HMAC-SHA256"
        assert verifier_attestation(attestation, "secret-test") is True
        assert verifier_attestation(attestation, "wrong-secret") is False
        assert (
            verifier_attestation(attestation, "secret-test", revoked_key_ids=["k1"])
            is False
        )

    def test_registre_rotation_et_revocation(self):
        workspace = tempfile.mkdtemp()
        try:
            registre = RegistreClesAttestation(workspace_root=workspace)
            nouvelle = registre.rotation("k-rotate")
            assert nouvelle["key_id"] == "k-rotate"
            active = registre.cle_active()
            assert active is not None
            assert active["key_id"] == "k-rotate"
            registre.revoquer("k-rotate")
            assert registre.cle_active() is None
            data = registre.charger()
            assert "k-rotate" in data["revoked"]
        finally:
            shutil.rmtree(workspace)

    def test_score_risque_global_et_policy_profiles(self):
        score = calculer_score_risque_global(
            shield_risk=0.2,
            sentinel_risk=0.1,
            codeql_risk=0.05,
            dependencies_risk=0.0,
        )
        assert 0.0 <= score["global_security_score"] <= 100.0

        policy_oss = evaluer_politique_gouvernance(
            global_security_score=score["global_security_score"],
            blocking_findings=0,
            profile="oss",
        )
        assert policy_oss["status"] == "PASS"

        policy_enterprise = evaluer_politique_gouvernance(
            global_security_score=72.0,
            blocking_findings=0,
            profile="enterprise",
        )
        assert policy_enterprise["status"] == "FAIL"

    def test_detecter_drift_heuristique(self):
        stable = detecter_drift_heuristique([0.4] * 20, window=8, tolerance=0.1)
        assert stable["drift_detected"] is False

        drift = detecter_drift_heuristique(
            [0.7] * 20 + [0.2] * 8,
            window=8,
            tolerance=0.1,
        )
        assert drift["drift_detected"] is True

    def test_detecter_drift_heuristique_baseline_insuffisante(self):
        result = detecter_drift_heuristique([0.8, 0.7, 0.6, 0.5], window=4)
        assert result["reason"] == "insufficient_baseline"
        assert result["drift_detected"] is False

    def test_construire_dossier_preuve_avec_attestation(self):
        tmpdir = tempfile.mkdtemp()
        try:
            artifact_path = os.path.join(tmpdir, "audit.json")
            with open(artifact_path, "w", encoding="utf-8") as f:
                json.dump({"ok": True}, f)

            dossier = construire_dossier_preuve(
                {"audit": artifact_path, "missing": os.path.join(tmpdir, "404.json")},
                metadata={"profile": "enterprise"},
                cle_secrete="secret-test",
                key_id="k-proof",
            )
            assert dossier["proof_bundle"]["artifacts"]["audit"]["exists"] is True
            assert dossier["proof_bundle"]["artifacts"]["missing"]["exists"] is False
            assert "attestation" in dossier
            assert verifier_attestation(dossier["attestation"], "secret-test") is True
        finally:
            shutil.rmtree(tmpdir)


class TestFindingsFromSarifBranches:
    """Tests couvrant les branches de _findings_from_sarif."""

    def test_sarif_runs_non_list(self):
        """runs n'est pas une liste → retourne [] (ligne 651)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump({"runs": "not_a_list"}, f)
            result = _findings_from_sarif(path)
            assert result == []
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_run_non_dict(self):
        """Run n'est pas un dict → skip (ligne 655)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump({"runs": ["not_a_dict"]}, f)
            result = _findings_from_sarif(path)
            assert result == []
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_tool_non_dict(self):
        """tool n'est pas un dict → outil défaut (ligne 658)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump(
                    {
                        "runs": [
                            {
                                "tool": "not_dict",
                                "results": [
                                    {
                                        "ruleId": "TEST",
                                        "level": "warning",
                                        "message": {"text": "test"},
                                    }
                                ],
                            }
                        ]
                    },
                    f,
                )
            result = _findings_from_sarif(path)
            assert len(result) == 1
            assert result[0]["source"] == "sarif"
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_driver_non_dict(self):
        """driver n'est pas un dict → driver défaut (ligne 661)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump(
                    {
                        "runs": [
                            {
                                "tool": {"driver": 42},
                                "results": [
                                    {
                                        "ruleId": "X",
                                        "level": "note",
                                        "message": {"text": "m"},
                                    }
                                ],
                            }
                        ]
                    },
                    f,
                )
            result = _findings_from_sarif(path)
            assert len(result) == 1
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_results_non_list(self):
        """results non-list → skip (ligne 665)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump(
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"name": "T"}},
                                "results": "not_a_list",
                            }
                        ]
                    },
                    f,
                )
            result = _findings_from_sarif(path)
            assert result == []
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_result_non_dict(self):
        """result non-dict → skip (ligne 668)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump(
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"name": "T"}},
                                "results": ["not_a_dict"],
                            }
                        ]
                    },
                    f,
                )
            result = _findings_from_sarif(path)
            assert result == []
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_physical_location_non_dict(self):
        """physicalLocation non-dict → défaut (ligne 677)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump(
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"name": "T"}},
                                "results": [
                                    {
                                        "ruleId": "X",
                                        "level": "warning",
                                        "message": {"text": "m"},
                                        "locations": [{"physicalLocation": "not_dict"}],
                                    }
                                ],
                            }
                        ]
                    },
                    f,
                )
            result = _findings_from_sarif(path)
            assert len(result) == 1
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_artifact_non_dict(self):
        """artifactLocation non-dict → défaut (ligne 680)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump(
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"name": "T"}},
                                "results": [
                                    {
                                        "ruleId": "X",
                                        "level": "warning",
                                        "message": {"text": "m"},
                                        "locations": [
                                            {
                                                "physicalLocation": {
                                                    "artifactLocation": 42,
                                                    "region": {"startLine": 1},
                                                }
                                            }
                                        ],
                                    }
                                ],
                            }
                        ]
                    },
                    f,
                )
            result = _findings_from_sarif(path)
            assert len(result) == 1
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_region_non_dict(self):
        """region non-dict → défaut (ligne 683)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump(
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"name": "T"}},
                                "results": [
                                    {
                                        "ruleId": "X",
                                        "level": "warning",
                                        "message": {"text": "m"},
                                        "locations": [
                                            {
                                                "physicalLocation": {
                                                    "artifactLocation": {
                                                        "uri": "test.c"
                                                    },
                                                    "region": "not_dict",
                                                }
                                            }
                                        ],
                                    }
                                ],
                            }
                        ]
                    },
                    f,
                )
            result = _findings_from_sarif(path)
            assert len(result) == 1
        finally:
            shutil.rmtree(tmpdir)

    def test_sarif_message_non_dict(self):
        """message non-dict → str(msg) (ligne 691)."""
        from phi_complexity.securite import _findings_from_sarif

        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "bad.sarif")
            with open(path, "w") as f:
                json.dump(
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"name": "T"}},
                                "results": [
                                    {
                                        "ruleId": "X",
                                        "level": "note",
                                        "message": "plain string message",
                                    }
                                ],
                            }
                        ]
                    },
                    f,
                )
            result = _findings_from_sarif(path)
            assert len(result) == 1
            assert "plain string" in result[0]["message"]
        finally:
            shutil.rmtree(tmpdir)


class TestScoreSecuriteBranches:
    """Tests couvrant _score_securite (ligne 755)."""

    def test_finding_hors_production_ignore(self):
        """Finding hors surface production → ignoré (ligne 755)."""
        from phi_complexity.securite import _score_securite

        findings = [
            {
                "surface": "demo",
                "severity": "critical",
                "blocking": True,
                "security_relevant": True,
            },
        ]
        score = _score_securite(findings)
        assert score == 100.0  # Le finding demo est ignoré


class TestConstruireAuditBranches:
    """Tests couvrant construire_audit_securite branches."""

    def test_fichier_avec_erreur_analyse(self):
        """Fichier qui cause une exception → capturé dans errors (lignes 789-790)."""
        audit = construire_audit_securite(["/non/existent/file.py"])
        assert len(audit["errors"]) >= 1

    def test_sarif_inexistant(self):
        """SARIF inexistant → erreur capturée (lignes 795-796)."""
        audit = construire_audit_securite([], sarif_path="/non/existent.sarif")
        assert len(audit["errors"]) >= 1


class TestVerifierPolitiqueBranches:
    """Tests couvrant verifier_politique_securite branches."""

    def test_summary_non_dict(self):
        """summary non-dict → False (ligne 848)."""
        assert verifier_politique_securite({"summary": "not_a_dict"}, 70.0) is False

class TestPhiClassification:
    def test_classer_finding_cwe(self):
        finding = {
            "source": "phi-complexity",
            "rule_id": "CWE-79",
            "severity": "high",
            "surface": "production",
        }
        classification = classer_finding(finding)
        assert classification["family"] == "security"
        assert classification["category"] == "injection"
        assert classification["priority"] == "P0"
        assert classification["cwe"] == "CWE-79"

    def test_classer_finding_quality(self):
        finding = {
            "source": "phi-complexity",
            "rule_id": "CYCLOMATIQUE",
            "severity": "medium",
            "surface": "production",
            "security_relevant": False,
        }
        classification = classer_finding(finding)
        assert classification["family"] == "quality"
        assert classification["category"] == "complexity"
        assert classification["priority"] == "P4"

    def test_extraire_cwe(self):
        assert _extraire_cwe("CWE-79") == "79"
        assert _extraire_cwe("CWE-134") == "134"
        assert _extraire_cwe("cwe_89") == "89"
        assert _extraire_cwe("CWE-00123") == "00123"
        assert _extraire_cwe("NO-CWE") is None

    def test_classer_findings_registry_reuse(self):
        findings = [
            {
                "source": "phi-complexity",
                "rule_id": "CWE-79",
                "severity": "critical",
                "surface": "production",
            }
        ]
        registry = {"phi-complexity:CWE-79": {"decision": "quality", "basis": "memo"}}
        classer_findings(findings, registry)
        classification = findings[0]["classification"]
        assert classification["family"] == "quality"
        assert classification["priority"] == "P4"
        assert classification["learning"]["reused"] is True
