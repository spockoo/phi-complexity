from __future__ import annotations
import os
import json
from dataclasses import dataclass
from typing import List, Dict, Any
from .core import PHI_INV

@dataclass
class AgentRole:
    """Définit le rôle et l'axiome d'un agent expert du conseil BMAD."""
    id: str
    nom: str
    axiome: str
    priorite: float = 1.0
    description: str = ""

class OrchestrateurBMAD:
    """
    Orchestrateur du Cycle BMAD (φ-Meta).
    Simule un conseil de 12 experts et calcule la Résistance Ω (Phase 10).
    """
    
    def __init__(self) -> None:
        self.agents = self._charger_conseil()

    def _charger_conseil(self) -> List[AgentRole]:
        """Charge les agents depuis le registre JSON ou utilise les défauts."""
        chemin = os.path.join(os.path.dirname(__file__), "agents_registry.json")
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [
                    AgentRole(aid, info["nom"], info["axiome"], 1.0, info.get("description", ""))
                    for aid, info in data.items()
                ]
        except Exception:
            # Fallback cosmologique si le registre est indisponible
            return [
                AgentRole("AG-01", "OUDJAT (L'Oeil)", "Vision centrale."),
                AgentRole("AG-02", "LILITH (La Variance)", "Entropie sauvage.")
            ]

    def calculer_omega_resistance(self, radiance: float, complexite_totale: int) -> float:
        """
        Calcule la Résistance Supraconductrice Ω (Phase 10).
        Ω = (Complexité / (Radiance + 1)) * PHI_INV.
        """
        if radiance <= 0:
            return 1.0
        base_resistance = complexite_totale / (radiance + 1)
        return float(base_resistance * PHI_INV / 10.0)

    def calculer_resonance_dirichlet(self, resultats_bruts: Dict[str, float]) -> Dict[str, float]:
        """
        Applique une Matrice de Dirichlet simplifiée pour pondérer les scores.
        Redistribue la radiance selon les priorités des agents.
        """
        poids_totaux = sum(agent.priorite for agent in self.agents)
        resonance: Dict[str, float] = {}
        
        for agent in self.agents:
            score_base = resultats_bruts.get(agent.id, 0.5)
            resonance[agent.nom] = score_base * (agent.priorite / poids_totaux) * len(self.agents)
            
        return resonance

    def generer_briefing_conseil(self, metrics: Dict[str, Any]) -> str:
        """Génère le briefing pour le prompt multi-agents."""
        brief = "LE CONSEIL DES 12 AGENTS BMAD SE RÉUNIT :\n"
        for agent in self.agents:
            desc = f" ({agent.description})" if agent.description else ""
            brief += f"- {agent.nom}{desc} : {agent.axiome}\n"
        return brief
