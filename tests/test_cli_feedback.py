import os
import sys
import pytest
import tempfile
import argparse
from unittest.mock import MagicMock
from phi_complexity.cli import (
    _verifier_et_collecter,
    _executer_scan,
    _executer_graph,
    main,
)


def test_verifier_et_collecter_non_python():
    """Vérifie que la collecte d'un fichier non supporté échoue proprement."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"test")
        path = f.name
    try:
        with pytest.raises(SystemExit) as cm:
            _verifier_et_collecter(path, type_scan="audit")
        assert cm.value.code == 1
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_verifier_et_collecter_non_existent():
    """Vérifie qu'un chemin inexistant déclenche une sortie d'erreur."""
    with pytest.raises(SystemExit) as cm:
        _verifier_et_collecter("/invalid/phi/path/999", type_scan="audit")
    assert cm.value.code == 1


def test_verifier_et_collecter_dossier_vide():
    """Vérifie qu'un dossier vide (ou sans fichiers supportés) échoue."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(SystemExit) as cm:
            _verifier_et_collecter(tmpdir, type_scan="audit")
        assert cm.value.code == 1


def test_executer_scan_not_writable():
    """Vérifie que l'impossibilité d'écrire le scan échoue proprement."""
    # Sur Windows, il est difficile de simuler un dossier non-scriptable sans changer les ACL complexes.
    # On teste ici le cas du dossier inexistant pour couvrir la branche os.path.exists.
    args = argparse.Namespace(
        harvest=True, output="/dossier_fantome_phi/test.jsonl", format="console"
    )
    with pytest.raises(SystemExit) as cm:
        _executer_scan(args, ["test.py"])
    assert cm.value.code == 1


def test_executer_graph_error(monkeypatch):
    """Vérifie la robustesse de l'affichage du graphe en cas d'erreur de vault."""
    from phi_complexity.vault import PhiVault

    def mock_gen(*args):
        raise Exception("Resonance Error")

    monkeypatch.setattr(PhiVault, "generer_graph_ascii", mock_gen)

    args = MagicMock(spec=argparse.Namespace)
    args.format = "ascii"
    assert _executer_graph(args) == 1


def test_main_unknown_command(monkeypatch):
    """Vérifie que Phidélia rejette les commandes inconnues (exit 2 via argparse)."""
    # Simulation d'arguments via monkeypatch de sys.argv
    monkeypatch.setattr(sys, "argv", ["phi", "hologramme_inconnu"])
    with pytest.raises(SystemExit) as cm:
        main()
    assert cm.value.code == 2


def test_executer_vault_error_accumulation(monkeypatch):
    """Vérifie que vault continue après une erreur sur un fichier."""
    import phi_complexity.cli as cli

    def mock_auditer(f):
        if "fail" in f:
            raise Exception("Audit Failed")
        return {"radiance": 80.0}

    monkeypatch.setattr(cli, "auditer", mock_auditer)
    # On mock aussi vault.enregistrer_audit pour éviter d'écrire sur le disque
    from phi_complexity.vault import PhiVault

    monkeypatch.setattr(PhiVault, "enregistrer_audit", lambda *a: "note.md")
    monkeypatch.setattr(PhiVault, "detecter_regressions", lambda *a: [])

    args = argparse.Namespace()
    fichiers = ["pass.py", "fail.py"]
    # Doit retourner 1 car au moins une erreur a eu lieu, mais traiter les deux
    assert cli._executer_vault(args, fichiers) == 1
