"""
tests/test_bmad.py — Tests du registre interne BMAD.
"""

from __future__ import annotations

import os
import json
import tempfile

from phi_complexity.bmad import AgentRole, OrchestrateurBMAD, RegistreInterneBMAD


def _creer_registre_json(contenu: dict[str, dict[str, str]]) -> str:
    fd, chemin = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(contenu, f)
    return chemin


def test_registre_charge_depuis_json_existant() -> None:
    chemin = _creer_registre_json(
        {
            "AG-X": {
                "nom": "TEST",
                "axiome": "Axiome test",
                "description": "Description test",
            }
        }
    )
    try:
        registre = RegistreInterneBMAD(chemin=chemin)
        agent = registre.obtenir("AG-X")
        assert agent is not None
        assert agent.nom == "TEST"
        assert agent.axiome == "Axiome test"
        assert agent.description == "Description test"
    finally:
        os.unlink(chemin)


def test_registre_fallback_si_fichier_absent() -> None:
    chemin = "/tmp/phi_registry_absent_123456789.json"
    registre = RegistreInterneBMAD(chemin=chemin)
    assert registre.obtenir("AG-01") is not None
    assert registre.obtenir("AG-02") is not None


def test_registre_enregistrer_met_a_jour_agent() -> None:
    registre = RegistreInterneBMAD(donnees_initiales={})
    registre.enregistrer(AgentRole("AG-77", "Premier", "Axiome 1"))
    registre.enregistrer(AgentRole("AG-77", "Second", "Axiome 2", description="D2"))

    agent = registre.obtenir("AG-77")
    assert agent is not None
    assert agent.nom == "Second"
    assert agent.axiome == "Axiome 2"
    assert agent.description == "D2"


def test_orchestrateur_utilise_registre_interne_injecte() -> None:
    registre = RegistreInterneBMAD(
        donnees_initiales={
            "AG-Z": {"nom": "Agent Z", "axiome": "Axiome Z", "description": ""}
        }
    )
    orchestrateur = OrchestrateurBMAD(registre=registre)
    assert len(orchestrateur.agents) == 1
    assert orchestrateur.agents[0].id == "AG-Z"
