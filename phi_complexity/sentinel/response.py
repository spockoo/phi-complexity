"""
phi_complexity/sentinel/response.py — Couche 5 : Alerting et Export OSS

Dernière couche de la chaîne Sentinel.
Prend les scores et signaux des couches précédentes et :
    - Classe les alertes par niveau de sévérité
    - Génère des rapports lisibles (console, JSON, Markdown)
    - Exporte les Indicateurs de Compromission (IoC) au format STIX/JSON
    - Produit des règles communautaires partageables

Format d'export IoC (inspiré de STIX 2.1 simplifié) :
    {
        "type": "indicator",
        "spec_version": "phi-sentinel/1.0",
        "pattern": "...",
        "confidence": 0.75,
        "mitre_technique": "T1059.004"
    }

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .bayesian import ScoreSentinel
from .behavior import SignalComportemental, TypeBehavior


class NiveauAlerte(Enum):
    """Niveaux d'alerte Sentinel (mapping vers ScoreSentinel.niveau)."""

    INFO = "info"
    AVERTISSEMENT = "avertissement"
    ALERTE = "alerte"
    CRITIQUE = "critique"

    @classmethod
    def depuis_niveau(cls, niveau: str) -> "NiveauAlerte":
        """Convertit un niveau de texte (FAIBLE/MODÉRÉ/ÉLEVÉ/CRITIQUE) en NiveauAlerte."""
        mapping = {
            "FAIBLE": cls.INFO,
            "MODÉRÉ": cls.AVERTISSEMENT,
            "ÉLEVÉ": cls.ALERTE,
            "CRITIQUE": cls.CRITIQUE,
        }
        return mapping.get(niveau.upper(), cls.INFO)


@dataclass
class Alerte:
    """Représentation d'une alerte générée par Sentinel."""

    niveau: NiveauAlerte
    titre: str
    description: str
    score: float
    signaux: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    ioc: Optional[Dict[str, Any]] = None  # Indicateur de Compromission

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'alerte en dictionnaire."""
        return {
            "niveau": self.niveau.value,
            "titre": self.titre,
            "description": self.description,
            "score": round(self.score, 4),
            "signaux": self.signaux,
            "timestamp": self.timestamp,
            "ioc": self.ioc,
        }


