"""
phi_complexity/sentinel/behavior.py — Couche 3 : Patterns Comportementaux

Extrait des signaux comportementaux de haut niveau depuis les traces normalisées
(Couche 2) pour détecter les techniques d'attaque connues.

Patterns détectés (inspirés du framework MITRE ATT&CK) :
    - PERSISTANCE    : Tentative d'ancrage dans le système (cron, startup, etc.)
    - ELEVATION      : Escalade de privilèges (setuid, chmod +s, sudo abuse)
    - EXFILTRATION   : Transfert anormal de données vers l'extérieur
    - CHIFFREMENT    : Modification massive de fichiers (ransomware pattern)
    - C2             : Communication avec potentiel centre de commande
    - RECONNAISSANCE : Scans réseau, discovery system
    - MOUVEMENT_LAT  : Connexions SSH/SMB internes suspectes
    - DEFENCE_EVASION: Techniques anti-détection (base64, obfuscation)

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from .telemetry import CriticiteTelemetrie, TraceNormalisee


class TypeBehavior(Enum):
    """Types de comportements malveillants détectables."""

    PERSISTANCE = "persistance"
    ELEVATION = "elevation"
    EXFILTRATION = "exfiltration"
    CHIFFREMENT = "chiffrement"
    C2 = "c2"
    RECONNAISSANCE = "reconnaissance"
    MOUVEMENT_LAT = "mouvement_lateral"
    DEFENCE_EVASION = "defence_evasion"
    INJECTION = "injection"
    ACCES_CREDENTIAL = "acces_credential"


@dataclass
class SignalComportemental:
    """
    Signal comportemental extrait de l'analyse des traces.

    Représente un pattern d'attaque potentiel avec son niveau de confiance.
    """

    type: TypeBehavior
    confiance: float          # [0.0, 1.0] — probabilité que ce signal soit réel
    description: str
    traces_source: List[str]  # Sources (descriptions) des traces ayant déclenché ce signal
    timestamp: float = field(default_factory=time.time)
    mitre_technique: str = ""  # Identifiant MITRE ATT&CK (ex: "T1059.001")

    def to_dict(self) -> Dict[str, object]:
        """Sérialise le signal en dictionnaire."""
        return {
            "type": self.type.value,
            "confiance": round(self.confiance, 3),
            "description": self.description,
            "traces_source": self.traces_source,
            "timestamp": self.timestamp,
            "mitre_technique": self.mitre_technique,
        }


# ──────────────────────────────────────────────
# RÈGLES DE DÉTECTION
# ──────────────────────────────────────────────

# Correspondance tag → (TypeBehavior, confiance, description, mitre)
_REGLES_TAGS: List[tuple] = [
    # Tag, TypeBehavior, confiance_base, description, mitre
    ("setuid_suspect", TypeBehavior.ELEVATION, 0.75,
     "Tentative d'escalade via setuid (chmod +s détecté)", "T1548.001"),
    ("permissions_larges", TypeBehavior.ELEVATION, 0.50,
     "Permissions larges appliquées (chmod 777)", "T1548"),
    ("encodage_base64", TypeBehavior.DEFENCE_EVASION, 0.65,
     "Encodage base64 détecté dans la ligne de commande", "T1027"),
    ("pipe_curl_bash", TypeBehavior.PERSISTANCE, 0.85,
     "Exécution directe depuis URL (curl | bash)", "T1059.004"),
    ("pipe_wget_bash", TypeBehavior.PERSISTANCE, 0.85,
     "Exécution directe depuis URL (wget | bash)", "T1059.004"),
    ("execution_tmp", TypeBehavior.DEFENCE_EVASION, 0.60,
     "Exécution depuis répertoire temporaire (/tmp, /dev/shm)", "T1036.005"),
    ("destruction_systeme", TypeBehavior.CHIFFREMENT, 0.95,
     "Commande destructrice détectée (rm -rf /)", "T1485"),
    ("lecture_raw_device", TypeBehavior.EXFILTRATION, 0.70,
     "Lecture directe d'un périphérique brut (dd if=/dev/)", "T1006"),
    ("tcp_via_bash", TypeBehavior.C2, 0.80,
     "Connexion TCP directe via Bash (/dev/tcp/)", "T1071.001"),
    ("udp_via_bash", TypeBehavior.C2, 0.80,
     "Connexion UDP directe via Bash (/dev/udp/)", "T1071.001"),
    ("connexion_tor", TypeBehavior.C2, 0.75,
     "Connexion réseau vers le réseau Tor (port 9001/9050)", "T1090.003"),
    ("port_suspect", TypeBehavior.C2, 0.55,
     "Connexion réseau sur port associé à du C2 connu", "T1071"),
    ("processus_suspect", TypeBehavior.RECONNAISSANCE, 0.65,
     "Processus offensif ou de reconnaissance détecté", "T1046"),
    ("port_ephemere_en_ecoute", TypeBehavior.C2, 0.45,
     "Port éphémère en écoute (bind shell potentiel)", "T1571"),
]


class BehaviorAnalyzer:
    """
    Couche 3 — Analyseur de comportements.

    Prend en entrée des traces normalisées (Couche 2) et produit
    des signaux comportementaux de haut niveau.

    Usage :
        analyzer = BehaviorAnalyzer()
        signaux = analyzer.analyser(traces)
    """

    def analyser(self, traces: List[TraceNormalisee]) -> List[SignalComportemental]:
        """
        Analyse les traces et retourne les signaux comportementaux détectés.

        Args:
            traces: Traces normalisées depuis TelemetryNormalizer.

        Returns:
            Liste de SignalComportemental (dédupliqués par type).
        """
        if not traces:
            return []

        # Collecte des contributions par type de behavior
        contributions: Dict[TypeBehavior, List[tuple]] = {}

        for trace in traces:
            for tag in trace.tags:
                for regle_tag, behavior_type, confiance, desc, mitre in _REGLES_TAGS:
                    if regle_tag == tag:
                        if behavior_type not in contributions:
                            contributions[behavior_type] = []
                        contributions[behavior_type].append(
                            (confiance, desc, trace.evenement.description, mitre)
                        )

        # Consolider les contributions par type en un seul signal
        signaux: List[SignalComportemental] = []
        for behavior_type, contrib_list in contributions.items():
            # Confiance consolidée : 1 - ∏(1 - p_i) — règle de fusion bayésienne
            confiance_consolidee = 1.0
            for conf, _, _, _ in contrib_list:
                confiance_consolidee *= 1.0 - conf
            confiance_finale = 1.0 - confiance_consolidee
            confiance_finale = min(1.0, confiance_finale)

            # Description et source depuis la contribution la plus confiante
            contrib_principale = max(contrib_list, key=lambda x: x[0])
            description = contrib_principale[1]
            mitre = contrib_principale[3]
            sources = list({c[2] for c in contrib_list})

            signaux.append(
                SignalComportemental(
                    type=behavior_type,
                    confiance=confiance_finale,
                    description=description,
                    traces_source=sources[:5],  # Limite à 5 sources pour la lisibilité
                    mitre_technique=mitre,
                )
            )

        # Trier par confiance décroissante
        signaux.sort(key=lambda s: s.confiance, reverse=True)
        return signaux

    def signaux_critiques(
        self,
        signaux: List[SignalComportemental],
        seuil_confiance: float = 0.70,
    ) -> List[SignalComportemental]:
        """Retourne uniquement les signaux au-delà du seuil de confiance."""
        return [s for s in signaux if s.confiance >= seuil_confiance]

    def score_global(self, signaux: List[SignalComportemental]) -> float:
        """
        Calcule un score global de menace depuis les signaux.

        Utilise la même règle de fusion bayésienne :
        score = 1 - ∏(1 - confiance_i)
        """
        if not signaux:
            return 0.0
        produit = 1.0
        for signal in signaux:
            produit *= 1.0 - signal.confiance
        return min(1.0, 1.0 - produit)

    def rapport_comportements(self, signaux: List[SignalComportemental]) -> str:
        """Génère un rapport ASCII des comportements détectés."""
        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║   PHI-SENTINEL — ANALYSE COMPORTEMENTALE         ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  Signaux détectés : {len(signaux)}",
            f"  Score global     : {self.score_global(signaux) * 100:.1f}%",
            "",
        ]

        if signaux:
            lignes.append("  Signaux (triés par confiance décroissante) :")
            for signal in signaux:
                conf_pct = signal.confiance * 100
                mitre_str = f" [{signal.mitre_technique}]" if signal.mitre_technique else ""
                lignes.append(
                    f"    ◈  {signal.type.value.upper():20s}"
                    f"  {conf_pct:5.1f}%{mitre_str}"
                )
                lignes.append(f"       {signal.description}")
        else:
            lignes.append("  ✦  Aucun signal comportemental suspect détecté.")

        lignes += [
            "",
            "  ─────────────────────────────────────────────────",
            "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
        ]
        return "\n".join(lignes)

    def filtrer_par_criticite(
        self, traces: List[TraceNormalisee]
    ) -> List[TraceNormalisee]:
        """Filtre les traces de criticité SUSPECT ou CRITIQUE uniquement."""
        return [
            t
            for t in traces
            if t.criticite in (CriticiteTelemetrie.SUSPECT, CriticiteTelemetrie.CRITIQUE)
        ]
