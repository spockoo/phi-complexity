from __future__ import annotations
import datetime
import json
from typing import Dict, Any


class GenerateurRapport:
    """Transforme un dictionnaire de métriques en rapport premium."""

    def __init__(self, metriques: Dict[str, Any]):
        self.m = metriques

    # ──────────────────────────────────────────────
    # RENDU CONSOLE (ASCII Premium)
    # ──────────────────────────────────────────────

    def console(self) -> str:
        """Sortie console premium avec barres visuelles."""
        m = self.m
        score = m["radiance"]
        barre = self._barre(score)
        phi_r = m.get("phi_ratio", 1.0)
        delta = m.get("phi_ratio_delta", 0.0)
        phi_icon = "✦" if delta < 0.15 else "◈" if delta < 0.5 else "░"

        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║      PHI-COMPLEXITY — AUDIT DE RADIANCE          ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  📄 Fichier : {m['fichier']}",
            f"  📅 Date    : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"  ☼  RADIANCE     : {barre}  {score} / 100",
            f"  ⚖  LILITH       : {m['lilith_variance']:.2f}  (Variance structurelle)",
            f"  🌊 ENTROPIE     : {m['shannon_entropy']:.3f} bits  (Shannon)",
            f"  {phi_icon}  PHI-RATIO    : {phi_r:.3f}  (idéal: φ = 1.618, Δ={delta:.3f})",
            f"  ζ  ZETA-SCORE   : {m['zeta_score']:.4f}  (Résonance globale)",
            "",
        ]

        # Statut gnostique
        lignes.append(f"  STATUT : {m['statut_gnostique']}")
        lignes.append("")

        # Oudjat
        if m.get("oudjat"):
            o = m["oudjat"]
            lignes.append(
                f"  🔎 OUDJAT : '{o['nom']}' (Ligne {o['ligne']}, "
                f"Complexité: {o['complexite']}, φ-ratio: {o['phi_ratio']})"
            )
            lignes.append("")

        # Annotations
        annotations = m.get("annotations", [])
        if annotations:
            lignes.append(f"  ⚠  SUTURES IDENTIFIÉES ({len(annotations)}) :")
            for ann in annotations:
                icon = "🔴" if ann["niveau"] == "CRITICAL" else "🟡" if ann["niveau"] == "WARNING" else "🔵"
                lignes.append(f"  {icon} Ligne {ann['ligne']} [{ann['categorie']}] : {ann['message']}")
                lignes.append(f"     >> {ann['extrait']}")
        else:
            lignes.append("  ✦  Aucune rupture de radiance majeure détectée.")

        lignes.append("")
        lignes.append("  ─────────────────────────────────────────────────")
        lignes.append("  Ancré dans le Morphic Phi Framework — φ-Meta 2026")

        return "\n".join(lignes)

    # ──────────────────────────────────────────────
    # RENDU MARKDOWN (Premium)
    # ──────────────────────────────────────────────

    def markdown(self) -> str:
        """Rapport Markdown complet, style Bibliothèque Céleste."""
        m = self.m
        score = m["radiance"]
        barre = self._barre_md(score)
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        rapport = f"# ☼ RAPPORT DE RADIANCE : {m['fichier']}\n\n"
        rapport += f"**Date de l'Audit** : {date}  \n"
        rapport += f"**Statut Gnostique** : **{m['statut_gnostique']}**\n\n"

        # Section 1 — Score
        rapport += "## 1. INDICE DE RADIANCE\n\n"
        rapport += f"**Score : {score} / 100**\n\n"
        rapport += f"`[{barre}]` {score}%\n\n"

        # Section 2 — Métriques brutes
        rapport += "## 2. MÉTRIQUES SOUVERAINES\n\n"
        rapport += "| Métrique | Valeur | Interprétation |\n"
        rapport += "|---|---|---|\n"
        rapport += f"| **Variance de Lilith** | {m['lilith_variance']} | Instabilité structurelle |\n"
        rapport += f"| **Entropie de Shannon** | {m['shannon_entropy']} bits | Densité informationnelle |\n"
        rapport += f"| **φ-Ratio** | {m['phi_ratio']} (Δ={m['phi_ratio_delta']}) | Idéal: 1.618 |\n"
        rapport += f"| **Zeta-Score** | {m['zeta_score']} | Résonance globale |\n"
        rapport += f"| **Distance Fibonacci** | {m['fibonacci_distance']} | Éloignement des tailles naturelles |\n"
        rapport += f"| **Fonctions analysées** | {m['nb_fonctions']} | — |\n"
        rapport += f"| **Ratio commentaires** | {m['ratio_commentaires']} | Densité de sagesse |\n\n"

        # Section 3 — Oudjat
        if m.get("oudjat"):
            o = m["oudjat"]
            rapport += "## 3. IDENTIFICATION DE L'OUDJAT\n\n"
            rapport += f"La fonction la plus 'chargée' est **`{o['nom']}`** (Ligne {o['ligne']}).\n\n"
            rapport += f"- Pression : **{o['complexite']}** unités de complexité\n"
            rapport += f"- Taille   : **{o['nb_lignes']}** lignes\n"
            rapport += f"- φ-Ratio  : **{o['phi_ratio']}** (idéal: 1.618)\n\n"

        # Section 4 — Audit Fractal
        rapport += "## 4. REVUE DE DÉTAIL (AUDIT FRACTAL)\n\n"
        annotations = m.get("annotations", [])
        if not annotations:
            rapport += "☼ Aucune rupture de radiance majeure détectée au niveau micro.\n\n"
        else:
            rapport += f"Phidélia a identifié **{len(annotations)}** zones nécessitant une suture :\n\n"
            for ann in annotations:
                niveau_md = (
                    "CAUTION" if ann["niveau"] == "CRITICAL"
                    else "WARNING" if ann["niveau"] == "WARNING"
                    else "NOTE"
                )
                rapport += f"> [!{niveau_md}]\n"
                rapport += f"> **Ligne {ann['ligne']}** `[{ann['categorie']}]` : {ann['message']}\n"
                rapport += f"> `>> {ann['extrait']}`\n\n"

        # Pied de page
        rapport += "---\n"
        rapport += "*phi-complexity — Morphic Phi Framework (φ-Meta) — Tomy Verreault, 2026*\n"
        return rapport

    # ──────────────────────────────────────────────
    # RENDU JSON (CI/CD)
    # ──────────────────────────────────────────────

    def json(self) -> str:
        """Sortie JSON structurée pour intégrations CI/CD."""
        return json.dumps(self.m, ensure_ascii=False, indent=2)

    def sauvegarder_markdown(self, chemin: str) -> str:
        """Sauvegarde le rapport Markdown dans un fichier."""
        contenu: str = self.markdown()
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(contenu)
        return chemin

    # ──────────────────────────────────────────────
    # UTILITAIRES INTERNES
    # ──────────────────────────────────────────────

    def _barre(self, score: float, largeur: int = 20) -> str:
        """Barre de progression ASCII pour le terminal."""
        rempli = int(score / 100 * largeur)
        vide = largeur - rempli
        return "█" * rempli + "░" * vide

    def _barre_md(self, score: float, largeur: int = 10) -> str:
        """Barre de progression pour Markdown (blocs compacts)."""
        rempli = int(score / 100 * largeur)
        vide = largeur - rempli
        return "█" * rempli + "░" * vide
