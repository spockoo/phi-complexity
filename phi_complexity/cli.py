from __future__ import annotations
import sys
import os
import json
import argparse
import traceback
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from . import auditer, rapport_console, rapport_markdown, rapport_json
from .core import VERSION

if TYPE_CHECKING:
    from .fingerprint import PhiFingerprint

# Extensions de fichiers supportées par le framework φ-Meta
_EXTENSIONS_SUPPORTEES: Tuple[str, ...] = (
    ".py",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".rs",
    ".asm",
    ".s",
)

# Extensions binaires supportées par le backend ELF/PE/Mach-O
_EXTENSIONS_BINAIRES: Tuple[str, ...] = (
    ".elf",
    ".so",
    ".o",
    ".exe",
    ".dll",
    ".sys",
    ".dylib",
    ".bin",
)

# ────────────────────────────────────────────────────────
# CONSTRUCTION DU PARSEUR (hermétique, sans effets de bord)
# ────────────────────────────────────────────────────────


def _construire_parseur() -> argparse.ArgumentParser:  # phi: ignore[FIBONACCI]
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
        """,
    )
    parser.add_argument(
        "--version", action="version", version=f"phi-complexity {VERSION}"
    )

    subparsers = parser.add_subparsers(dest="commande")

    check = subparsers.add_parser("check", help="Auditer un fichier ou un dossier")
    check.add_argument("cible", help="Fichier .py ou dossier à auditer")
    check.add_argument(
        "--min-radiance",
        type=float,
        default=0,
        help="Score minimum (exit code 1 si en-dessous)",
    )
    check.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Format de sortie",
    )
    check.add_argument(
        "--bmad", action="store_true", help="Afficher la résonance des 12 agents BMAD"
    )

    report = subparsers.add_parser("report", help="Générer un rapport Markdown")
    report.add_argument("cible", help="Fichier .py à analyser")
    report.add_argument(
        "--output", "-o", default=None, help="Fichier de sortie (ex: rapport.md)"
    )

    subparsers.add_parser("fund", help="Soutenir la recherche sur le framework φ-Meta")

    suture_parser = subparsers.add_parser(
        "suture", help="Invoque Phidélia pour une suture intelligente."
    )
    suture_parser.add_argument("path", help="Fichier à suturer")
    suture_parser.add_argument("--url", help="URL de l'API LLM locale")

    subparsers.add_parser("memory", help="Consulter les annales akashiques (Phase 11)")

    seal_parser = subparsers.add_parser(
        "seal", help="Apposer un sceau gnostique permanent (Phase 12)."
    )
    seal_parser.add_argument("cible", help="Fichier à sceller")

    heal_parser = subparsers.add_parser(
        "heal", help="Lancer une guérison autonome (Auto-Suture Phase 12)."
    )
    heal_parser.add_argument("cible", help="Fichier à guérir")
    heal_parser.add_argument(
        "--force",
        action="store_true",
        help="Forcer la guérison même si la radiance est élevée",
    )
    heal_parser.add_argument("--url", help="URL de l'API LLM locale")

    oracle_parser = subparsers.add_parser(
        "oracle", help="Valider une release selon l'Oracle de Radiance (Phase 14)."
    )
    oracle_parser.add_argument("cible", help="Fichier ou dossier à auditer")
    oracle_parser.add_argument(
        "--min-radiance",
        type=float,
        default=70.0,
        help="Seuil de radiance requis pour autoriser la release (défaut: 70)",
    )
    oracle_parser.add_argument(
        "--nb-tests",
        type=int,
        default=0,
        help="Nombre de tests passés (intégré dans la version Phi)",
    )

    harvest_parser = subparsers.add_parser(
        "harvest", help="Collecter des vecteurs AST anonymisés pour l'IA (Phase 14)."
    )
    harvest_parser.add_argument("cible", help="Fichier ou dossier à collecter")
    harvest_parser.add_argument(
        "--output",
        "-o",
        default=".phi/harvest.jsonl",
        help="Fichier JSONL de sortie (défaut: .phi/harvest.jsonl)",
    )

    # Phase 15 — Metadata (gouvernance harvest/vault)
    metadata_parser = subparsers.add_parser(
        "metadata", help="Synthèse et purge souveraine des métadonnées."
    )
    metadata_parser.set_defaults(_metadata_parser=metadata_parser)
    metadata_sub = metadata_parser.add_subparsers(dest="metadata_action")

    metadata_summary = metadata_sub.add_parser(
        "summary", help="Afficher une synthèse des métadonnées (harvest + vault)."
    )
    metadata_summary.add_argument(
        "--harvest",
        default=".phi/harvest.jsonl",
        help="Chemin du corpus harvest (défaut: .phi/harvest.jsonl)",
    )
    metadata_summary.add_argument(
        "--vault-index",
        default=".phi/vault/index.json",
        help="Index du vault (défaut: .phi/vault/index.json)",
    )
    metadata_summary.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Format de sortie (texte par défaut).",
    )

    metadata_purge = metadata_sub.add_parser(
        "purge", help="Sanitiser un corpus harvest pour partage (strip / features)."
    )
    metadata_purge.add_argument(
        "--harvest",
        default=".phi/harvest.jsonl",
        help="Chemin du corpus harvest (défaut: .phi/harvest.jsonl)",
    )
    metadata_purge.add_argument(
        "--output",
        "-o",
        default=None,
        help="Fichier de sortie. Par défaut : <harvest>.sanitized.jsonl",
    )
    metadata_purge.add_argument(
        "--in-place",
        action="store_true",
        help="Écrase le fichier harvest (attention : irréversible).",
    )
    metadata_purge.add_argument(
        "--strip",
        action="append",
        default=[],
        help="Clés supplémentaires à supprimer (option répétable).",
    )
    metadata_purge.add_argument(
        "--strip-sensitive",
        action="store_true",
        help="Supprime les clés sensibles (timestamp, fingerprint).",
    )
    metadata_purge.add_argument(
        "--strip-labels",
        action="store_true",
        help="Supprime les labels/nb_critiques (partage sans annotations).",
    )
    metadata_purge.add_argument(
        "--keep-features",
        action="store_true",
        help="Conserve uniquement les métriques structurelles (vecteur φ).",
    )

    spiral_parser = subparsers.add_parser(
        "spiral", help="Afficher la Spirale Dorée de radiance (Phase 14)."
    )
    spiral_parser.add_argument("cible", help="Fichier à visualiser")

    # Phase 16 — Vault (mémoire persistante type Obsidian)
    vault_parser = subparsers.add_parser(
        "vault", help="Auditer et enregistrer dans le Phi Vault (Phase 16)."
    )
    vault_parser.add_argument("cible", help="Fichier ou dossier à auditer et archiver")

    # Phase 16 — Graph (visualisation du graphe de radiance)
    graph_parser = subparsers.add_parser(
        "graph",
        help="Afficher le graphe de radiance du vault (Phase 16).",
    )
    graph_parser.add_argument(
        "--format",
        choices=["ascii", "dot"],
        default="ascii",
        help="Format de sortie (ascii ou dot)",
    )

    # Phase 17 — Canvas (export .canvas compatible Obsidian)
    canvas_parser = subparsers.add_parser(
        "canvas",
        help="Exporter un Canvas Obsidian (.canvas) du code audité (Phase 17).",
    )
    canvas_parser.add_argument("cible", help="Fichier ou dossier à auditer")
    canvas_parser.add_argument(
        "--output",
        "-o",
        default=".phi/architecture.canvas",
        help="Fichier .canvas de sortie (défaut: .phi/architecture.canvas)",
    )

    # Phase 18 — Search (recherche sémantique dans le vault)
    search_parser = subparsers.add_parser(
        "search", help="Recherche sémantique dans le Phi Vault (Phase 18)."
    )
    search_parser.add_argument(
        "--statut",
        help="Chercher par statut (HERMÉTIQUE, EN ÉVEIL, DORMANT)",
    )
    search_parser.add_argument(
        "--min-radiance",
        type=float,
        default=0.0,
        help="Radiance minimale",
    )
    search_parser.add_argument(
        "--max-radiance",
        type=float,
        default=100.0,
        help="Radiance maximale",
    )
    search_parser.add_argument(
        "--categorie",
        help="Chercher par catégorie d'annotation (LILITH, SUTURE, FIBONACCI, SOUVERAINETE)",
    )
    search_parser.add_argument(
        "--etat-zero",
        help="Chercher par état morphogénétique (PRE_ZERO, ZERO_CAUSAL, POST_RENAISSANCE)",
    )

    # Phase 20 — SBOM (Software Bill of Materials)
    sbom_parser = subparsers.add_parser(
        "sbom", help="Générer le Software Bill of Materials (Phase 20)."
    )
    sbom_parser.add_argument(
        "--output",
        "-o",
        default=".phi/sbom.json",
        help="Fichier SBOM de sortie (défaut: .phi/sbom.json)",
    )

    shield_parser = subparsers.add_parser(
        "shield", help="Audit sécurité unifié + gate CI (Phase 22)."
    )
    shield_parser.add_argument("cible", help="Fichier ou dossier à auditer")
    shield_parser.add_argument(
        "--sarif",
        default=None,
        help="Fichier SARIF externe à fusionner (ex: flawfinder_results.sarif)",
    )
    shield_parser.add_argument(
        "--output",
        "-o",
        default=".phi/security_audit.json",
        help="Fichier JSON de sortie (défaut: .phi/security_audit.json)",
    )
    shield_parser.add_argument(
        "--min-security-score",
        type=float,
        default=70.0,
        help="Seuil minimal de sécurité pour passer le gate (défaut: 70)",
    )
    shield_parser.add_argument(
        "--include-demo",
        action="store_true",
        help="Inclure les exemples pédagogiques dans le score/gate",
    )

    # Phase 24 — Scan antiviral (phi-fingerprint + sentinel)
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scanner un binaire ou fichier source (analyse antivirale φ-Sentinel Phase 24).",
    )
    scan_parser.add_argument("cible", help="Fichier binaire ou dossier à scanner")
    scan_parser.add_argument(
        "--format",
        choices=["console", "json"],
        default="console",
        help="Format de sortie (console ou json)",
    )
    scan_parser.add_argument(
        "--harvest",
        action="store_true",
        help="Collecter le fingerprint dans le corpus harvest",
    )
    scan_parser.add_argument(
        "--output",
        "-o",
        default=".phi/harvest.jsonl",
        help="Fichier JSONL pour le harvest (défaut: .phi/harvest.jsonl)",
    )

    subparsers.add_parser("ui", help="Démarrer le Moteur Web IDE Phidélia local.")

    return parser


# ────────────────────────────────────────────────────────
# COLLECTE DES FICHIERS (Suture des boucles LILITH)
# ────────────────────────────────────────────────────────


def _fichiers_depuis_dossier(dossier: str) -> List[str]:
    """Collecte récursivement les fichiers supportés d'un dossier."""
    fichiers: List[str] = []
    for racine, _, noms in os.walk(dossier):
        fichiers.extend(
            os.path.join(racine, nom)
            for nom in noms
            if nom.lower().endswith(_EXTENSIONS_SUPPORTEES)
        )
    return sorted(fichiers)


