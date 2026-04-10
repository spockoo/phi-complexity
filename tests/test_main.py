"""
tests/test_main.py — Teste le point d'entrée `python -m phi_complexity`.
Couvre phi_complexity/__main__.py (lines 3-5).
"""

import sys
from unittest.mock import patch


def test_main_entrypoint_appelle_cli_main():
    """
    `python -m phi_complexity` doit déléguer à phi_complexity.cli.main().
    On vérifie que main() est appelé exactement une fois.
    """
    # S'assurer que le module est rechargé pour exécuter ses lignes
    sys.modules.pop("phi_complexity.__main__", None)

    with patch("phi_complexity.cli.main") as mock_main:
        import phi_complexity.__main__  # noqa: F401  — exécute main()

        mock_main.assert_called_once()
