from __future__ import annotations
import datetime
import json
import math
from typing import Dict, Any, List

# Constantes de la Spirale Dorée
_TERMINAL_ASPECT_RATIO: float = (
    2.0  # Les caractères terminaux sont ~2× plus hauts que larges
)
_SPIRAL_EPSILON: float = 0.001  # Garde-fou anti-division par zéro


class GenerateurRapport:
    """Transforme un dictionnaire de métriques en rapport premium."""

    def __init__(self, metriques: Dict[str, Any]):
        self.m = metriques

    # ──────────────────────────────────────────────
    # RENDU CONSOLE (ASCII Premium)
    # ──────────────────────────────────────────────

    def console(self) -> str:
        """Sortie console premium avec barres visuelles (Aesthetic V0.1.0 pure)."""
        m = self.m
        score = m.get("radiance", 0.0)
        barre = self._barre(score)
        phi_r = m.get("phi_ratio", 1.0)
        delta = m.get("phi_ratio_delta", 0.0)
        zeta = m.get("zeta_score", 0.0)
        lilith = m.get("lilith_variance", 0.0)
        shannon = m.get("shannon_entropy", 0.0)
        phi_icon = "◈"

        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║     PHI-COMPLEXITY — AUDIT DE RADIANCE           ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  📄 Fichier : {m.get('fichier', '?')}",
            f"  📅 Date    : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"  ☼  RADIANCE      : {barre}     {score:.1f} / 100",
            f"  ⚖  LILITH        : {lilith:<7.1f}  (Structural variance)",
            f"  🌊 ENTROPIE      : {shannon:<4.2f} bits   (Shannon)",
            f"  {phi_icon}  PHI-RATIO     : {phi_r:<4.2f}        (ideal: φ = 1.618, Δ={delta:.2f})",
            f"  ζ  ZETA-SCORE    : {zeta:<6.4f}     (Global resonance)",
            "",
            f"  STATUT : {m.get('statut_gnostique', 'INCONNU')} ◈",
            "",
        ]

        # Oudjat
        oudjat_data = m.get("oudjat")
        if oudjat_data:
            lignes.append(
                f"  👁  OUDJAT : '{oudjat_data.get('nom', '?')}' (Line {oudjat_data.get('ligne', '?')}, Complexity: {oudjat_data.get('complexite', '?')})"
            )
            lignes.append("")

        # Annotations (Sutures)
        annotations = m.get("annotations", [])
        if annotations:
            lignes.append(f"  ⚠  SUTURES IDENTIFIED ({len(annotations)}):")
            for ann in annotations:
                icon = (
                    "🔴"
                    if ann.get("niveau") == "CRITICAL"
                    else "🟡" if ann.get("niveau") == "WARNING" else "🔵"
                )
                lignes.append(
                    f"  {icon} Line {ann.get('ligne', '?')} [{ann.get('categorie', '?')}] : {ann.get('message', '?')}"
                )
                lignes.append(f"     >> {ann.get('extrait', '')}")
        else:
            lignes.append("  ✦  Aucune rupture de radiance majeure détectée.")

        lignes.append("")
        lignes.append("  ─────────────────────────────────────────────────")
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
        oudjat_data = m.get("oudjat")
        if oudjat_data:
            rapport += "## 3. IDENTIFICATION DE L'OUDJAT\n\n"
            rapport += f"La fonction la plus 'chargée' est **`{oudjat_data.get('nom', '?')}`** (Ligne {oudjat_data.get('ligne', '?')}).\n\n"
            rapport += f"- Pression : **{oudjat_data.get('complexite', '?')}** unités de complexité\n"
            rapport += f"- Taille   : **{oudjat_data.get('nb_lignes', '?')}** lignes\n"
            rapport += f"- φ-Ratio  : **{oudjat_data.get('phi_ratio', '?')}** (idéal: 1.618)\n\n"

        # Section 4 — Audit Fractal
        rapport += "## 4. REVUE DE DÉTAIL (AUDIT FRACTAL)\n\n"
        annotations = m.get("annotations", [])
        if not annotations:
            rapport += (
                "☼ Aucune rupture de radiance majeure détectée au niveau micro.\n\n"
            )
        else:
            rapport += f"Phidélia a identifié **{len(annotations)}** zones nécessitant une suture :\n\n"
            for ann in annotations:
                niveau_md = (
                    "CAUTION"
                    if ann["niveau"] == "CRITICAL"
                    else "WARNING" if ann["niveau"] == "WARNING" else "NOTE"
                )
                rapport += f"> [!{niveau_md}]\n"
                rapport += f"> **Ligne {ann['ligne']}** `[{ann['categorie']}]` : {ann['message']}\n"
                rapport += f"> `>> {ann['extrait']}`\n\n"

        # Pied de page
        rapport += "---\n"
        rapport += (
            "*phi-complexity — Morphic Phi Framework (φ-Meta) — Tomy Verreault, 2026*\n"
        )
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

    # ──────────────────────────────────────────────
    # SPIRALE DORÉE (Visualisation φ)
    # ──────────────────────────────────────────────

    def spirale_doree(self) -> str:
        """
        Visualisation ASCII de la Spirale Dorée (φ-Meta Phase 14).
        Utilise le motif de Fibonacci (angle doré ≈ 137.5°) pour placer
        les points : plus la radiance est haute, plus la spirale est dense.
        """
        score = float(self.m.get("radiance", 50.0))
        largeur, hauteur = 41, 17
        grille: List[List[str]] = [[" "] * largeur for _ in range(hauteur)]
        cx, cy = largeur // 2, hauteur // 2
        golden_angle = math.pi * (
            3 - math.sqrt(5)
        )  # ≈ 2.39996 rad ≈ 137.508° (angle doré)
        n_points = min(100, max(5, int(score)))
        denom = math.sqrt(max(n_points - 1, 1))
        scale = min(cx, cy * _TERMINAL_ASPECT_RATIO) / denom

        for i in range(n_points):
            r = math.sqrt(i) * scale
            theta = i * golden_angle
            x = int(cx + r * math.cos(theta))
            y = int(cy + r * math.sin(theta) / _TERMINAL_ASPECT_RATIO)
            if 0 <= x < largeur and 0 <= y < hauteur:
                ratio = r / (scale * denom + _SPIRAL_EPSILON)
                if i == 0:
                    grille[y][x] = "☼"
                elif ratio < 0.3:
                    grille[y][x] = "✦"
                elif ratio < 0.65:
                    grille[y][x] = "◈"
                else:
                    grille[y][x] = "░"

        phi_r = float(self.m.get("phi_ratio", 1.0))
        delta = float(self.m.get("phi_ratio_delta", 0.0))
        harmonie = "harmonie ✦" if delta < 0.5 else "divergence ░"
        lignes_grille = ["  " + "".join(row) for row in grille]
        lignes = [
            "  ☼  φ-SPIRALE DE RADIANCE (Motif Fibonacci / Angle Doré 137.5°)",
            f"     Score: {score:.1f} / 100  |  φ-Ratio: {phi_r:.3f}  |  {harmonie}",
            "",
            *lignes_grille,
            "",
            "     ☼ noyau  ✦ zone interne  ◈ zone médiane  ░ périphérie",
        ]
        return "\n".join(lignes)
