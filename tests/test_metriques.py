"""
tests/test_metriques.py — Tests unitaires de la Relation d'Incertitude de Heisenberg-Phi
et des formules souveraines du CalculateurRadiance.
"""

import math

from phi_complexity.core import PHI, HBAR_PHI, PHI_INV


class TestConstanteHeisenbergPhi:
    """Vérifie la constante ħ_φ définie dans core.py."""

    def test_hbar_phi_egal_phi_inv(self):
        """ħ_φ doit être exactement 1/φ."""
        assert abs(HBAR_PHI - PHI_INV) < 1e-12

    def test_hbar_phi_valeur_approx(self):
        """ħ_φ ≈ 0.6180."""
        assert abs(HBAR_PHI - 0.6180339887) < 1e-9

    def test_plancher_heisenberg(self):
        """plancher = ħ_φ / 2 ≈ 0.309."""
        plancher = HBAR_PHI / 2
        assert abs(plancher - 0.309016994) < 1e-9


class TestHeisenbergPhi:
    """Tests unitaires pour CalculateurRadiance._heisenberg_phi()."""

    def _build_calculateur(self):
        """Instancie un CalculateurRadiance avec un ResultatAnalyse minimal."""
        from phi_complexity.analyseur import ResultatAnalyse
        from phi_complexity.metriques import CalculateurRadiance

        r = ResultatAnalyse(fichier="test.py")
        return CalculateurRadiance(r)

    def test_zero_variance_zero_entropie(self):
        """Quand variance et entropie sont nulles, le produit est 0 et tension = 0."""
        calc = self._build_calculateur()
        result = calc._heisenberg_phi(0.0, 0.0)
        assert result["delta_complexite"] == 0.0
        assert result["delta_lisibilite"] == 0.0
        assert result["produit_incertitude"] == 0.0
        assert result["tension_quantique"] == 0.0

    def test_plancher_hbar_est_hbar_sur_2(self):
        """Le plancher retourné doit être ħ_φ / 2."""
        calc = self._build_calculateur()
        result = calc._heisenberg_phi(0.0, 0.0)
        assert abs(result["plancher_hbar"] - HBAR_PHI / 2) < 1e-12

    def test_delta_complexite_normalise(self):
        """ΔC = sqrt(variance / (φ² × 100)). Quand variance = φ²×100, ΔC = 1."""
        calc = self._build_calculateur()
        variance_max = PHI**2 * 100
        result = calc._heisenberg_phi(variance_max, 0.0)
        assert abs(result["delta_complexite"] - 1.0) < 1e-10

    def test_delta_lisibilite_normalise(self):
        """ΔL = H_S / log₂(φ⁴). Quand H_S = log₂(φ⁴), ΔL = 1."""
        calc = self._build_calculateur()
        h_max = math.log2(PHI**4)
        result = calc._heisenberg_phi(0.0, h_max)
        assert abs(result["delta_lisibilite"] - 1.0) < 1e-10

    def test_produit_incertitude_couvre_plancher(self):
        """Quand ΔC = ΔL = 1 (cas extrême), la tension doit être >> 1."""
        calc = self._build_calculateur()
        variance_max = PHI**2 * 100
        h_max = math.log2(PHI**4)
        result = calc._heisenberg_phi(variance_max, h_max)
        assert result["tension_quantique"] > 1.0
        # produit = 1.0 × 1.0 = 1.0 ; tension = 1.0 / (ħ_φ/2) ≈ 3.24
        attendu = 1.0 / (HBAR_PHI / 2)
        assert abs(result["tension_quantique"] - attendu) < 1e-9

    def test_etat_coherent_minimal(self):
        """Un produit exactement égal au plancher doit donner tension ≈ 1."""
        calc = self._build_calculateur()
        plancher = HBAR_PHI / 2
        # On choisit ΔC = ΔL = sqrt(plancher)
        sigma_max_sq = PHI**2 * 100
        h_max = math.log2(PHI**4)
        delta = math.sqrt(plancher)
        variance = (delta**2) * sigma_max_sq
        entropie = delta * h_max
        result = calc._heisenberg_phi(variance, entropie)
        assert abs(result["tension_quantique"] - 1.0) < 1e-9

    def test_tension_super_coherent(self):
        """Un code très simple (faible variance, faible entropie) a tension < 1."""
        calc = self._build_calculateur()
        # Très petite variance et très petite entropie
        result = calc._heisenberg_phi(1.0, 0.1)
        assert result["tension_quantique"] < 1.0

    def test_tension_toujours_positive(self):
        """La tension ne peut jamais être négative."""
        calc = self._build_calculateur()
        for variance in [0.0, 10.0, 100.0, 500.0]:
            for entropie in [0.0, 0.5, 2.0, 5.0]:  # phi: ignore[LILITH]
                result = calc._heisenberg_phi(variance, entropie)
                assert result["tension_quantique"] >= 0.0

    def test_delta_lisibilite_clampe_a_1(self):
        """ΔL est borné à 1 même quand H_F dépasse H_max."""
        calc = self._build_calculateur()
        h_max = math.log2(PHI**4)
        # Entropie > H_max : sans borne, delta_l > 1 ; avec borne, doit valoir 1
        result = calc._heisenberg_phi(0.0, h_max * 3.0)
        assert result["delta_lisibilite"] <= 1.0
        assert abs(result["delta_lisibilite"] - 1.0) < 1e-10


