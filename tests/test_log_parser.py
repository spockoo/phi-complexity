"""
tests/test_log_parser.py — Tests de l'analyseur de logs (Phase 3.1)
"""

from __future__ import annotations


from phi_complexity.log_parser import (
    CATALOGUE_SIGNATURES,
    ClassificationResult,
    PatternSignature,
    classifier_depuis_nom,
    classifier_log,
    enrichir_depuis_logs,
)


class TestClassifierLog:
    def test_checkout_ref_not_found(self) -> None:
        result = classifier_log(
            "Run actions/checkout@v4 A branch or tag with the name 'foo/bar' could not be found"
        )
        assert result.category == "CHECKOUT_REF_NOT_FOUND"

    def test_checkout_ref_generic(self) -> None:
        result = classifier_log(
            "error: checkout failed with exit code 128 after fetch"
        )
        assert result.category == "CHECKOUT_REF"

    def test_infra_runner_unavailable(self) -> None:
        result = classifier_log("no runner available for this job queued timeout")
        assert result.category == "INFRA_RUNNER_UNAVAILABLE"
        assert result.confidence >= 0.70

    def test_toolchain_setup(self) -> None:
        result = classifier_log("setup-python failed: version not available")
        assert result.category == "TOOLCHAIN_SETUP"

    def test_dependency_install(self) -> None:
        result = classifier_log("pip install failed: no matching distribution for foo")
        assert result.category == "DEPENDENCY_INSTALL"

    def test_checkout_ref_not_found_variations(self) -> None:
        logs = [
            "fatal: couldn't find remote ref copilot/missing-branch",
            "fatal: reference is not a tree: 1234567890abcdef",
            "Unable to checkout requested ref in detached HEAD mode",
        ]
        for log in logs:
            assert classifier_log(log).category == "CHECKOUT_REF_NOT_FOUND"

    def test_checkout_repo_missing_maps_to_not_found(self) -> None:
        result = classifier_log(
            "fatal: repository 'https://github.com/org/missing.git' not found during checkout"
        )
        assert result.category == "CHECKOUT_REF_NOT_FOUND"

    def test_permissions(self) -> None:
        result = classifier_log(
            "permission denied: 403 forbidden resource not accessible"
        )
        assert result.category == "PERMISSIONS"

    def test_network_transient(self) -> None:
        result = classifier_log("connection timeout: name resolution failed")
        assert result.category == "NETWORK_TRANSIENT"

    def test_api_contract_drift(self) -> None:
        result = classifier_log("ImportError: cannot import 'foo' smoke test failed")
        assert result.category == "API_CONTRACT_DRIFT"

    def test_type_check(self) -> None:
        result = classifier_log(
            "error: [assignment] found 3 errors in 2 files incompatible type"
        )
        assert result.category == "TYPE_CHECK"

    def test_quality_gate(self) -> None:
        result = classifier_log("ruff error: would reformat black failed")
        assert result.category == "QUALITY_GATE"

    def test_test_regression(self) -> None:
        result = classifier_log("3 failed: assertion error test failed")
        assert result.category == "TEST_REGRESSION"

    def test_timeout_capacity(self) -> None:
        result = classifier_log("timed out after 60 minutes exceeded time limit")
        assert result.category == "TIMEOUT_CAPACITY"

    def test_ci_gate_cascade(self) -> None:
        result = classifier_log("ci resonance sous le seuil below dynamic threshold")
        assert result.category == "CI_GATE_CASCADE"

    def test_unclassified_when_no_match(self) -> None:
        result = classifier_log(
            "some completely random log with no known patterns here"
        )
        assert result.category == "UNCLASSIFIED"
        assert result.confidence == 0.55
        assert result.matched_patterns == []

    def test_case_insensitivity(self) -> None:
        result = classifier_log("PERMISSION DENIED: 403 FORBIDDEN")
        assert result.category == "PERMISSIONS"

    def test_empty_log(self) -> None:
        result = classifier_log("")
        assert result.category == "UNCLASSIFIED"

    def test_confidence_boosted_by_multiple_matches(self) -> None:
        single = classifier_log("ruff error")
        multi = classifier_log("ruff error would reformat reformatted black failed")
        assert multi.confidence >= single.confidence

    def test_custom_catalogue(self) -> None:
        custom = [
            PatternSignature(
                category="CUSTOM_CAT",
                patterns=[r"my_custom_pattern"],
                confidence_base=0.80,
                priority=1,
                hint="Custom hint",
                mutation="Custom mutation",
            )
        ]
        result = classifier_log("my_custom_pattern detected", catalogue=custom)
        assert result.category == "CUSTOM_CAT"

    def test_matched_patterns_populated(self) -> None:
        result = classifier_log("permission denied unauthorized")
        assert result.category == "PERMISSIONS"
        assert len(result.matched_patterns) >= 1

    def test_confidence_capped_at_099(self) -> None:
        log = (
            "ruff error would reformat reformatted black failed "
            "E123 [lint] ruff check failed"
        )
        result = classifier_log(log)
        assert result.confidence <= 0.99