def _collecter_fichiers(cible: str) -> List[str]:
    """Retourne la liste des fichiers à auditer depuis un chemin."""
    if os.path.isfile(cible):
        return [cible] if cible.lower().endswith(_EXTENSIONS_SUPPORTEES) else []
    if os.path.isdir(cible):
        return _fichiers_depuis_dossier(cible)
    return []


def _fichiers_depuis_dossier_scan(dossier: str) -> List[str]:
    """Collecte récursivement les fichiers scannables d'un dossier (source + binaire)."""
    toutes = _EXTENSIONS_SUPPORTEES + _EXTENSIONS_BINAIRES
    fichiers: List[str] = []
    for racine, _, noms in os.walk(dossier):
        fichiers.extend(
            os.path.join(racine, nom) for nom in noms if nom.lower().endswith(toutes)
        )
    return sorted(fichiers)


def _collecter_fichiers_scan(cible: str) -> List[str]:
    """Retourne la liste des fichiers à scanner (source + binaire)."""
    if os.path.isfile(cible):
        # Accept any file for scanning (even without known extension)
        return [cible]
    if os.path.isdir(cible):
        return _fichiers_depuis_dossier_scan(cible)
    return []


# ────────────────────────────────────────────────────────
# EXÉCUTION DES SOUS-COMMANDES (une fonction par rôle)
# ────────────────────────────────────────────────────────


