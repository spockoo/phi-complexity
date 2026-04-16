import os
import tempfile
import shutil
import json

from phi_complexity.securite import (
    valider_chemin_fichier,
    JournalAudit,
    JournalConflits,
    resoudre_conflit_par_consensus,
    journaliser_conflit_audit,
    _score_securite,
    construire_audit_securite,
    verifier_politique_securite,
    _normaliser_sortie_capturee,
)


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
        result = _normaliser_sortie_capturee(["err1", "err2"])
        assert "err1" in result
        assert "err2" in result

    def test_valeur_numerique(self):
        """Entier en entrée → str() (ligne 232)."""
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
        from phi_complexity.securite import (
            signer_attestation,
            verifier_attestation,
            RegistreClesAttestation,
        )
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
        from phi_complexity.securite import RegistreClesAttestation
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
        from phi_complexity.securite import calculer_score_risque_global, evaluer_politique_gouvernance
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
        from phi_complexity.securite import detecter_drift_heuristique
        stable = detecter_drift_heuristique([0.4] * 20, window=8, tolerance=0.1)
        assert stable["drift_detected"] is False

        drift = detecter_drift_heuristique(
            [0.7] * 20 + [0.2] * 8,
            window=8,
            tolerance=0.1,
        )
        assert drift["drift_detected"] is True

    def test_detecter_drift_heuristique_baseline_insuffisante(self):
        from phi_complexity.securite import detecter_drift_heuristique
        result = detecter_drift_heuristique([0.8, 0.7, 0.6, 0.5], window=4)
        assert result["reason"] == "insufficient_baseline"
        assert result["drift_detected"] is False

    def test_construire_dossier_preuve_avec_attestation(self):
        from phi_complexity.securite import (
            signer_attestation,
            verifier_attestation,
            construire_dossier_preuve,
        )
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
        audit = construire_audit_securite(["/non/existent/file.py"])
        assert len(audit["errors"]) >= 1

    def test_sarif_inexistant(self):
        audit = construire_audit_securite([], sarif_path="/non/existent.sarif")
        assert len(audit["errors"]) >= 1


class TestVerifierPolitiqueBranches:
    """Tests couvrant verifier_politique_securite branches."""

    def test_summary_non_dict(self):
        assert verifier_politique_securite({"summary": "not_a_dict"}, 70.0) is False
