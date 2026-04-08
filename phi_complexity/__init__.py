"""
__init__.py — API publique de phi-complexity.
Expose les fonctions de haut niveau pour une utilisation simple.
"""
from .core import PHI, TAXE_SUTURE, ETA_GOLDEN, VERSION, AUTEUR, FRAMEWORK
from .analyseur import AnalyseurPhi
from .metriques import CalculateurRadiance
from .rapport import GenerateurRapport


def auditer(fichier: str) -> dict:
    """
    Lance un audit complet sur un fichier Python.
    Retourne un dictionnaire de métriques.

    Usage:
        from phi_complexity import auditer
        result = auditer("mon_script.py")
        print(result["radiance"])  # → 82.4
    """
    analyseur = AnalyseurPhi(fichier)
    resultat = analyseur.analyser()
    calculateur = CalculateurRadiance(resultat)
    return calculateur.calculer()


def rapport_console(fichier: str) -> str:
    """Retourne le rapport ASCII formaté pour le terminal."""
    metriques = auditer(fichier)
    return GenerateurRapport(metriques).console()


def rapport_markdown(fichier: str, sortie: str = None) -> str:
    """
    Génère un rapport Markdown.
    Si `sortie` est spécifié, sauvegarde dans ce fichier.
    Retourne le contenu Markdown.
    """
    metriques = auditer(fichier)
    gen = GenerateurRapport(metriques)
    if sortie:
        gen.sauvegarder_markdown(sortie)
    return gen.markdown()


def rapport_json(fichier: str) -> str:
    """Retourne le rapport JSON pour CI/CD."""
    metriques = auditer(fichier)
    return GenerateurRapport(metriques).json()


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
]