def _executer_check(args: argparse.Namespace, fichiers: List[str]) -> int:
    """Exécute la sous-commande 'check'. Retourne le code de sortie."""
    if args.format == "json":
        return _executer_check_json(args, fichiers)
    exit_code = 0
    for fichier in fichiers:
        exit_code = max(exit_code, _auditer_un_fichier(fichier, args))
    return exit_code


def _executer_check_json(args: argparse.Namespace, fichiers: List[str]) -> int:
    """Exécute 'check --format json' : collecte tous les résultats et émet un tableau JSON unique."""
    import json as _json

    resultats = []
    exit_code = 0
    for fichier in fichiers:
        try:
            data = _json.loads(rapport_json(fichier))
            resultats.append(data)
            if args.min_radiance > 0 and data.get("radiance", 0) < args.min_radiance:
                exit_code = 1
        except SyntaxError as e:
            resultats.append({"fichier": fichier, "erreur": str(e)})
            exit_code = 1
        except Exception as e:
            resultats.append({"fichier": fichier, "erreur": str(e)})
            exit_code = 1
    sortie = resultats[0] if len(resultats) == 1 else resultats
    print(_json.dumps(sortie, ensure_ascii=False))
    return exit_code


def _auditer_un_fichier(  # phi: ignore[CYCLOMATIQUE]
    fichier: str, args: argparse.Namespace
) -> int:
    """Audite un seul fichier et affiche le résultat (format console). Retourne 0 ou 1."""
    try:
        print(rapport_console(fichier))
        if getattr(args, "bmad", False):
            _afficher_bmad(fichier)

        # Phase 12 : Vérification du Sceau Gnostique
        try:
            from .gnose import MoteurGnostique
            from .analyseur import AnalyseurPhi

            gnose = MoteurGnostique()
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            if gnose.verifier(resultat):
                print("  🛡  SCEAU GNOSTIQUE : Vérifié (Résonance Intacte) ✦")
            else:
                # On vérifie si un sceau existe pour ce fichier
                import json

                if os.path.exists(gnose.gnose_path):
                    with open(gnose.gnose_path, "r") as f:
                        if resultat.fichier in json.load(f):
                            print(
                                "  ⚠  SCEAU BRISÉ : Divergence spectrale détectée ! ░"
                            )
        except Exception:
            pass

        # Phase 11 : Enregistrement Akashique automatique
        try:
            from .akasha import RegistreAkashique

            akasha = RegistreAkashique()
            akasha.enregistrer(auditer(fichier))
        except Exception:
            pass
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


