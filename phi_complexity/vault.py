"""
phi_complexity/vault.py — Phi Vault : Mémoire Persistante type Obsidian.

Stocke l'historique complet des audits sous forme de fichiers Markdown interliés
(wikilinks [[fichier]]), avec journal chronologique et détection de régressions.

Phase 16 du Morphic Phi Framework.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from .core import PHI, statut_gnostique


class PhiVault:
    """
    Vault souverain de métriques — inspiré d'Obsidian.

    Chaque audit génère une note Markdown dans ``.phi/vault/``
    avec des wikilinks ``[[fichier]]`` vers les fichiers liés.
    Un journal quotidien trace l'évolution de la radiance.
    """

    def __init__(self, workspace_root: str = ".") -> None:
        self.phi_dir = os.path.join(workspace_root, ".phi")
        self.vault_dir = os.path.join(self.phi_dir, "vault")
        self.journal_dir = os.path.join(self.vault_dir, "journal")
        self.index_path = os.path.join(self.vault_dir, "index.json")
        self._initialiser_vault()

    def _initialiser_vault(self) -> None:
        """Crée la structure du vault si elle n'existe pas."""
        for d in (self.phi_dir, self.vault_dir, self.journal_dir):
            if not os.path.exists(d):
                os.makedirs(d)
        if not os.path.exists(self.index_path):
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump({"notes": {}, "version": "16.0"}, f)

    def enregistrer_audit(self, metriques: Dict[str, Any]) -> str:
        """
        Crée une note Markdown pour un audit et l'enregistre dans l'index.
        Retourne le chemin de la note créée.
        """
        fichier = str(metriques.get("fichier", "inconnu"))
        note_nom = self._nom_note(fichier)
        note_path = os.path.join(self.vault_dir, note_nom)

        contenu = self._generer_note(metriques)
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(contenu)

        # Mettre à jour l'index
        self._mettre_a_jour_index(fichier, note_nom, metriques)

        # Écrire dans le journal quotidien
        self._ecrire_journal(fichier, metriques)

        return note_path

    def _nom_note(self, fichier: str) -> str:
        """Génère un nom de note sûr à partir du chemin du fichier."""
        base = os.path.basename(fichier)
        safe_name = base.replace(".", "_").replace("/", "_").replace("\\", "_")
        return f"{safe_name}.md"

    def _generer_note(self, metriques: Dict[str, Any]) -> str:
        """Génère le contenu Markdown d'une note d'audit avec wikilinks."""
        fichier = str(metriques.get("fichier", "inconnu"))
        radiance = float(metriques.get("radiance", 0.0))
        statut = statut_gnostique(radiance)
        date_str = time.strftime("%Y-%m-%d %H:%M:%S")

        lignes = [
            f"# 📄 {os.path.basename(fichier)}",
            "",
            f"> Audit réalisé le {date_str}",
            "",
            "## Métriques",
            "",
            "| Métrique | Valeur |",
            "|----------|--------|",
            f"| **Radiance** | {radiance:.2f} / 100 |",
            f"| **Statut** | {statut} |",
            f"| **Lilith Variance** | {metriques.get('lilith_variance', 0.0):.2f} |",
            f"| **Shannon Entropy** | {metriques.get('shannon_entropy', 0.0):.2f} bits |",
            f"| **Phi-Ratio** | {metriques.get('phi_ratio', 0.0):.4f} (φ = {PHI:.4f}) |",
            f"| **Zeta-Score** | {metriques.get('zeta_score', 0.0):.4f} |",
            f"| **Fibonacci Distance** | {metriques.get('fibonacci_distance', 0.0):.2f} |",
            f"| **Résistance Ω** | {metriques.get('resistance', 0.0):.4f} |",
            "",
        ]

        # Wikilinks vers les fonctions
        fonctions = metriques.get("fonctions", [])
        if fonctions:
            lignes.append("## Fonctions")
            lignes.append("")
            for fn in fonctions:
                fn_dict = fn if isinstance(fn, dict) else {}
                nom = fn_dict.get("nom", "?")
                complexite = fn_dict.get("complexite", 0)
                lignes.append(
                    f"- [[{nom}]] — Complexité: {complexite}, "
                    f"Ligne: {fn_dict.get('ligne', '?')}"
                )
            lignes.append("")

        # Oudjat
        oudjat = metriques.get("oudjat")
        if oudjat:
            oudjat_dict = oudjat if isinstance(oudjat, dict) else {}
            lignes.append("## 🔎 Oudjat (Fonction Dominante)")
            lignes.append("")
            lignes.append(
                f"- **[[{oudjat_dict.get('nom', '?')}]]** — "
                f"Complexité: {oudjat_dict.get('complexite', 0)}, "
                f"Ligne: {oudjat_dict.get('ligne', '?')}"
            )
            lignes.append("")

        # Annotations
        annotations = metriques.get("annotations", [])
        if annotations:
            lignes.append("## ⚠ Annotations")
            lignes.append("")
            for ann in annotations:
                ann_dict = ann if isinstance(ann, dict) else {}
                cat = ann_dict.get("categorie", "?")
                msg = ann_dict.get("message", "?")
                ligne_no = ann_dict.get("ligne", "?")
                lignes.append(f"- **[{cat}]** Ligne {ligne_no}: {msg}")
            lignes.append("")

        # Tags
        lignes.append("## Tags")
        lignes.append("")
        lignes.append(
            f"#phi-audit #{statut.split()[0].lower().replace('é', 'e')} "
            f"#radiance-{int(radiance)}"
        )
        lignes.append("")

        return "\n".join(lignes)

    def _mettre_a_jour_index(
        self, fichier: str, note_nom: str, metriques: Dict[str, Any]
    ) -> None:
        """Met à jour l'index JSON du vault."""
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                index = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            index = {"notes": {}, "version": "16.0"}

        index["notes"][fichier] = {
            "note": note_nom,
            "radiance": float(metriques.get("radiance", 0.0)),
            "statut": statut_gnostique(float(metriques.get("radiance", 0.0))),
            "timestamp": time.time(),
        }

        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def _ecrire_journal(self, fichier: str, metriques: Dict[str, Any]) -> None:
        """Ajoute une entrée au journal quotidien (daily notes)."""
        date_str = time.strftime("%Y-%m-%d")
        journal_path = os.path.join(self.journal_dir, f"{date_str}.md")

        heure = time.strftime("%H:%M:%S")
        radiance = float(metriques.get("radiance", 0.0))
        statut = statut_gnostique(radiance)

        entree = (
            f"- **{heure}** — [[{os.path.basename(fichier)}]] "
            f"— Radiance: {radiance:.2f} ({statut})\n"
        )

        # Append mode pour journal quotidien
        mode = "a" if os.path.exists(journal_path) else "w"
        with open(journal_path, mode, encoding="utf-8") as f:
            if mode == "w":
                f.write(f"# 📅 Journal Phi — {date_str}\n\n")
            f.write(entree)

    def consulter_index(self) -> Dict[str, Any]:
        """Retourne l'index complet du vault."""
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                return dict(json.load(f))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"notes": {}, "version": "16.0"}

    def lire_note(self, fichier: str) -> Optional[str]:
        """Lit le contenu d'une note du vault."""
        note_nom = self._nom_note(fichier)
        note_path = os.path.join(self.vault_dir, note_nom)
        if os.path.exists(note_path):
            with open(note_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def detecter_regressions(self, metriques: Dict[str, Any]) -> List[str]:
        """
        Détecte les régressions de radiance par rapport aux audits précédents.
        Retourne une liste de messages de régression.
        """
        fichier = str(metriques.get("fichier", ""))
        index = self.consulter_index()
        notes = index.get("notes", {})

        if fichier not in notes:
            return []

        ancienne_radiance = float(notes[fichier].get("radiance", 0.0))
        nouvelle_radiance = float(metriques.get("radiance", 0.0))

        regressions: List[str] = []
        delta = nouvelle_radiance - ancienne_radiance

        if delta < -5.0:
            regressions.append(
                f"⚠ RÉGRESSION : {os.path.basename(fichier)} — "
                f"Radiance {ancienne_radiance:.1f} → {nouvelle_radiance:.1f} "
                f"(Δ = {delta:+.1f})"
            )

        return regressions

    def generer_graph(self) -> str:
        """
        Génère une représentation DOT du graphe de dépendances
        avec les scores de radiance comme poids des nœuds.
        """
        index = self.consulter_index()
        notes = index.get("notes", {})

        lignes = [
            "digraph phi_vault {",
            "    rankdir=LR;",
            "    node [shape=box, style=filled];",
            "",
        ]

        for fichier, info in notes.items():
            radiance = float(info.get("radiance", 0.0))
            statut = str(info.get("statut", ""))
            base = os.path.basename(fichier)

            if "HERMÉTIQUE" in statut:
                color = "#2ecc71"
            elif "EN ÉVEIL" in statut:
                color = "#f39c12"
            else:
                color = "#e74c3c"

            label = f"{base}\\nRadiance: {radiance:.1f}"
            lignes.append(f'    "{base}" [label="{label}", fillcolor="{color}"];')

        lignes.append("}")
        return "\n".join(lignes)

    def generer_graph_ascii(self) -> str:
        """Génère une vue ASCII du graphe de radiance."""
        index = self.consulter_index()
        notes = index.get("notes", {})

        if not notes:
            return "  ░  Vault vide. Lancez un audit pour commencer."

        lignes = [
            "  ╔══════════════════════════════════════════════════╗",
            "  ║      PHI-VAULT — GRAPHE DE RADIANCE              ║",
            "  ╚══════════════════════════════════════════════════╝",
            "",
        ]

        for fichier, info in sorted(
            notes.items(), key=lambda x: float(x[1].get("radiance", 0)), reverse=True
        ):
            radiance = float(info.get("radiance", 0.0))
            statut = str(info.get("statut", ""))
            base = os.path.basename(fichier)

            barre_len = int(radiance / 5)
            barre = "█" * barre_len + "░" * (20 - barre_len)

            if "HERMÉTIQUE" in statut:
                icone = "✦"
            elif "EN ÉVEIL" in statut:
                icone = "◈"
            else:
                icone = "░"

            lignes.append(f"  {icone} {base:<30} {barre} {radiance:>6.1f}")

        lignes.append("")
        return "\n".join(lignes)
