from __future__ import annotations
from typing import TYPE_CHECKING
from .base import AnalyseurBackend

if TYPE_CHECKING:
    from ..analyseur import ResultatAnalyse

class PythonBackend(AnalyseurBackend):
    """
    Backend d'analyse pour le langage Python.
    Utilise le module AST natif pour une précision souveraine.
    """

    def analyser(self) -> ResultatAnalyse:
        """Exécute l'analyse via AnalyseurPythonInternal."""
        from ..analyseur import AnalyseurPythonInternal
        analyseur = AnalyseurPythonInternal(self.fichier)
        return analyseur.analyser()