def _afficher_bmad(fichier: str) -> None:
    """Affiche la répartition de la radiance entre les agents BMAD."""
    from .bmad import OrchestrateurBMAD
    from . import auditer as phi_auditer

    metrics = phi_auditer(fichier)
    orchestrateur = OrchestrateurBMAD()

    # Simulation de répartition basée sur les métriques réelles
    scores_bruts = {
        "AG-01": metrics["radiance"] / 100,
        "AG-02": (
            1.0 - (metrics["lilith_variance"] / 1000)
            if metrics["lilith_variance"] < 1000
            else 0.1
        ),
        "AG-03": 0.9 if metrics["oudjat"] else 0.5,
    }
    resonance = orchestrateur.calculer_resonance_dirichlet(scores_bruts)

    print("  ◈ RÉSONANCE DES AGENTS BMAD :")
    for nom, score in list(resonance.items())[:6]:
        barre = "█" * int(score * 10)
        print(f"    - {nom:<20} : {barre:<10} {score * 100:>5.1f}%")

    print("\n  ⚛ SUPRACONDUCTIVITÉ (PHASE 10) :")
    omega = metrics["resistance"]
    res_barre = "░" * int(min(10, omega * 10))
    print(f"    - Résistance Ω       : {res_barre:<10} {omega:.4f} (friction)")
    print(f"    - Pôle Alpha         : Ligne {metrics['pole_alpha']}")
    print(f"    - Pôle Omega         : Ligne {metrics['pole_omega']}")


def _executer_report(args: argparse.Namespace, fichiers: List[str]) -> int:
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


def _nom_rapport(fichier: str, sortie_demandee: Optional[str]) -> str:
    """Calcule le nom du fichier rapport de sortie."""
    if sortie_demandee:
        return sortie_demandee
    base = os.path.splitext(os.path.basename(fichier))[0]
    return f"RAPPORT_PHI_{base}.md"


def _executer_suture(args: argparse.Namespace) -> int:
    """Exécute la commande de suture via Phidélia."""
    from . import suture as phi_suture

    print(f"  ◈  Inspiration de Phidélia pour {args.path}...")
    try:
        suggestion = phi_suture(args.path, api_url=args.url)
        print("\n" + suggestion)
        return 0
    except Exception as e:
        print(f"  ❌ Erreur lors de la suture : {e}")
        return 1


def _executer_seal(args: argparse.Namespace) -> int:
    """Phase 12 : Appose un sceau gnostique permanent sur un fichier."""
    from .gnose import MoteurGnostique
    from .analyseur import AnalyseurPhi

    print(f"  🛡  Scellement gnostique de {args.cible}...")
    try:
        analyseur = AnalyseurPhi(args.cible)
        resultat = analyseur.analyser()
        gnose = MoteurGnostique()
        sceau = gnose.sceller(resultat)
        print(f"      Sceau apposé : {sceau[:16]}... (Z[φ] Resonance Locked)")
        return 0
    except Exception as e:
        print(f"  ❌ Erreur de scellement : {e}")
        return 1


def _executer_heal(args: argparse.Namespace) -> int:
    """Phase 12 : Tente une guérison autonome du fichier."""
    from .autosuture import AutoSuture

    print(f"  ⚕  Tentative de guérison autonome pour {args.cible}...")
    try:
        medecin = AutoSuture(api_url=args.url)
        verdict = medecin.guerir(args.cible, force=args.force)
        print(f"\n  {verdict}")
        return 0
    except Exception as e:
        print(f"  ❌ Échec de la guérison : {e}")
        return 1


