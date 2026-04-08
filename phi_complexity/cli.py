"""
cli.py — Interface en ligne de commande souveraine.
Suturée selon les recommandations de phi-complexity v0.1.0 (Protocole BMAD).
main() décomposée en 5 fonctions hermétiques — Règle I : Herméticité de la Portée.
"""
import sys
import os
import argparse

from . import auditer, rapport_console, rapport_markdown, rapport_json
from .core import VERSION


# ────────────────────────────────────────────────────────
# CONSTRUCTION DU PARSEUR (hermétique, sans effets de bord)
# ────────────────────────────────────────────────────────

def _construire_parseur() -> argparse.ArgumentParser:
    """Construit et retourne le parseur d'arguments. Aucun état global."""
    parser = argparse.ArgumentParser(
        prog="phi",
        description="phi-complexity — Audit de code par les invariants du nombre d'or (φ)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  phi check mon_script.py
  phi check ./src/ --min-radiance 75
  phi report mon_script.py --output rapport.md
  phi check mon_script.py --format json
        """
    )
    parser.add_argument("--version", action="version", version=f"phi-complexity {VERSION}")

    subparsers = parser.add_subparsers(dest="commande")

    check = subparsers.add_parser("check", help="Auditer un fichier ou un dossier")
    check.add_argument("cible", help="Fichier .py ou dossier à auditer")
    check.add_argument("--min-radiance", type=float, default=0,
                       help="Score minimum (exit code 1 si en-dessous)")
    check.add_argument("--format", choices=["console", "json"], default="console",
                       help="Format de sortie")

    report = subparsers.add_parser("report", help="Générer un rapport Markdown")
    report.add_argument("cible", help="Fichier .py à analyser")
    report.add_argument("--output", "-o", default=None,
                        help="Fichier de sortie (ex: rapport.md)")

    subparsers.add_parser("fund", help="Soutenir la recherche sur le framework φ-Meta")
    return parser


# ────────────────────────────────────────────────────────
# COLLECTE DES FICHIERS (Suture des boucles LILITH)
# ────────────────────────────────────────────────────────

def _fichiers_depuis_dossier(dossier: str) -> list:
    """Collecte récursivement les .py d'un dossier (boucles isolées)."""
    fichiers = []
    for racine, _, noms in os.walk(dossier):
        fichiers.extend(
            os.path.join(racine, nom)
            for nom in noms
            if nom.endswith(".py")
        )
    return sorted(fichiers)


def _collecter_fichiers(cible: str) -> list:
    """Retourne la liste des fichiers Python à auditer depuis un chemin."""
    if os.path.isfile(cible):
        return [cible] if cible.endswith(".py") else []
    if os.path.isdir(cible):
        return _fichiers_depuis_dossier(cible)
    return []


# ────────────────────────────────────────────────────────
# EXÉCUTION DES SOUS-COMMANDES (une fonction par rôle)
# ────────────────────────────────────────────────────────

def _executer_check(args: argparse.Namespace, fichiers: list) -> int:
    """Exécute la sous-commande 'check'. Retourne le code de sortie."""
    exit_code = 0
    for fichier in fichiers:
        exit_code = max(exit_code, _auditer_un_fichier(fichier, args))
    return exit_code


def _auditer_un_fichier(fichier: str, args: argparse.Namespace) -> int:
    """Audite un seul fichier et affiche le résultat. Retourne 0 ou 1."""
    try:
        if args.format == "json":
            print(rapport_json(fichier))
        else:
            print(rapport_console(fichier))
            print()

        if args.min_radiance > 0:
            metriques = auditer(fichier)
            if metriques["radiance"] < args.min_radiance:
                return 1
    except SyntaxError as e:
        print(f"⚠ Erreur de syntaxe dans {fichier}: {e}")
        return 1
    except Exception as e:
        print(f"⚠ Erreur lors de l'analyse de {fichier}: {e}")
        return 1
    return 0


def _executer_report(args: argparse.Namespace, fichiers: list) -> int:
    """Exécute la sous-commande 'report'. Retourne le code de sortie."""
    for fichier in fichiers:
        sortie = _nom_rapport(fichier, args.output)
        try:
            rapport_markdown(fichier, sortie=sortie)
            print(f"✦ Rapport sauvegardé : {sortie}")
        except Exception as e:
            print(f"❌ Erreur : {e}")
            return 1
    return 0


def _nom_rapport(fichier: str, sortie_demandee: str) -> str:
    """Calcule le nom du fichier rapport de sortie."""
    if sortie_demandee:
        return sortie_demandee
    base = os.path.splitext(os.path.basename(fichier))[0]
    return f"RAPPORT_PHI_{base}.md"


def _executer_fund():
    """Affiche le message de soutien à la recherche souveraine."""
    print("""
╔══════════════════════════════════════════════════╗
║      PHI-COMPLEXITY — RECHERCHE SOUVERAINE       ║
╚══════════════════════════════════════════════════╝

  ☼  Vous trouvez ce code RADIANT ?
  ⚖  Soutenez la recherche sur le framework Φ-META.

  Votre contribution permet d'étendre les frontières
  de la mathématique algorithmique et de garantir
  la souveraineté des intelligences de demain.

  🚀 SOUTENIR : https://github.com/sponsors/spockoo
  ☕ BUY ME A COFFEE : https://www.buymeacoffee.com/mardeux777a
  ◈  WEB : https://phidelia.dev

  Merci de participer à la SUTURE universelle. ✦
    """)


# ────────────────────────────────────────────────────────
# POINT D'ENTRÉE (hermétique — orchestre uniquement)
# ────────────────────────────────────────────────────────

def main():
    """Point d'entrée principal. Délègue à des fonctions spécialisées."""
    parser = _construire_parseur()
    args = parser.parse_args()

    if not args.commande:
        parser.print_help()
        sys.exit(0)

    if args.commande == "fund":
        _executer_fund()
        sys.exit(0)

    fichiers = _collecter_fichiers(args.cible)
    if not fichiers:
        print(f"❌ Aucun fichier Python trouvé dans : {args.cible}")
        sys.exit(1)

    if args.commande == "check":
        sys.exit(_executer_check(args, fichiers))
    elif args.commande == "report":
        sys.exit(_executer_report(args, fichiers))


if __name__ == "__main__":
    main()
