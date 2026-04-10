"""
phi_complexity/oracle.py — Oracle de Radiance (Phase 14)
Gardien du Versionnement Souverain : bloque une release si la radiance chute.

Loi de version Phi : v{floor(radiance)}.{nb_tests}
Ancrage : EQ-AFR-BMAD (Loi Antifragile) + AX-A39 (Attracteur Doré).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from .core import PHI


class OracleRadiance:
    """
    Oracle de Radiance — Gardien du Versionnement Souverain.

    Audite un ensemble de fichiers et délivre un verdict de release :
    si la radiance globale est en-dessous du seuil, la release est bloquée.
    La version suit la loi Phi : v{floor(radiance_globale)}.{nb_tests}.
    """

    SEUIL_PAR_DEFAUT: float = 70.0

    def calculer_version_phi(self, radiance: float, nb_tests: int) -> str:
        """Calcule la version Phi : v{floor(radiance)}.{nb_tests}."""
        return f"v{int(math.floor(radiance))}.{nb_tests}"

    def auditer_fichiers(self, fichiers: List[str]) -> List[Dict[str, Any]]:
        """Audite une liste de fichiers et retourne leurs métriques individuelles."""
        from . import auditer as phi_auditer

        resultats: List[Dict[str, Any]] = []
        for f in fichiers:
            try:
                resultats.append(phi_auditer(f))
            except Exception as e:
                resultats.append(
                    {
                        "fichier": f,
                        "radiance": 0.0,
                        "erreur": str(e),
                    }
                )
        return resultats

    def calculer_radiance_globale(self, audits: List[Dict[str, Any]]) -> float:
        """
        Calcule la radiance globale comme moyenne pondérée par φ.
        Pondération dorée : les fichiers à haute radiance pèsent plus (φ-Weighted Mean).
        Les fichiers en erreur (radiance == 0 ET clé 'erreur' présente) sont exclus
        du calcul pour ne pas pénaliser injustement la release.
        """
        if not audits:
            return 0.0
        audits_valides = [
            a
            for a in audits
            if not (max(0.0, float(a.get("radiance", 0.0))) == 0.0 and "erreur" in a)
        ]
        if not audits_valides:
            return 0.0
        radiancies = [max(0.0, float(a.get("radiance", 0.0))) for a in audits_valides]
        poids = [r / PHI for r in radiancies]
        total_poids = sum(poids)
        if total_poids == 0.0:
            return 0.0
        return sum(r * p for r, p in zip(radiancies, poids)) / total_poids

    def valider_release(
        self,
        fichiers: List[str],
        seuil: float = SEUIL_PAR_DEFAUT,
        nb_tests: int = 0,
    ) -> Dict[str, Any]:
        """
        Délivre le verdict de release selon l'Oracle de Radiance.
        Retourne un dictionnaire complet : acceptée/bloquée + version Phi.
        """
        audits = self.auditer_fichiers(fichiers)
        radiance_globale = self.calculer_radiance_globale(audits)
        acceptee = radiance_globale >= seuil
        version = self.calculer_version_phi(radiance_globale, nb_tests)
        fichiers_sous_seuil = [
            str(a.get("fichier", ""))
            for a in audits
            if float(a.get("radiance", 0.0)) < seuil
        ]
        return {
            "acceptee": acceptee,
            "radiance_globale": round(radiance_globale, 2),
            "seuil": seuil,
            "version_phi": version,
            "nb_fichiers": len(fichiers),
            "nb_tests": nb_tests,
            "fichiers_sous_seuil": fichiers_sous_seuil,
            "audits": audits,
        }

    def rapport_oracle(self, verdict: Dict[str, Any]) -> str:
        """Génère le rapport ASCII de l'Oracle de Radiance."""
        acceptee: bool = bool(verdict["acceptee"])
        symbole = "✦ RELEASE AUTORISÉE" if acceptee else "░ RELEASE BLOQUÉE"

        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║      PHI-ORACLE — VALIDATION DE RELEASE          ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  {'☼' if acceptee else '⚠'}  {symbole}",
            f"  Version Phi    : {verdict['version_phi']}",
            f"  Radiance Globale : {verdict['radiance_globale']} / 100",
            f"  Seuil Requis   : {verdict['seuil']}",
            f"  Fichiers audités : {verdict['nb_fichiers']}",
            f"  Tests passés   : {verdict['nb_tests']}",
            "",
        ]
        sous_seuil: List[str] = list(verdict.get("fichiers_sous_seuil", []))
        if sous_seuil:
            lignes.append(f"  ⚠  FICHIERS SOUS SEUIL ({len(sous_seuil)}) :")
            for f in sous_seuil:
                lignes.append(f"    - {f}")
        else:
            lignes.append("  ✦  Tous les fichiers respectent le seuil de radiance.")
        lignes += [
            "",
            "  ─────────────────────────────────────────────────",
            "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
        ]
        return "\n".join(lignes)