def _executer_metadata(args: argparse.Namespace) -> int:
    """Phase 15 : Synthèse et purge souveraine des métadonnées."""
    from .metadata_ops import (
        default_sanitized_path,
        format_summary_text,
        sanitize_harvest,
        summarize_metadata,
    )

    metadata_action = getattr(args, "metadata_action", None)
    if metadata_action not in {"summary", "purge"}:
        print("❌ Commande 'metadata' requiert une action : summary ou purge.")
        metadata_parser = getattr(args, "_metadata_parser", None)
        if metadata_parser is not None:
            metadata_parser.print_help()
        else:
            print("ℹ️ Utilisez : phi metadata {summary|purge} --help")
        return 1

    if metadata_action == "summary":
        try:
            resume = summarize_metadata(args.harvest, args.vault_index)
            if args.format == "json":
                print(json.dumps(resume, ensure_ascii=False, indent=2))
            else:
                print(format_summary_text(resume))
            return 0
        except (ValueError, RuntimeError, OSError) as e:
            print(f"❌ Erreur metadata : {e}")
            return 1
        except Exception as e:
            print(f"❌ Erreur metadata inattendue : {e}")
            traceback.print_exc()
            return 1

    if metadata_action == "purge":
        try:
            sortie = args.harvest if args.in_place else args.output
            if not sortie:
                sortie = default_sanitized_path(args.harvest)
            resultat = sanitize_harvest(
                args.harvest,
                sortie,
                strip_keys=args.strip,
                strip_sensitive=args.strip_sensitive,
                strip_labels=args.strip_labels,
                keep_only_features=args.keep_features,
            )
            print(
                f"✦ Corpus purgé → {resultat['output']} ({resultat['written']} vecteurs)"
            )
            if resultat["removed_keys"]:
                print(f"  Clés retirées : {', '.join(resultat['removed_keys'])}")
            if resultat["kept_features_only"]:
                print(
                    "  Mode features-only : seules les métriques structurelles sont conservées."
                )
            return 0
        except (ValueError, RuntimeError, OSError) as e:
            print(f"❌ Erreur metadata : {e}")
            return 1
        except Exception as e:
            print(f"❌ Erreur metadata inattendue : {e}")
            traceback.print_exc()
            return 1

    return 1


def _executer_oracle(args: argparse.Namespace, fichiers: List[str]) -> int:
    """Phase 14 : Valide une release selon l'Oracle de Radiance."""
    from .oracle import OracleRadiance

    oracle = OracleRadiance()
    verdict = oracle.valider_release(fichiers, args.min_radiance, args.nb_tests)
    print(oracle.rapport_oracle(verdict))
    return 0 if verdict["acceptee"] else 1


def _executer_harvest(args: argparse.Namespace, fichiers: List[str]) -> int:
    """Phase 14 : Collecte des vecteurs AST anonymisés (phi-harvest)."""
    from .harvest import HarvestEngine

    engine = HarvestEngine(sortie=args.output)
    nb_collectes = 0
    nb_erreurs = 0
    for fichier in fichiers:
        try:
            engine.collecter_et_exporter(fichier)
            nb_collectes += 1
        except Exception as e:
            print(f"  ⚠  {fichier} : {e}")
            nb_erreurs += 1
    print(f"\n  ✦  {nb_collectes} vecteur(s) collecté(s) → {args.output}")
    print(engine.rapport_harvest())
    return 1 if nb_erreurs > 0 else 0


def _executer_spiral(fichiers: List[str]) -> int:
    """Phase 14 : Affiche la Spirale Dorée de radiance pour chaque fichier."""
    from . import auditer as phi_auditer
    from .rapport import GenerateurRapport

    for fichier in fichiers:
        try:
            metriques = phi_auditer(fichier)
            gen = GenerateurRapport(metriques)
            print(f"\n  📄 {fichier}")
            print(gen.spirale_doree())
        except Exception as e:
            print(f"  ❌ {fichier} : {e}")
            return 1
    return 0


