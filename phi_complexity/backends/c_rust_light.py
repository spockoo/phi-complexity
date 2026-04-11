from __future__ import annotations
import re
from typing import List, Optional, Tuple
from ..analyseur import ResultatAnalyse, MetriqueFonction, Annotation
from .base import AnalyseurBackend
from ..core import distance_fibonacci

# ── CWE-134 : Format String Vulnerability ──────────────────────────
#
# Fonctions C de formatage dont le premier argument variadic (le "format")
# ne doit *jamais* provenir d'une variable contrôlable par l'utilisateur.
#
# Réf. : https://cwe.mitre.org/data/definitions/134.html
# ────────────────────────────────────────────────────────────────────

# Mapping: nom_fonction -> indice (0-based) de l'argument "format"
_FORMAT_FUNCTIONS: dict[str, int] = {
    "printf": 0,
    "fprintf": 1,
    "sprintf": 1,
    "snprintf": 2,
    "dprintf": 1,
    "vprintf": 0,
    "vfprintf": 1,
    "vsprintf": 1,
    "vsnprintf": 2,
    "syslog": 1,
    "wprintf": 0,
    "fwprintf": 1,
    "swprintf": 1,
}

# Pattern qui capture un appel à une fonction de formatage avec ses arguments.
# Groupe 1: nom de la fonction, Groupe 2: chaîne d'arguments brute.
_RE_FORMAT_CALL = re.compile(
    r"\b(" + "|".join(re.escape(fn) for fn in _FORMAT_FUNCTIONS) + r")\s*\((.+)\)",
)

# Un littéral chaîne C commence par " (optionnel L/u8/u/U prefix).
_RE_STRING_LITERAL = re.compile(r'^(?:L|u8|u|U)?"')


def _extraire_arguments(args_bruts: str) -> List[str]:
    """Découpe une chaîne d'arguments C en respectant les parenthèses et guillemets."""
    args: List[str] = []
    courant: List[str] = []
    profondeur = 0
    dans_chaine = False
    escape = False

    for car in args_bruts:
        if escape:
            courant.append(car)
            escape = False
            continue
        if car == "\\":
            courant.append(car)
            escape = True
            continue
        if car == '"' and profondeur == 0:
            dans_chaine = not dans_chaine
            courant.append(car)
            continue
        if dans_chaine:
            courant.append(car)
            continue
        if car == "(":
            profondeur += 1
            courant.append(car)
        elif car == ")":
            profondeur -= 1
            courant.append(car)
        elif car == "," and profondeur == 0:
            args.append("".join(courant).strip())
            courant = []
        else:
            courant.append(car)

    reste = "".join(courant).strip()
    if reste:
        args.append(reste)
    return args


def detecter_cwe_134(
    lignes: List[str],
) -> List[Tuple[int, str, str]]:
    """Détecte les appels de fonctions de formatage avec un format non-littéral.

    Retourne une liste de tuples (numéro_ligne_1based, nom_fonction, extrait).
    """
    resultats: List[Tuple[int, str, str]] = []

    for i, ligne in enumerate(lignes):
        ligne_strip = ligne.strip()
        # Ignorer les commentaires simples
        if ligne_strip.startswith("//") or ligne_strip.startswith("/*"):
            continue

        for match in _RE_FORMAT_CALL.finditer(ligne_strip):
            nom_func = match.group(1)
            args_bruts = match.group(2)
            idx_format = _FORMAT_FUNCTIONS[nom_func]

            args = _extraire_arguments(args_bruts)
            if idx_format >= len(args):
                continue

            arg_format = args[idx_format].strip()
            # Si l'argument format n'est PAS un littéral chaîne → CWE-134
            if not _RE_STRING_LITERAL.match(arg_format):
                resultats.append((i + 1, nom_func, ligne_strip))

    return resultats


class CRustLightBackend(AnalyseurBackend):
    """
    Backend souverain pour C, C++ et Rust.
    Analyse "Light" basée sur la profondeur des accolades et les patterns de fonctions.
    Inclut la détection de CWE-134 (Format String Vulnerability).
    Zéro dépendances.
    """

    def analyser(self) -> ResultatAnalyse:
        with open(self.fichier, "r", encoding="utf-8") as handle:
            lignes = handle.readlines()

        resultat = ResultatAnalyse(fichier=self.fichier)
        resultat.nb_lignes_total = len(lignes)

        # Détection simple de fonctions (pattern: type nom(args) {)
        pattern_func = re.compile(r"^\s*(?:[\w<>:]+\s+)+(\w+)\s*\([^)]*\)\s*\{?")

        current_func_name: Optional[str] = None
        current_func_start: int = 0
        current_func_complexity: int = 0
        depth: int = 0

        for i, ligne in enumerate(lignes):
            ligne_strip = ligne.strip()
            if not ligne_strip:
                continue

            # Analyse des accolades
            prev_depth = depth
            depth += ligne_strip.count("{")
            depth -= ligne_strip.count("}")

            # Détection début de fonction
            if prev_depth == 0 and depth > 0:
                match = pattern_func.match(ligne_strip)
                if match:
                    current_func_name = match.group(1)
                    current_func_start = i + 1
                    current_func_complexity = 0

            # Comptage complexité
            if depth > 0:
                current_func_complexity += 1
                if depth > 2:
                    current_func_complexity += (depth - 2) * 2

            # Fin de fonction
            if prev_depth > 0 and depth == 0 and current_func_name:
                nb_lignes = (i + 1) - current_func_start + 1
                metrique = MetriqueFonction(
                    nom=current_func_name,
                    ligne=current_func_start,
                    complexite=current_func_complexity,
                    nb_args=0,
                    nb_lignes=nb_lignes,
                    profondeur_max=0,
                    distance_fib=distance_fibonacci(nb_lignes),
                    phi_ratio=1.0,
                )
                resultat.fonctions.append(metrique)

                if current_func_complexity > 50:
                    resultat.annotations.append(
                        Annotation(
                            ligne=current_func_start,
                            message=(
                                f"LILITH : Fonction '{current_func_name}' trop complexe "
                                f"pour le bas niveau ({current_func_complexity} nœuds)."
                            ),
                            niveau="WARNING",
                            extrait=ligne_strip,
                            categorie="LILITH",
                        )
                    )

                current_func_name = None

        # ── Détection CWE-134 (Format String Vulnerability) ──
        for num_ligne, nom_func, extrait in detecter_cwe_134(lignes):
            resultat.annotations.append(
                Annotation(
                    ligne=num_ligne,
                    message=(
                        f"CWE-134 : Appel à '{nom_func}()' avec un format "
                        f"non-littéral (chaîne contrôlable). "
                        f"Risque d'injection de chaîne de format. "
                        f"Correction : utiliser un format littéral, ex. "
                        f'{nom_func}("%s", variable).'
                    ),
                    niveau="CRITICAL",
                    extrait=extrait,
                    categorie="CWE-134",
                )
            )

        if resultat.fonctions:
            resultat.oudjat = max(resultat.fonctions, key=lambda f: f.complexite)
            moyenne = sum(f.complexite for f in resultat.fonctions) / len(
                resultat.fonctions
            )
            if moyenne > 0:
                for f in resultat.fonctions:
                    f.phi_ratio = f.complexite / moyenne

        return resultat
