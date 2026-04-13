from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .core import PHI_INV


@dataclass
class AgentRole:
    """Définit le rôle et l'axiome d'un agent expert du conseil BMAD."""

    id: str
    nom: str
    axiome: str
    priorite: float = 1.0
    description: str = ""


def _agents_par_defaut() -> Dict[str, Dict[str, str]]:
    """Retourne un registre minimal si le registre disque est indisponible."""
    return {
        "AG-01": {
            "nom": "OUDJAT (L'Oeil)",
            "axiome": "Vision centrale.",
            "description": "",
        },
        "AG-02": {
            "nom": "LILITH (La Variance)",
            "axiome": "Entropie sauvage.",
            "description": "",
        },
    }


class RegistreInterneBMAD:
    """Registre interne des agents BMAD, basé sur le registre JSON existant."""

    def __init__(
        self,
        chemin: Optional[str] = None,
        donnees_initiales: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> None:
        self._chemin = (
            Path(chemin)
            if chemin is not None
            else Path(__file__).with_name("agents_registry.json")
        )
        self._agents: Dict[str, AgentRole] = {}
        source = (
            donnees_initiales
            if donnees_initiales is not None
            else self._charger_depuis_fichier()
        )
        self.fusionner(source)

    def _charger_depuis_fichier(self) -> Dict[str, Dict[str, str]]:
        try:
            with self._chemin.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return _agents_par_defaut()

    def fusionner(self, donnees: Dict[str, Dict[str, str]]) -> None:
        for aid, info in donnees.items():
            if not isinstance(info, dict):
                continue
            nom = str(info.get("nom", aid))
            axiome = str(info.get("axiome", ""))
            description = str(info.get("description", ""))
            self.enregistrer(
                AgentRole(
                    id=aid,
                    nom=nom,
                    axiome=axiome,
                    priorite=1.0,
                    description=description,
                )
            )

    def enregistrer(self, agent: AgentRole) -> None:
        self._agents[agent.id] = agent

    def obtenir(self, agent_id: str) -> Optional[AgentRole]:
        return self._agents.get(agent_id)

    def lister(self) -> List[AgentRole]:
        return list(self._agents.values())


class OrchestrateurBMAD:
    """
    Orchestrateur du Cycle BMAD (φ-Meta).
    Simule un conseil de 12 experts et calcule la Résistance Ω (Phase 10).
    """

    def __init__(self, registre: Optional[RegistreInterneBMAD] = None) -> None:
        self._registre = registre if registre is not None else RegistreInterneBMAD()
        self.agents = self._charger_conseil()

    def _charger_conseil(self) -> List[AgentRole]:
        """Charge les agents depuis le registre interne."""
        return self._registre.lister()

    def calculer_omega_resistance(
        self, radiance: float, complexite_totale: int
    ) -> float:
        """
        Calcule la Résistance Supraconductrice Ω (Phase 10).
        Ω = (Complexité / (Radiance + 1)) * PHI_INV.
        """
        if radiance <= 0:
            return 1.0
        base_resistance = complexite_totale / (radiance + 1)
        return float(base_resistance * PHI_INV / 10.0)

    def calculer_resonance_dirichlet(
        self, resultats_bruts: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Applique une Matrice de Dirichlet simplifiée pour pondérer les scores.
        Redistribue la radiance selon les priorités des agents.
        """
        poids_totaux = sum(agent.priorite for agent in self.agents)
        resonance: Dict[str, float] = {}

        for agent in self.agents:
            score_base = resultats_bruts.get(agent.id, 0.5)
            resonance[agent.nom] = (
                score_base * (agent.priorite / poids_totaux) * len(self.agents)
            )

        return resonance

    def generer_briefing_conseil(self, metrics: Dict[str, Any]) -> str:
        """Génère le briefing pour le prompt multi-agents."""
        brief = "LE CONSEIL DES 12 AGENTS BMAD SE RÉUNIT :\n"
        for agent in self.agents:
            desc = f" ({agent.description})" if agent.description else ""
            brief += f"- {agent.nom}{desc} : {agent.axiome}\n"
        return brief
