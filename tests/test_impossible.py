"""
tests/test_impossible.py — Tests de l'Algèbre de l'Impossible (Phase 13).
"""

import math

from phi_complexity.impossible import ImpossibleOperator
from phi_complexity.core import PHI


class TestImpossibleOperator:

    def setup_method(self):
        self.op = ImpossibleOperator()

    # ──────────────── calculate() ────────────────

    def test_calculate_zero(self):
        """I(0) = 0 (point fixe au zéro)."""
        assert self.op.calculate(0.0) == 0.0

    def test_calculate_positif(self):
        """Pour s > 0, I(s) = -s * exp(-φ * s) < 0."""
        val = self.op.calculate(1.0)
        assert val < 0.0
        expected = -1.0 * math.exp(-PHI * 1.0)
        assert abs(val - expected) < 1e-10

    def test_calculate_negatif(self):
        """Pour s < 0, I(s) > 0."""
        val = self.op.calculate(-1.0)
        assert val > 0.0

    def test_calculate_phi_inv(self):
        """I(1/φ) ≈ -0.2270 (résidu de souveraineté)."""
        val = self.op.calculate(1.0 / PHI)
        assert abs(val - (-(1.0 / PHI) * math.exp(-1.0))) < 1e-10

    def test_calculate_grand_s(self):
        """Pour s très grand, I(s) → 0 (amortissement exponentiel)."""
        val = self.op.calculate(100.0)
        assert abs(val) < 1e-6

    # ──────────────── stability() ────────────────

    def test_stability_s_positif(self):
        """La stabilité est non-négative pour s > 0."""
        s = self.op.stability(0.5)
        assert s >= 0.0

    def test_stability_s_zero(self):
        """stability(0) utilise epsilon pour éviter la division par zéro."""
        val = self.op.stability(0.0)
        assert val == 0.0  # I(0) = 0 → stabilité = 0

    def test_stability_bornee(self):
        """La stabilité dans [0, 1/φ] converge vers une valeur finie."""
        for s in [0.1, 0.2, 0.3, 0.618]:
            s_val = self.op.stability(s)
            assert s_val >= 0.0

    # ──────────────── integrate_harmonic() ────────────────

    def test_integrate_harmonic_t_zero(self):
        """Intégrale avec t=0 retourne 0."""
        result = self.op.integrate_harmonic(0.0, lambda s: 1.0)
        assert result == 0.0

    def test_integrate_harmonic_steps_zero(self):
        """Intégrale avec steps=0 retourne 0."""
        result = self.op.integrate_harmonic(1.0, lambda s: 1.0, steps=0)
        assert result == 0.0

    def test_integrate_harmonic_resonance_constante(self):
        """Avec R(s) = 1, l'intégrale est finie et non-nulle pour t > 0."""
        result = self.op.integrate_harmonic(1.0, lambda s: 1.0, k=1.0, h=1.0, steps=100)
        assert isinstance(result, float)
        assert result != 0.0

    def test_integrate_harmonic_k_nul(self):
        """k=0 → intégrale nulle."""
        result = self.op.integrate_harmonic(1.0, lambda s: 1.0, k=0.0)
        assert result == 0.0

    def test_integrate_harmonic_h_nul(self):
        """h=0 → intégrale nulle."""
        result = self.op.integrate_harmonic(1.0, lambda s: 1.0, h=0.0)
        assert result == 0.0

    # ──────────────── exploration_vide() ────────────────

    def test_exploration_vide_appelle_calculate(self):
        """exploration_vide(iota) == calculate(iota)."""
        for iota in [0.0, 0.3, 0.618, 1.0]:
            assert self.op.exploration_vide(iota) == self.op.calculate(iota)

    def test_exploration_vide_iota_zero(self):
        assert self.op.exploration_vide(0.0) == 0.0

    # ──────────────── propriété φ ────────────────

    def test_phi_correct(self):
        assert abs(self.op.phi - PHI) < 1e-10