class TestHeisenbergDansResultat:
    """Vérifie que heisenberg_tension apparaît dans le résultat de calculer()."""

    def test_heisenberg_tension_present_dans_resultat(self, tmp_path):
        """Le champ heisenberg_tension doit être présent dans le résultat complet."""
        from phi_complexity.analyseur import AnalyseurPhi
        from phi_complexity.metriques import CalculateurRadiance

        code = (
            "def f(x):\n"
            "    if x > 0:\n"
            "        return x\n"
            "    return -x\n"
            "\n"
            "def g(y):\n"
            "    for i in range(y):\n"
            "        print(i)\n"
        )
        fichier = tmp_path / "sample.py"
        fichier.write_text(code)

        analyseur = AnalyseurPhi(str(fichier))
        resultat = analyseur.analyser()
        calc = CalculateurRadiance(resultat)
        sortie = calc.calculer()

        assert "heisenberg_tension" in sortie
        assert isinstance(sortie["heisenberg_tension"], float)
        assert sortie["heisenberg_tension"] >= 0.0

    def test_heisenberg_tension_present_resultat_vide(self):
        """heisenberg_tension doit apparaître même pour un fichier sans fonctions."""
        from phi_complexity.analyseur import ResultatAnalyse
        from phi_complexity.metriques import CalculateurRadiance

        r = ResultatAnalyse(fichier="empty.py")
        calc = CalculateurRadiance(r)
        sortie = calc.calculer()

        assert "heisenberg_tension" in sortie
        assert sortie["heisenberg_tension"] == 0.0


