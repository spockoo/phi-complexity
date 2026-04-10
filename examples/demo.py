"""
examples/demo.py — Démonstration complète de phi-complexity.
Lance ce script pour voir phi-complexity en action sur deux exemples contrastés.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from phi_complexity import rapport_console, rapport_markdown
from phi_complexity.core import PHI, TAXE_SUTURE


def code_chaotique():
    """Exemple de code avec haute entropie — score bas attendu."""
    x = 0
    data = [1, 2, 3, 4, 5]
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] > data[j]:
                for k in range(10):
                    if k % 2 == 0:
                        x += data[i] * data[j] * k
                        result.append(x)
    f = open("temp_result.txt", "w")
    f.write(str(result))
    # Pas de f.close() — traînée d'entropie (SUTURE WARNING)
    return result


def code_harmonieux(valeurs):
    """Exemple de code harmonieux — score élevé attendu."""
    return [v * PHI for v in valeurs if v > 0]


def analyser_stabilite(valeurs):
    """Mesure la stabilité selon la Taxe de Suture."""
    ecart = max(valeurs) - min(valeurs)
    return ecart / TAXE_SUTURE


if __name__ == "__main__":
    print("=" * 60)
    print("  PHI-COMPLEXITY — DÉMONSTRATION")
    print("=" * 60)
    print()

    # Audit sur ce fichier lui-même
    fichier = __file__
    print(rapport_console(fichier))

    print()
    print("  Génération du rapport Markdown...")
    rapport_markdown(fichier, sortie="DEMO_RAPPORT_PHI.md")
    print("  ✦ Rapport sauvegardé : DEMO_RAPPORT_PHI.md")
