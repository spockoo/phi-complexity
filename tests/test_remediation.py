"""
tests/test_remediation.py — Tests du moteur de mutations déterministes (Phase 1.1)
"""

from __future__ import annotations

import pytest

from phi_complexity.remediation import (
    CATALOGUE_MUTATIONS,
    MutationPlan,
    RegleMutation,
    ResultatMutation,
    appliquer_mutation,
    mutations_pour_rapport,
    planifier_mutation,
)


class TestPlanifierMutation:
    def test_applicable_for_quality_gate_high_confidence(self) -> None:
        plan = planifier_mutation("QUALITY_GATE", 0.95)
        assert plan.applicable is True
        assert plan.categorie == "QUALITY_GATE"
        assert len(plan.regles) > 0

    def test_not_applicable_below_threshold(self) -> None:
        plan = planifier_mutation("QUALITY_GATE", 0.50)
        assert plan.applicable is False
        assert plan.regles == []

    def test_not_applicable_for_unknown_category(self) -> None:
        plan = planifier_mutation("UNKNOWN_CATEGORY", 0.99)
        assert plan.applicable is False

    def test_applicable_for_dependency_install(self) -> None:
        plan = planifier_mutation("DEPENDENCY_INSTALL", 0.90)
        assert plan.applicable is True

    def test_applicable_for_test_regression(self) -> None:
        plan = planifier_mutation("TEST_REGRESSION", 0.85)
        assert plan.applicable is True

    def test_applicable_for_type_check(self) -> None:
        plan = planifier_mutation("TYPE_CHECK", 0.90)
        assert plan.applicable is True

    def test_confidence_stored_in_plan(self) -> None:
        plan = planifier_mutation("QUALITY_GATE", 0.92)
        assert plan.diagnostic_confidence == pytest.approx(0.92)

    def test_custom_catalogue(self) -> None:
        custom = [
            RegleMutation(
                categorie="CUSTOM",
                confidence_threshold=0.70,
                description="Custom rule",
                commandes=["echo custom"],
                idempotence_check=None,
                rollback_commandes=[],
                necessite_tests=False,
            )
        ]
        plan = planifier_mutation("CUSTOM", 0.80, catalogue=custom)
        assert plan.applicable is True
        assert plan.regles[0].categorie == "CUSTOM"

    def test_exactly_at_threshold_is_applicable(self) -> None:
        plan = planifier_mutation("TEST_REGRESSION", 0.85)
        assert plan.applicable is True

    def test_just_below_threshold_is_not_applicable(self) -> None:
        plan = planifier_mutation("TEST_REGRESSION", 0.84)
        assert plan.applicable is False


class TestAppliquerMutation:
    def test_dry_run_does_not_execute(self) -> None:
        plan = planifier_mutation("QUALITY_GATE", 0.95)
        result = appliquer_mutation(plan, dry_run=True)
        assert result.succes is True
        assert result.rollback_effectue is False
        assert len(result.commandes_executees) > 0
        assert result.sortie == ""

    def test_non_applicable_plan_returns_failure(self) -> None:
        plan = planifier_mutation("QUALITY_GATE", 0.10)
        result = appliquer_mutation(plan, dry_run=True)
        assert result.succes is False
        assert result.erreur is not None
        assert "Aucune règle applicable" in (result.erreur or "")

    def test_dry_run_records_commands(self) -> None:
        plan = planifier_mutation("DEPENDENCY_INSTALL", 0.90)
        result = appliquer_mutation(plan, dry_run=True)
        assert "pip install -e . --upgrade" in result.commandes_executees

    def test_dry_run_quality_gate_commands(self) -> None:
        plan = planifier_mutation("QUALITY_GATE", 0.95)
        result = appliquer_mutation(plan, dry_run=True)
        assert "ruff check --fix ." in result.commandes_executees
        assert "black ." in result.commandes_executees

    def test_result_has_correct_categorie(self) -> None:
        plan = planifier_mutation("TYPE_CHECK", 0.92)
        result = appliquer_mutation(plan, dry_run=True)
        assert result.categorie == "TYPE_CHECK"

    def test_non_applicable_has_empty_commands_executed(self) -> None:
        plan = planifier_mutation("UNKNOWN", 0.99)
        result = appliquer_mutation(plan, dry_run=True)
        assert result.commandes_executees == []

    def test_real_execution_echo(self) -> None:
        custom_plan = MutationPlan(
            categorie="TEST_EXEC",
            regles=[
                RegleMutation(
                    categorie="TEST_EXEC",
                    confidence_threshold=0.50,
                    description="Echo test",
                    commandes=["echo hello"],
                    idempotence_check=None,
                    rollback_commandes=[],
                    necessite_tests=False,
                )
            ],
            diagnostic_confidence=0.99,
            applicable=True,
        )
        result = appliquer_mutation(custom_plan, dry_run=False)
        assert result.succes is True
        assert "hello" in result.sortie

    def test_rollback_on_failure(self) -> None:
        custom_plan = MutationPlan(
            categorie="TEST_FAIL",
            regles=[
                RegleMutation(
                    categorie="TEST_FAIL",
                    confidence_threshold=0.50,
                    description="Failing command",
                    commandes=["exit 1"],
                    idempotence_check=None,
                    rollback_commandes=["echo rollback"],
                    necessite_tests=False,
                )
            ],
            diagnostic_confidence=0.99,
            applicable=True,
        )
        result = appliquer_mutation(custom_plan, dry_run=False)
        assert result.succes is False
        assert result.rollback_effectue is True


class TestMutationsPourRapport:
    def test_returns_list_of_plans(self) -> None:
        mutations = [
            {"category": "QUALITY_GATE", "confidence": 0.95},
            {"category": "TEST_REGRESSION", "confidence": 0.85},
        ]
        plans = mutations_pour_rapport(mutations)
        assert len(plans) == 2
        assert all(isinstance(p, MutationPlan) for p in plans)

    def test_applicable_plans_for_known_categories(self) -> None:
        mutations = [{"category": "QUALITY_GATE", "confidence": 0.95}]
        plans = mutations_pour_rapport(mutations)
        assert plans[0].applicable is True

    def test_not_applicable_for_low_confidence(self) -> None:
        mutations = [{"category": "QUALITY_GATE", "confidence": 0.10}]
        plans = mutations_pour_rapport(mutations)
        assert plans[0].applicable is False

    def test_empty_list(self) -> None:
        plans = mutations_pour_rapport([])
        assert plans == []

    def test_missing_fields_use_defaults(self) -> None:
        plans = mutations_pour_rapport([{}])
        assert plans[0].categorie == "UNCLASSIFIED"
        assert plans[0].applicable is False


class TestCatalogueMutations:
    def test_has_all_expected_categories(self) -> None:
        categories = {r.categorie for r in CATALOGUE_MUTATIONS}
        expected = {"QUALITY_GATE", "DEPENDENCY_INSTALL", "TEST_REGRESSION", "TYPE_CHECK"}
        assert expected == categories

    def test_all_rules_have_commands(self) -> None:
        for rule in CATALOGUE_MUTATIONS:
            assert len(rule.commandes) > 0, f"{rule.categorie} has no commands"

    def test_confidence_thresholds_in_range(self) -> None:
        for rule in CATALOGUE_MUTATIONS:
            assert 0.0 < rule.confidence_threshold < 1.0

    def test_quality_gate_has_rollback(self) -> None:
        quality_rules = [r for r in CATALOGUE_MUTATIONS if r.categorie == "QUALITY_GATE"]
        assert any(len(r.rollback_commandes) > 0 for r in quality_rules)
