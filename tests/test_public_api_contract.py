"""
tests/test_public_api_contract.py — Contrat de stabilité des imports publics.
"""

import phi_complexity
from phi_complexity.analyseur import AnalyseurPhi
from phi_complexity.core import calculer_sync_index
from phi_complexity.metriques import CalculateurRadiance


def test_imports_critiques_symboles_resolus():
    """Les symboles utilisés dans les smoke-tests CI doivent rester importables."""
    assert callable(calculer_sync_index)
    assert AnalyseurPhi.__name__ == "AnalyseurPhi"
    assert CalculateurRadiance.__name__ == "CalculateurRadiance"


def test_package_exporte_les_symbols_critiques():
    """Le package top-level doit exposer les symboles critiques du contrat public."""
    exports = set(phi_complexity.__all__)
    assert {"AnalyseurPhi", "CalculateurRadiance", "suture", "auditer"}.issubset(
        exports
    )


def test_alias_top_level_pointent_sur_impl_reelles():
    """Les alias top-level doivent rester reliés aux implémentations réelles."""
    assert phi_complexity.AnalyseurPhi is AnalyseurPhi
    assert phi_complexity.CalculateurRadiance is CalculateurRadiance
