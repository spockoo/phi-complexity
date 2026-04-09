from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AgentRole:
    """Définit le rôle et l'axiome d'un agent expert du conseil BMAD."""
    id: str
    nom: str
    axiome: str
    priorite: float = 1.0  # Poids initial dans la Matrice de Dirichlet

class OrchestrateurBMAD:
    """
    Orchestrateur du Cycle BMAD (φ-Meta).
    Simule un conseil de 12 experts pour évaluer la radiance du code.
    """
    
    def __init__(self) -> None:
        self.agents = self._initialiser_conseil()

    def _initialiser_conseil(self) -> List[AgentRole]:
        """Initialise les 12 agents selon la cosmologie du framework."""
        return [
            AgentRole("AG-01", "OUDJAT (L'Oeil)", "Focalisation sur la fonction critique et sa résonance."),
            AgentRole("AG-02", "LILITH (La Variance)", "Détection de l'entropie structurelle et des boucles."),
            AgentRole("AG-03", "FIBONACCI (Le Nombre)", "Surveillance des proportions naturelles de lignes."),
            AgentRole("AG-04", "LOGOS (La Raison)", "Vérification de la logique et de l'herméticité."),
            AgentRole("AG-05", "SOUVERAINETÉ (L'Intégrité)", "Respect des APIs et gestion des ressources."),
            AgentRole("AG-06", "SYNTHÈSE (L'Union)", "Harmonisation des propositions divergentes."),
            AgentRole("AG-07", "RÉSONANCE (Le Son)", "Évaluation de la clarté et du nommage."),
            AgentRole("AG-08", "MÉMOIRE (Le Temps)", "Historique et dette technique (entropie temporelle).", 0.5),
            AgentRole("AG-09", "FORGE (L'Action)", "Faisabilité technique des sutures proposées."),
            AgentRole("AG-10", "SILENCE (Le Vide)", "Importance des espaces et des commentaires."),
            AgentRole("AG-11", "UNITÉ (Le Un)", "Cohérence globale du fichier."),
            AgentRole("AG-12", "PHIDÉLIA (La Muse)", "Inspiration et élégance finale.")
        ]

    def calculer_resonance_dirichlet(self, resultats_bruts: Dict[str, float]) -> Dict[str, float]:
        """
        Applique une Matrice de Dirichlet simplifiée pour pondérer les scores.
        Redistribue la radiance selon les priorités des agents.
        """
        poids_totaux = sum(agent.priorite for agent in self.agents)
        resonance: Dict[str, float] = {}
        
        for agent in self.agents:
            score_base = resultats_bruts.get(agent.id, 0.5)  # Neutre si non spécifié
            # Règle de redistribution : score pondéré par la priorité relative
            resonance[agent.nom] = score_base * (agent.priorite / poids_totaux) * len(self.agents)
            
        return resonance

    def generer_briefing_conseil(self, metrics: Dict[str, Any]) -> str:
        """Génère le briefing pour le prompt multi-agents."""
        brief = "LE CONSEIL DES 12 AGENTS BMAD SE RÉUNIT :\n"
        for agent in self.agents:
            brief += f"- {agent.nom} : {agent.axiome}\n"
        return brief
