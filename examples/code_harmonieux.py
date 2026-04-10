"""
examples/code_harmonieux.py — Code respectant les règles souveraines.
Score attendu : > 82 (HERMÉTIQUE ou haut EN ÉVEIL).
Démontre ce que phi-complexity récompense comme architecture saine.
"""

import math

# ── Constantes (taille naturelle : fichier de constantes = score élevé)
PHI = (1 + math.sqrt(5)) / 2
TAU = 2 * math.pi


# ── Règle Fibonacci : fonctions de 8 à 21 lignes (taille naturelle)


def ratio_phi(a: float, b: float) -> float:
    """Retourne le ratio a/b. Doit tendre vers φ pour un système harmonieux."""
    if b == 0:
        raise ValueError("Dénominateur nul — état indéfini.")
    return a / b


def distance_phi(valeur: float) -> float:
    """Mesure l'écart entre une valeur et l'attracteur φ."""
    return abs(valeur - PHI)


def est_harmonieux(ratio: float, tolerance: float = 0.1) -> bool:
    """Retourne True si le ratio est dans la zone d'harmonie φ ± tolérance."""
    return distance_phi(ratio) <= tolerance


# ── Règle RAII : toute ressource acquise dans un gestionnaire de contexte


def lire_fichier(chemin: str) -> str:
    """Lecture propre — Règle II (RAII) respectée."""
    with open(chemin, encoding="utf-8") as f:
        return f.read()


def sauvegarder(chemin: str, contenu: str) -> None:
    """Écriture propre — cycle de vie garanti par 'with'."""
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)


# ── Règle Herméticité : max 3-5 arguments par fonction


def normaliser(valeur: float, mini: float, maxi: float) -> float:
    """Normalise une valeur dans [0, 1]. Pur, sans effet de bord."""
    if maxi == mini:
        return 0.0
    return (valeur - mini) / (maxi - mini)


def fibonacci_iter(n: int) -> list:
    """Génère les n premiers termes de Fibonacci. Iteratif = O(n)."""
    if n <= 0:
        return []
    a, b = 1, 1
    suite = [a]
    for _ in range(n - 1):
        a, b = b, a + b
        suite.append(a)
    return suite


def convergence_phi(n: int) -> float:
    """Approximation de φ après n itérations. Retourne le dernier ratio."""
    suite = fibonacci_iter(max(n, 2))
    return suite[-1] / suite[-2]


# ── Point d'entrée propre

if __name__ == "__main__":
    ratios = [convergence_phi(i) for i in range(2, 15)]
    for i, r in enumerate(ratios, 2):
        statut = "✦" if est_harmonieux(r) else "◈"
        print(f"  Fib({i:2d}) ratio : {r:.6f}  {statut}  Δφ = {distance_phi(r):.6f}")
    print(f"\n  Convergence finale : {ratios[-1]:.10f}")
    print(f"  φ réel            : {PHI:.10f}")