class SentinelResponse:
    """
    Couche 5 — Module de réponse et d'export.

    Génère des alertes actionnables à partir du score Sentinel (Couche 4)
    et des signaux comportementaux (Couche 3).

    Usage :
        responder = SentinelResponse()
        alertes = responder.generer_alertes(score, signaux)
        rapport = responder.rapport_markdown(alertes)
    """

    VERSION_SPEC: str = "phi-sentinel/1.0"

    def generer_alertes(
        self,
        score: ScoreSentinel,
        signaux: Optional[List[SignalComportemental]] = None,
        contexte: Optional[Dict[str, Any]] = None,
    ) -> List[Alerte]:
        """
        Génère la liste d'alertes depuis le score et les signaux.

        Args:
            score    : ScoreSentinel (Couche 4).
            signaux  : Signaux comportementaux (Couche 3). Peut être None.
            contexte : Métadonnées supplémentaires (SHA commit, hostname, etc.).

        Returns:
            Liste d'Alerte classée par sévérité décroissante.
        """
        signaux = signaux or []
        contexte = contexte or {}
        alertes: List[Alerte] = []
        niveau_alerte = NiveauAlerte.depuis_niveau(score.niveau)

        # Alerte principale sur le score global
        if score.score_final >= 0.20:
            ioc_principal = self._construire_ioc(
                pattern="score_global",
                valeur=str(round(score.score_final, 3)),
                confiance=score.score_final,
                contexte=contexte,
            )
            alertes.append(
                Alerte(
                    niveau=niveau_alerte,
                    titre=f"Menace détectée — Score {score.score_final * 100:.1f}%",
                    description=self._description_score(score),
                    score=score.score_final,
                    signaux=score.facteurs,
                    ioc=ioc_principal,
                )
            )

        # Alertes individuelles par signal comportemental critique
        for signal in signaux:
            if signal.confiance >= 0.60:
                niveau_signal = (
                    NiveauAlerte.CRITIQUE
                    if signal.confiance >= 0.85
                    else NiveauAlerte.ALERTE
                )
                ioc_signal = self._construire_ioc(
                    pattern=signal.type.value,
                    valeur=signal.mitre_technique,
                    confiance=signal.confiance,
                    contexte=contexte,
                )
                alertes.append(
                    Alerte(
                        niveau=niveau_signal,
                        titre=f"Comportement suspect: {signal.type.value.upper()}",
                        description=signal.description,
                        score=signal.confiance,
                        signaux=signal.traces_source,
                        ioc=ioc_signal,
                    )
                )

        # Trier par score décroissant
        alertes.sort(key=lambda a: a.score, reverse=True)
        return alertes

    def _description_score(self, score: ScoreSentinel) -> str:
        """Construit une description textuelle du score global."""
        parties = [
            f"Score de menace : {score.score_final * 100:.1f}% ({score.niveau}).",
            f"Contribution OS : {score.score_os * 100:.1f}%",
            f"Commit : {score.score_commit * 100:.1f}%",
            f"Télémétrie : {score.score_telemetrie * 100:.1f}%.",
        ]
        if score.facteurs:
            parties.append("Facteurs : " + "; ".join(score.facteurs[:3]))
        return " ".join(parties)

    def _construire_ioc(
        self,
        pattern: str,
        valeur: str,
        confiance: float,
        contexte: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Construit un Indicateur de Compromission au format STIX-like simplifié.

        Ce format peut être partagé avec la communauté OSS pour alimenter
        des bases de données de threat intelligence.
        """
        return {
            "type": "indicator",
            "spec_version": self.VERSION_SPEC,
            "id": f"indicator--phi-{hash(pattern + valeur) % 100000:05d}",
            "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pattern_type": "phi-sentinel",
            "pattern": f"[{pattern}:value = '{valeur}']",
            "confidence": round(confiance, 3),
            "mitre_technique": valeur if valeur.startswith("T") else "",
            "contexte": {k: str(v)[:64] for k, v in list(contexte.items())[:5]},
        }

    def exporter_ioc_json(
        self,
        alertes: List[Alerte],
        chemin: Optional[str] = None,
    ) -> str:
        """
        Exporte les IoC de toutes les alertes en JSON (STIX-like).

        Args:
            alertes : Liste d'alertes Sentinel.
            chemin  : Chemin de fichier de sortie. Si None, retourne le JSON.

        Returns:
            Contenu JSON sérialisé.
        """
        bundle = {
            "type": "bundle",
            "spec_version": self.VERSION_SPEC,
            "id": f"bundle--phi-{int(time.time())}",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "objects": [a.ioc for a in alertes if a.ioc is not None],
        }
        contenu = json.dumps(bundle, ensure_ascii=False, indent=2)

        if chemin:
            dossier = os.path.dirname(chemin)
            if dossier:
                os.makedirs(dossier, exist_ok=True)
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(contenu)

        return contenu

    def rapport_console(self, alertes: List[Alerte]) -> str:
        """Génère le rapport ASCII de la Couche 5."""
        nb_critiques = sum(1 for a in alertes if a.niveau == NiveauAlerte.CRITIQUE)
        nb_alertes = sum(1 for a in alertes if a.niveau == NiveauAlerte.ALERTE)

        symboles = {
            NiveauAlerte.INFO: "ℹ️ ",
            NiveauAlerte.AVERTISSEMENT: "⚠️ ",
            NiveauAlerte.ALERTE: "🔴",
            NiveauAlerte.CRITIQUE: "🚨",
        }

        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║   PHI-SENTINEL — RÉPONSE & ALERTING              ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  Alertes totales  : {len(alertes)}",
            f"  Critiques        : {nb_critiques}",
            f"  Alertes élevées  : {nb_alertes}",
            "",
        ]

        if alertes:
            lignes.append("  Alertes actives :")
            for alerte in alertes[:10]:
                sym = symboles.get(alerte.niveau, "?")
                lignes.append(f"    {sym}  [{alerte.niveau.value.upper()}] {alerte.titre}")
                lignes.append(f"       {alerte.description[:80]}")
        else:
            lignes.append("  ✦  Aucune alerte active. Système en état nominal.")

        lignes += [
            "",
            "  ─────────────────────────────────────────────────",
            "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
        ]
        return "\n".join(lignes)

    def rapport_markdown(self, alertes: List[Alerte], titre: str = "Rapport Sentinel") -> str:
        """Génère un rapport Markdown (pour PR comments, GitHub Issues, etc.)."""
        lignes = [
            f"# 🛡 {titre}",
            "",
            f"**Date** : {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}",
            f"**Alertes** : {len(alertes)} ({sum(1 for a in alertes if a.niveau == NiveauAlerte.CRITIQUE)} critiques)",
            "",
            "## Alertes",
            "",
        ]

        if not alertes:
            lignes.append("✅ Aucune alerte — Système en état nominal.")
        else:
            emojis = {
                NiveauAlerte.INFO: "ℹ️",
                NiveauAlerte.AVERTISSEMENT: "⚠️",
                NiveauAlerte.ALERTE: "🔴",
                NiveauAlerte.CRITIQUE: "🚨",
            }
            for alerte in alertes:
                em = emojis.get(alerte.niveau, "❓")
                lignes += [
                    f"### {em} {alerte.titre}",
                    "",
                    f"**Niveau** : `{alerte.niveau.value.upper()}`  "
                    f"**Score** : `{alerte.score * 100:.1f}%`",
                    "",
                    alerte.description,
                    "",
                ]
                if alerte.signaux:
                    lignes.append("**Signaux** :")
                    for s in alerte.signaux[:3]:
                        lignes.append(f"- {s}")
                    lignes.append("")

        lignes += [
            "---",
            f"*Genere par phi-complexity/sentinel v{self.VERSION_SPEC}*",
        ]
        return "\n".join(lignes)

    def politique_de_reponse(
        self,
        alertes: List[Alerte],
        politique: Optional[Dict[NiveauAlerte, str]] = None,
    ) -> Dict[str, Any]:
        """
        Applique la politique de réponse aux alertes et retourne les actions recommandées.

        La politique par défaut :
            INFO         → Logger uniquement
            AVERTISSEMENT → Notifier l'équipe
            ALERTE        → Bloquer la PR / Ouvrir un ticket
            CRITIQUE      → Bloquer + Escalader + Isoler

        Args:
            alertes  : Liste d'alertes Sentinel.
            politique: Override de la politique par défaut.

        Returns:
            Dict avec les actions recommandées par niveau.
        """
        politique_defaut: Dict[NiveauAlerte, str] = {
            NiveauAlerte.INFO: "LOG_ONLY",
            NiveauAlerte.AVERTISSEMENT: "NOTIFY_TEAM",
            NiveauAlerte.ALERTE: "BLOCK_PR|OPEN_TICKET",
            NiveauAlerte.CRITIQUE: "BLOCK_ALL|ESCALATE|ISOLATE",
        }
        pol = politique or politique_defaut

        actions_requises: Dict[str, Any] = {
            "bloquer_pr": False,
            "escalader": False,
            "isoler": False,
            "notifier": False,
            "actions_par_alerte": [],
        }

        for alerte in alertes:
            action = pol.get(alerte.niveau, "LOG_ONLY")
            actions_requises["actions_par_alerte"].append(
                {"titre": alerte.titre, "action": action}
            )
            if "BLOCK" in action:
                actions_requises["bloquer_pr"] = True
            if "ESCALATE" in action:
                actions_requises["escalader"] = True
            if "ISOLATE" in action:
                actions_requises["isoler"] = True
            if "NOTIFY" in action or "ESCALATE" in action:
                actions_requises["notifier"] = True

        return actions_requises