def _executer_memory() -> int:
    """Affiche les annales akashiques avec le moteur holographique."""
    from .akasha import RegistreAkashique, MatriceHolographique
    import time

    akasha = RegistreAkashique()
    annales = akasha.consulter_historique(10)

    print("\n  𓂀  ANNALES AKASHIQUES — MÉMOIRE HOLOGRAPHIQUE")
    print("  " + "─" * 45)

    if not annales:
        print("      L'Akasha est encore vierge. Lancez un audit pour l'élever.")
        return 0

    for i, entry in enumerate(annales):
        timestamp = entry.get("timestamp", time.time())
        date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))
        f = os.path.basename(entry["fichier"])
        print(f"\n  [{i + 1}] {f} — {date_str}")
        print(
            f"      Radiance: {entry['radiance']:.1f} | Masse Harmonique: {entry.get('masse_harmonique', 'N/A')}"
        )
        print(f"      Cohérence C_bit: {entry.get('coherence_c_bit', 'N/A')}%")

        # Affichage du dôme de résonance si le vecteur est présent
        if "vecteur" in entry:
            # Reconstruction de la matrice pour affichage
            donnees_simulees = {
                "radiance": entry["radiance"],
                "resistance": entry.get("resistance", 0),
                "lilith_variance": entry.get("lilith_variance", 0),
                "shannon_entropy": entry.get("shannon_entropy", 0),
                "phi_ratio": entry.get("phi_ratio", 0),
            }
            mat = MatriceHolographique(donnees_simulees)
            mat.vecteur = entry["vecteur"]
            print(mat.vers_grille())

    print("\n  ◈  Utilisez 'phi suture <fichier>' pour puiser dans cette sagesse.")
    return 0


def _executer_fund() -> None:
    """Affiche le message de soutien à la recherche souveraine."""
    print(
        """
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
    """
    )


def _executer_vault(args: argparse.Namespace, fichiers: List[str]) -> int:
    """Phase 16 : Audite et enregistre dans le Phi Vault."""
    from .vault import PhiVault

    vault = PhiVault()
    nb_erreurs = 0
    for fichier in fichiers:
        try:
            metriques = auditer(fichier)
            regressions = vault.detecter_regressions(metriques)
            for reg in regressions:
                print(f"  {reg}")
            note_path = vault.enregistrer_audit(metriques)
            radiance = metriques.get("radiance", 0.0)
            print(f"  ✦ {fichier} → vault ({radiance:.1f}) : {note_path}")
        except Exception as e:
            print(f"  ❌ {fichier} : {e}")
            nb_erreurs += 1
    print(f"\n  ◈ {len(fichiers)} fichier(s) archivé(s) dans le Phi Vault.")
    return 1 if nb_erreurs > 0 else 0


def _executer_graph(args: argparse.Namespace) -> int:
    """Phase 16 : Affiche le graphe de radiance du vault."""
    try:
        from .vault import PhiVault

        vault = PhiVault()
        fmt = getattr(args, "format", "ascii")
        if fmt == "dot":
            print(vault.generer_graph())
        else:
            print(vault.generer_graph_ascii())
        return 0
    except Exception as e:
        print(f"  ❌ Erreur lors de la génération du graphe : {e}")
        return 1


def _executer_canvas(args: argparse.Namespace, fichiers: List[str]) -> int:
    """Phase 17 : Exporte un Canvas Obsidian du code audité."""
    from .canvas import PhiCanvas

    canvas = PhiCanvas()
    for fichier in fichiers:
        try:
            metriques = auditer(fichier)
            canvas.ajouter_fichier(metriques)
        except Exception as e:
            print(f"  ⚠ {fichier} : {e}")

    sortie = args.output
    canvas.exporter(sortie)
    print(
        f"  ✦ Canvas exporté : {sortie} ({len(canvas.nodes)} nœuds, {len(canvas.edges)} arêtes)"
    )
    return 0


def _executer_search(args: argparse.Namespace) -> int:
    """Phase 18 : Recherche sémantique dans le vault."""
    from .search import PhiSearch

    search = PhiSearch()

    if args.statut:
        resultats = search.chercher_par_statut(args.statut)
        print(search.rapport_recherche(resultats, f"Statut: {args.statut}"))
    elif args.etat_zero:
        resultats = search.chercher_transitions_zero(args.etat_zero)
        print(search.rapport_recherche(resultats, f"État Zéro: {args.etat_zero}"))
    elif args.categorie:
        resultats = search.chercher_annotations(args.categorie)
        print(search.rapport_recherche(resultats, f"Catégorie: {args.categorie}"))
    else:
        resultats = search.chercher_par_radiance(args.min_radiance, args.max_radiance)
        print(
            search.rapport_recherche(
                resultats,
                f"Radiance [{args.min_radiance:.0f}-{args.max_radiance:.0f}]",
            )
        )
    return 0


def _executer_sbom(args: argparse.Namespace) -> int:
    """Phase 20 : Génère le Software Bill of Materials."""
    from .securite import exporter_sbom

    sortie = args.output
    exporter_sbom(sortie)
    print(f"  ✦ SBOM exporté : {sortie}")
    return 0


