from __future__ import annotations
from typing import Dict, Any, Optional
from .core import PHI, TAXE_SUTURE, ETA_GOLDEN, VERSION, AUTEUR
from .analyseur import AnalyseurPhi
from .metriques import CalculateurRadiance
from .rapport import GenerateurRapport
from .suture import SutureAgent
from .oracle import OracleRadiance
from .harvest import HarvestEngine
from .vault import PhiVault
from .canvas import PhiCanvas
from .search import PhiSearch


def auditer(fichier: str) -> Dict[str, Any]:
    """
    Lance un audit complet sur un fichier Python.
    Retourne un dictionnaire de métriques.

    Usage:
        from phi_complexity import auditer
        result = auditer("mon_script.py")
        print(result["radiance"])  # → 82.4
    """
    analyseur: AnalyseurPhi = AnalyseurPhi(fichier)
    resultat = analyseur.analyser()
    calculateur: CalculateurRadiance = CalculateurRadiance(resultat)
    return calculateur.calculer()


def rapport_console(fichier: str) -> str:
    """Retourne le rapport ASCII formaté pour le terminal."""
    metriques = auditer(fichier)
    return GenerateurRapport(metriques).console()


def rapport_markdown(fichier: str, sortie: Optional[str] = None) -> str:
    """
    Génère un rapport Markdown.
    Si `sortie` est spécifié, sauvegarde dans ce fichier.
    Retourne le contenu Markdown.
    """
    metriques: Dict[str, Any] = auditer(fichier)
    gen: GenerateurRapport = GenerateurRapport(metriques)
    if sortie:
        gen.sauvegarder_markdown(sortie)
    return gen.markdown()


def rapport_json(fichier: str) -> str:
    """Retourne le rapport JSON pour CI/CD."""
    metriques = auditer(fichier)
    return GenerateurRapport(metriques).json()


def suture(fichier: str, api_url: Optional[str] = None) -> str:
    """
    Invoque Phidélia pour proposer une suture du fichier.
    Retourne la suggestion de l'IA (Markdown).
    """
    from .analyseur import AnalyseurPhi
    from .metriques import CalculateurRadiance

    analyseur = AnalyseurPhi(fichier)
    resultat = analyseur.analyser()

    # On injecte les métriques de radiance dans le résultat pour Phidélia
    calculateur = CalculateurRadiance(resultat)
    metriques = calculateur.calculer()
    resultat.radiance = metriques["radiance"]

    agent = SutureAgent(api_url) if api_url else SutureAgent()
    return agent.suturer(resultat)


__version__ = VERSION
__author__ = AUTEUR
__all__ = [
    "auditer",
    "rapport_console",
    "rapport_markdown",
    "rapport_json",
    "PHI",
    "TAXE_SUTURE",
    "ETA_GOLDEN",
    "AnalyseurPhi",
    "CalculateurRadiance",
    "GenerateurRapport",
    "SutureAgent",
    "OracleRadiance",
    "HarvestEngine",
    "PhiVault",
    "PhiCanvas",
    "PhiSearch",
    "suture",
]