class TestClassifierDepuisNom:
    def test_quality_gate_from_name(self) -> None:
        result = classifier_depuis_nom("quality check", "ruff error lint")
        assert result.category == "QUALITY_GATE"

    def test_unclassified_from_unknown_name(self) -> None:
        result = classifier_depuis_nom("unknown-job", "unknown-step")
        assert result.category == "UNCLASSIFIED"

    def test_type_check_from_name(self) -> None:
        result = classifier_depuis_nom("type check mypy", "error: [assignment]")
        assert result.category == "TYPE_CHECK"

    def test_returns_classification_result(self) -> None:
        result = classifier_depuis_nom("job", "step")
        assert isinstance(result, ClassificationResult)


class TestEnrichirDepuisLogs:
    def test_enriches_unclassified(self) -> None:
        unclassified = ClassificationResult(
            category="UNCLASSIFIED",
            confidence=0.55,
            priority=3,
            hint="Inspection manuelle nécessaire.",
            mutation="Collecter les logs.",
            matched_patterns=[],
        )
        enriched = enrichir_depuis_logs(unclassified, "permission denied 403 forbidden")
        assert enriched.category == "PERMISSIONS"

    def test_does_not_change_classified(self) -> None:
        classified = ClassificationResult(
            category="QUALITY_GATE",
            confidence=0.90,
            priority=2,
            hint="Lint échec.",
            mutation="Fix lint.",
            matched_patterns=["ruff.*error"],
        )
        result = enrichir_depuis_logs(classified, "completely unrelated log text")
        assert result.category == "QUALITY_GATE"
        assert result.confidence == 0.90

    def test_stays_unclassified_if_no_patterns(self) -> None:
        unclassified = ClassificationResult(
            category="UNCLASSIFIED",
            confidence=0.55,
            priority=3,
            hint="",
            mutation="",
            matched_patterns=[],
        )
        result = enrichir_depuis_logs(
            unclassified, "random log without known patterns here"
        )
        assert result.category == "UNCLASSIFIED"


class TestCatalogueSignatures:
    def test_catalogue_has_all_expected_categories(self) -> None:
        categories = {sig.category for sig in CATALOGUE_SIGNATURES}
        expected = {
            "INFRA_RUNNER_UNAVAILABLE",
            "CHECKOUT_REF_NOT_FOUND",
            "CHECKOUT_REF",
            "TOOLCHAIN_SETUP",
            "DEPENDENCY_INSTALL",
            "PERMISSIONS",
            "NETWORK_TRANSIENT",
            "API_CONTRACT_DRIFT",
            "TYPE_CHECK",
            "QUALITY_GATE",
            "TEST_REGRESSION",
            "TIMEOUT_CAPACITY",
            "CI_GATE_CASCADE",
        }
        assert expected.issubset(categories)

    def test_all_signatures_have_patterns(self) -> None:
        for sig in CATALOGUE_SIGNATURES:
            assert len(sig.patterns) > 0, f"{sig.category} has no patterns"

    def test_all_confidence_bases_in_range(self) -> None:
        for sig in CATALOGUE_SIGNATURES:
            assert 0.0 < sig.confidence_base < 1.0