def _executer_shield(args: argparse.Namespace, fichiers: List[str]) -> int:
    """Phase 22 : Audit sécurité unifié avec gate CI."""
    from .securite import (
        JournalAudit,
        construire_audit_securite,
        exporter_audit_securite,
        journaliser_conflit_audit,
        verifier_politique_securite,
    )

    if args.sarif and not os.path.exists(args.sarif):
        print(f"❌ Fichier SARIF introuvable : {args.sarif}")
        return 1

    audit = construire_audit_securite(
        fichiers=fichiers,
        sarif_path=args.sarif,
        include_demo=args.include_demo,
    )
    exporter_audit_securite(audit, args.output)

    summary = audit["summary"]
    score = float(summary["security_score"])
    status = (
        "PASS"
        if verifier_politique_securite(audit, args.min_security_score)
        else "FAIL"
    )
    oos = int(summary.get("out_of_scope_findings", 0))
    print(
        f"  ✦ Shield: {status} | score={score:.2f} | "
        f"findings={summary['findings_total']} | blocking={summary['blocking_findings']}"
        + (f" | out_of_scope={oos}" if oos else "")
    )
    print(f"  ✦ Audit exporté : {args.output}")

    journal = JournalAudit()
    journal.enregistrer(
        "SECURITY_AUDIT",
        {
            "target_count": len(fichiers),
            "score": score,
            "status": status,
            "blocking_findings": int(summary["blocking_findings"]),
            "out_of_scope_findings": oos,
            "sarif": args.sarif or "",
        },
    )
    if status != "PASS" or audit.get("errors"):
        conflit = journaliser_conflit_audit(
            audit=audit,
            sorties={
                "summary": f"Shield: {status} | score={score:.2f}",
                "stderr": "\n".join(audit.get("errors", [])),
                "errors": audit.get("errors", []),
            },
            contexte={
                "target_count": len(fichiers),
                "sarif": args.sarif or "",
            },
        )
        resolution = conflit.get("resolution", {})
        print(
            "  ✦ Consensus conflit: "
            f"{resolution.get('decision', 'UNKNOWN')} | "
            f"score={float(resolution.get('consensus_score', 0.0)):.2f}"
        )
    return 0 if status == "PASS" else 1


def _executer_scan(args: argparse.Namespace, fichiers: List[str]) -> int:
    """Phase 24 : Scanner des fichiers avec le φ-fingerprint antiviral."""
    import json as _json
    import os
    import sys

    from .fingerprint import FingerprintEngine
    from .harvest import HarvestEngine

    if getattr(args, "harvest", False) and getattr(args, "output", None):
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            print(f"❌ Le dossier de sortie n'existe pas : {output_dir}")
            sys.exit(1)

    engine = FingerprintEngine()
    resultats: List[Dict[str, Any]] = []
    nb_suspects = 0

    for fichier in fichiers:
        try:
            fp = engine.calculer(fichier)
            entry: Dict[str, Any] = {
                "fichier": fichier,
                **fp.to_dict(),
            }
            resultats.append(entry)

            if fp.classification != "SAIN":
                nb_suspects += 1

            if args.format == "console":
                _afficher_scan_console(fichier, fp)

            # Optionnel : collecter dans le corpus harvest
            if getattr(args, "harvest", False):
                try:
                    harvest = HarvestEngine(sortie=args.output)
                    harvest.collecter_et_exporter_fingerprint(fichier)
                except Exception:
                    pass

        except Exception as e:
            entry = {"fichier": fichier, "erreur": str(e)}
            resultats.append(entry)
            if args.format == "console":
                print(f"  ❌ {fichier} : {e}")

    if args.format == "json":
        sortie = resultats[0] if len(resultats) == 1 else resultats
        print(_json.dumps(sortie, ensure_ascii=False, indent=2))
    elif args.format == "console":
        _afficher_scan_resume(len(fichiers), nb_suspects)

    return 1 if nb_suspects > 0 else 0


def _afficher_scan_console(fichier: str, fp: PhiFingerprint) -> None:
    """Affiche le résultat d'un scan en mode console."""
    symboles = {
        "SAIN": "✅",
        "SUSPECT": "⚠️ ",
        "MALVEILLANT": "🚨",
    }
    symbole = symboles.get(fp.classification, "❓")

    pct = fp.score_anomalie * 100
    barre_len = 20
    rempli = int(pct / 100 * barre_len)
    barre = "█" * rempli + "░" * (barre_len - rempli)

    print(f"\n  📄 {fichier}")
    print(f"      Format     : {fp.format_source}")
    print(f"      Anomalie   : [{barre}] {pct:.1f}%")
    print(f"      Verdict    : {symbole}  {fp.classification}")
    print(f"      Sections   : {fp.nb_sections}")
    print(f"      Vecteur φ  : [{', '.join(f'{v:.3f}' for v in fp.vecteur)}]")


