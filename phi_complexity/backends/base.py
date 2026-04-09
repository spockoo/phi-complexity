from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..analyseur import ResultatAnalyse

class AnalyseurBackend(ABC):
    """
    Interface abstraite pour tous les backends d'analyse de radiance.
    Définit le contrat minimal pour qu'un langage soit intégré au framework Φ-Meta.
    """

    def __init__(self, fichier: str):
        self.fichier = fichier

    @abstractmethod
    def analyser(self) -> ResultatAnalyse:
        """Exécute l'analyse et retourne un ResultatAnalyse standardisé."""
        pass