class TestEntropieFibonacci:
    """Tests unitaires pour CalculateurRadiance._entropie_fibonacci()."""

    def _build_calculateur(self):
        from phi_complexity.analyseur import ResultatAnalyse
        from phi_complexity.metriques import CalculateurRadiance

        r = ResultatAnalyse(fichier="test.py")
        return CalculateurRadiance(r)

    def test_entropie_vide_retourne_zero(self):
        """Une liste vide donne H_F = 0."""
        calc = self._build_calculateur()
        assert calc._entropie_fibonacci([]) == 0.0

    def test_entropie_valeurs_nulles_retourne_zero(self):
        """Une liste de zéros donne H_F = 0 (total pondéré nul)."""
        calc = self._build_calculateur()
        assert calc._entropie_fibonacci([0, 0, 0]) == 0.0

    def test_entropie_valeur_unique_retourne_zero(self):
        """Une seule fonction → distribution dégénérée → H_F = 0."""
        calc = self._build_calculateur()
        assert calc._entropie_fibonacci([5]) == 0.0

    def test_entropie_toujours_non_negative(self):
        """H_F ≥ 0 pour toute entrée."""
        calc = self._build_calculateur()
        for valeurs in ([1, 2, 3], [5, 13, 21, 34], [1] * 20):
            assert calc._entropie_fibonacci(valeurs) >= 0.0

    def test_entropie_fibonacci_present_dans_resultat(self):
        """Le champ fibonacci_entropy doit apparaître dans le résultat calculer()."""
        import tempfile
        import textwrap
        from pathlib import Path
        from phi_complexity.analyseur import AnalyseurPhi
        from phi_complexity.metriques import CalculateurRadiance

        code = textwrap.dedent(
            """
            def f(x):
                return x * 2

            def g(a, b):
                return a + b
        """
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(code)
            path = temp_file.name
        try:
            analyseur = AnalyseurPhi(path)
            resultat = analyseur.analyser()
            calc = CalculateurRadiance(resultat)
            sortie = calc.calculer()
            assert "fibonacci_entropy" in sortie
            assert isinstance(sortie["fibonacci_entropy"], float)
            assert sortie["fibonacci_entropy"] >= 0.0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_entropie_fibonacci_present_resultat_vide(self):
        """fibonacci_entropy = 0.0 pour un fichier sans fonctions."""
        from phi_complexity.analyseur import ResultatAnalyse
        from phi_complexity.metriques import CalculateurRadiance

        r = ResultatAnalyse(fichier="empty.py")
        calc = CalculateurRadiance(r)
        sortie = calc.calculer()
        assert "fibonacci_entropy" in sortie
        assert sortie["fibonacci_entropy"] == 0.0

    def test_entropie_fibonacci_extension_dynamique(self):
        """H_F fonctionne pour plus de 14 fonctions (extension au-delà de SEQUENCE_FIBONACCI)."""
        calc = self._build_calculateur()
        valeurs = list(range(1, 20))  # 19 fonctions
        result = calc._entropie_fibonacci(valeurs)
        assert isinstance(result, float)
        assert result >= 0.0


class TestFormulesBrutesEdgeCases:
    """
    Couverture des branches 'liste vide' dans les formules atomiques.
    Ces branches ne sont jamais atteintes via calculer() (qui retourne
    _resultat_vide() avant d'appeler les formules), donc on les appelle
    directement pour garantir la couverture.
    """

    def _build_calculateur(self):
        from phi_complexity.analyseur import ResultatAnalyse
        from phi_complexity.metriques import CalculateurRadiance

        r = ResultatAnalyse(fichier="test.py")
        return CalculateurRadiance(r)

    def test_variance_liste_vide(self):
        """_variance([]) retourne 0.0."""
        calc = self._build_calculateur()
        assert calc._variance([]) == 0.0

    def test_entropie_shannon_liste_vide(self):
        """_entropie_shannon([]) retourne 0.0."""
        calc = self._build_calculateur()
        assert calc._entropie_shannon([]) == 0.0

    def test_entropie_shannon_somme_nulle(self):
        """_entropie_shannon([0, 0]) retourne 0.0 (total == 0)."""
        calc = self._build_calculateur()
        assert calc._entropie_shannon([0, 0]) == 0.0

    def test_zeta_score_liste_vide(self):
        """_zeta_score([]) retourne 0.0."""
        calc = self._build_calculateur()
        assert calc._zeta_score([]) == 0.0

    def test_serialiser_oudjat_none_quand_pas_de_oudjat(self):
        """_serialiser_oudjat() retourne None si self.r.oudjat est None."""
        calc = self._build_calculateur()
        # Par défaut, ResultatAnalyse.oudjat est None
        assert calc._serialiser_oudjat() is None


class TestCoherenceBayes:
    """Tests unitaires pour CalculateurRadiance._coherence_bayes() — EQ-BAY-001..008."""

    def _build_calculateur(self):
        from phi_complexity.analyseur import ResultatAnalyse
        from phi_complexity.metriques import CalculateurRadiance

        r = ResultatAnalyse(fichier="test.py")
        return CalculateurRadiance(r)

    def test_moins_de_deux_valeurs_retourne_zero(self):
        """Moins de 2 fonctions → C_Bayes = 0.0 (pas de paire à mesurer)."""
        calc = self._build_calculateur()
        assert calc._coherence_bayes([]) == 0.0
        assert calc._coherence_bayes([5]) == 0.0

    def test_paire_parfaitement_doree(self):
        """κ[1]/κ[0] = φ → C_Bayes = 0.0 (attracteur exact)."""
        from phi_complexity.core import PHI

        calc = self._build_calculateur()
        # Choisir des valeurs dont le rapport est exactement φ
        a = 100.0
        b = a * PHI
        # _coherence_bayes attend des int, approcher avec des ints proches
        result = calc._coherence_bayes([100, round(b)])
        assert result < 0.1  # très proche de 0

    def test_paires_toutes_zero_ignorees(self):
        """Si κ[i] = 0 pour toutes les paires (dénominateurs nuls), retourne 0.0."""
        calc = self._build_calculateur()
        # [0, 0, 0] : paires (0,0) et (0,0) — les deux ont κ[i]=0, toutes ignorées
        assert calc._coherence_bayes([0, 0, 0]) == 0.0

    def test_valeur_positive_pour_distribution_chaotique(self):
        """Distribution très disparate → C_Bayes > 0."""
        calc = self._build_calculateur()
        result = calc._coherence_bayes([1, 100, 1, 100])
        assert result > 0.0

    def test_symetrie_pas_garantie(self):
        """C_Bayes est asymétrique : [a, b] ≠ [b, a] en général."""
        calc = self._build_calculateur()
        ab = calc._coherence_bayes([2, 5])
        ba = calc._coherence_bayes([5, 2])
        # L'un ou l'autre peut être plus petit ; les deux sont ≥ 0
        assert ab >= 0.0
        assert ba >= 0.0

    def test_coherence_bayes_dans_resultat_calculer(self, tmp_path):
        """calculer() expose 'coherence_bayes' dans le dictionnaire résultat."""
        import textwrap

        from phi_complexity.analyseur import AnalyseurPhi
        from phi_complexity.metriques import CalculateurRadiance

        code = textwrap.dedent(
            """\
            def f(): pass
            def g(): pass
        """
        )
        f = tmp_path / "test.py"
        f.write_text(code)
        r = AnalyseurPhi(str(f)).analyser()
        result = CalculateurRadiance(r).calculer()
        assert "coherence_bayes" in result
        assert isinstance(result["coherence_bayes"], float)
        assert result["coherence_bayes"] >= 0.0

    def test_coherence_bayes_dans_resultat_vide(self):
        """_resultat_vide() expose 'coherence_bayes' = 0.0."""
        from phi_complexity.analyseur import ResultatAnalyse
        from phi_complexity.metriques import CalculateurRadiance

        r = ResultatAnalyse(fichier="vide.py")
        result = CalculateurRadiance(r)._resultat_vide()
        assert "coherence_bayes" in result
        assert result["coherence_bayes"] == 0.0

    def test_deduction_bayes_zero_quand_coherent(self):
        """_deduction_bayes(0.0) = 0.0 — aucune pénalité si parfaitement doré."""
        calc = self._build_calculateur()
        assert calc._deduction_bayes(0.0) == 0.0

    def test_deduction_bayes_plafonnee_a_10(self):
        """_deduction_bayes est plafonnée à 10 points (Loi d'Indulgence)."""
        calc = self._build_calculateur()
        assert calc._deduction_bayes(100.0) == 10.0

    def test_deduction_bayes_scale_phi(self):
        """_deduction_bayes(c) = c × φ pour les petites valeurs."""
        from phi_complexity.core import PHI

        calc = self._build_calculateur()
        c = 1.0
        assert abs(calc._deduction_bayes(c) - c * PHI) < 1e-10