def _afficher_scan_resume(total: int, suspects: int) -> None:
    """Affiche le résumé final du scan."""
    print("\n╔══════════════════════════════════════════════════╗")
    print("║   PHI-SENTINEL — SCAN ANTIVIRAL UNIVERSEL         ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"\n  ◈  Fichiers scannés   : {total}")
    print(f"  ✅ Sains              : {total - suspects}")
    if suspects > 0:
        print(f"  ⚠  Suspects/Malveillants : {suspects}")
    else:
        print("  ✦  Aucune menace détectée.")
    print("\n  ─────────────────────────────────────────────────")
    print("  Ancré dans le Morphic Phi Framework — φ-Meta 2026")


def _executer_ui() -> int:
    """Phase 33 : Lance le backend FastAPI et ouvre le navigateur (IDE Web Local)."""
    try:
        import uvicorn
        import webbrowser
        from threading import Timer

        url = "http://127.0.0.1:8000"

        def open_browser() -> None:
            import urllib.request
            import time
            from urllib.error import URLError

            # Polling au lieu de délai fixe pour éviter la race condition
            for _ in range(30):
                try:
                    urllib.request.urlopen(url)
                    webbrowser.open(url)
                    return
                except URLError:
                    time.sleep(0.2)

        print("  ◈  Lancement de la Cyber Station Phidélia...")
        print(f"  ◈  Interface locale : {url}")

        Timer(0.1, open_browser).start()
        uvicorn.run(
            "phi_complexity.web.server:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="warning",
        )
        return 0
    except ImportError:
        print("❌ Erreur : Le module web n'est pas installé.")
        print("👉 Veuillez installer avec : pip install phi-complexity[web]")
        return 1
    except Exception as e:
        print(f"❌ Erreur critique lors du lancement : {e}")
        return 1


# ────────────────────────────────────────────────────────
# POINT D'ENTRÉE (hermétique — orchestre uniquement)
# ────────────────────────────────────────────────────────


def main() -> None:  # phi: ignore[CYCLOMATIQUE]
    """Point d'entrée principal. Délègue à des fonctions spécialisées."""
    parser = _construire_parseur()
    args = parser.parse_args()

    if not args.commande:
        parser.print_help()
        sys.exit(0)

    if args.commande == "ui":
        sys.exit(_executer_ui())

    if args.commande == "memory":
        sys.exit(_executer_memory())

    if args.commande == "fund":
        _executer_fund()
        sys.exit(0)

    if args.commande == "suture":
        sys.exit(_executer_suture(args))

    if args.commande == "seal":
        sys.exit(_executer_seal(args))

    if args.commande == "heal":
        sys.exit(_executer_heal(args))

    # Phase 16 — commandes sans collecte de fichiers
    if args.commande == "graph":
        sys.exit(_executer_graph(args))

    # Phase 18 — recherche dans le vault
    if args.commande == "search":
        sys.exit(_executer_search(args))

    # Phase 20 — SBOM
    if args.commande == "sbom":
        sys.exit(_executer_sbom(args))

    if args.commande == "metadata":
        sys.exit(_executer_metadata(args))

    # Phase 14 — commandes sans collecte de fichiers préalable
    if args.commande == "spiral":
        fichiers = _collecter_fichiers(args.cible)
        if not fichiers:
            print(f"❌ Aucun fichier supporté trouvé dans : {args.cible}")
            sys.exit(1)
        sys.exit(_executer_spiral(fichiers))

    # Phase 24 — scan antiviral (accepte source + binaire)
    if args.commande == "scan":
        fichiers = _collecter_fichiers_scan(args.cible)
        if not fichiers:
            print(f"❌ Aucun fichier scannable trouvé dans : {args.cible}")
            sys.exit(1)
        sys.exit(_executer_scan(args, fichiers))

    fichiers = _collecter_fichiers(args.cible)
    if not fichiers:
        print(f"❌ Aucun fichier supporté trouvé dans : {args.cible}")
        sys.exit(1)

    if args.commande == "check":
        sys.exit(_executer_check(args, fichiers))
    elif args.commande == "report":
        sys.exit(_executer_report(args, fichiers))
    elif args.commande == "oracle":
        sys.exit(_executer_oracle(args, fichiers))
    elif args.commande == "harvest":
        sys.exit(_executer_harvest(args, fichiers))
    elif args.commande == "vault":
        sys.exit(_executer_vault(args, fichiers))
    elif args.commande == "canvas":
        sys.exit(_executer_canvas(args, fichiers))
    elif args.commande == "shield":
        sys.exit(_executer_shield(args, fichiers))
    else:
        print(f"❌ Commande inconnue : {args.commande}")
        sys.exit(1)


if __name__ == "__main__":
    main()
