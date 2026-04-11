"""
phi_complexity/sentinel/telemetry.py — Couche 2 : Normalisation des Traces

Normalise les événements bruts collectés par HostCollector (Couche 1)
en structures typées et enrichies, prêtes pour l'analyse comportementale.

Transformations appliquées :
    - Déduplication des événements similaires
    - Classification par niveau de criticité
    - Enrichissement contextuel (port bien-connu, processus suspect, etc.)
    - Agrégation par source (groupe les connexions par processus)

Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .host import HostEvent, EventType


class CriticiteTelemetrie(Enum):
    """Niveau de criticité d'une trace normalisée."""

    INFO = "info"
    ATTENTION = "attention"
    SUSPECT = "suspect"
    CRITIQUE = "critique"


# Ports bien connus à surveiller (ports privilégiés ou sensibles)
_PORTS_SUSPECTS: frozenset[int] = frozenset(
    {
        22,  # SSH
        23,  # Telnet (non chiffré)
        25,  # SMTP (potentielle exfiltration mail)
        53,  # DNS (canal caché)
        4444,  # Metasploit par défaut
        4445,  # Variante Metasploit
        5554,  # Sasser worm
        6666,  # IRC (souvent C2)
        6667,  # IRC
        7777,  # Variante backdoor
        8080,  # Proxy HTTP alternatif
        8888,  # Proxy alternatif
        9001,  # Tor default
        9050,  # Tor SOCKS proxy
        9999,  # Port backdoor commun
        31337,  # Elite / backdoor
        65535,  # Port max (inhabituel)
    }
)

# Noms de processus typiquement associés à des activités suspectes
_PROCESSUS_SUSPECTS: frozenset[str] = frozenset(
    {
        "nc",
        "ncat",
        "netcat",  # Outils réseau offensifs
        "nmap",  # Scan de réseau
        "tcpdump",
        "wireshark",  # Capture réseau (légitime mais à surveiller)
        "msfconsole",
        "msfvenom",  # Metasploit
        "hydra",
        "medusa",  # Brute force
        "sqlmap",  # SQL injection
        "john",
        "hashcat",  # Cracking de mots de passe
        "aircrack-ng",  # Attaque WiFi
        "mimikatz",  # Extraction de credentials
        "cobalt",  # Cobalt Strike
        "beacon",  # Cobalt Strike beacon
        "powershell",  # Souvent utilisé dans les attaques Windows
        "wscript",
        "cscript",  # Scripting Windows
        "regsvr32",
        "mshta",  # Living-off-the-land (LOTL)
        "certutil",  # LOTL (download/decode)
        "bitsadmin",  # LOTL (téléchargement)
    }
)


@dataclass
class TraceNormalisee:
    """
    Événement normalisé après traitement de la Couche 2.

    Contient l'événement brut d'origine plus les enrichissements contextuels.
    """

    evenement: HostEvent
    criticite: CriticiteTelemetrie
    tags: List[str] = field(default_factory=list)
    contexte: Dict[str, object] = field(default_factory=dict)
    timestamp_normalisation: float = field(default_factory=time.time)


class TelemetryNormalizer:
    """
    Couche 2 — Normalisateur de télémétrie.

    Prend en entrée une liste de HostEvent bruts et produit
    des TraceNormalisee enrichies et classifiées.

    Usage :
        normalizer = TelemetryNormalizer()
        traces = normalizer.normaliser(events)
    """

    def normaliser(self, events: List[HostEvent]) -> List[TraceNormalisee]:
        """
        Normalise et enrichit une liste d'événements bruts.

        Args:
            events: Liste de HostEvent depuis HostCollector.

        Returns:
            Liste de TraceNormalisee classifiées et enrichies.
        """
        traces: List[TraceNormalisee] = []
        for event in events:
            if event.type == EventType.PROCESSUS:
                traces.append(self._normaliser_processus(event))
            elif event.type == EventType.RESEAU:
                traces.append(self._normaliser_reseau(event))
            else:
                traces.append(
                    TraceNormalisee(
                        evenement=event,
                        criticite=CriticiteTelemetrie.INFO,
                        tags=["inconnu"],
                    )
                )
        return traces

    def _normaliser_processus(self, event: HostEvent) -> TraceNormalisee:
        """Normalise un événement de type PROCESSUS."""
        nom = str(event.metadata.get("nom", "")).lower()
        cmdline = str(event.metadata.get("cmdline", "")).lower()
        tags: List[str] = ["processus"]
        criticite = CriticiteTelemetrie.INFO

        # Détection de processus suspects
        if nom in _PROCESSUS_SUSPECTS:
            tags.append("processus_suspect")
            criticite = CriticiteTelemetrie.SUSPECT

        # Détection de patterns suspects dans la ligne de commande
        patterns_suspects = [
            ("base64", "encodage_base64"),
            ("chmod +s", "setuid_suspect"),
            ("chmod 777", "permissions_larges"),
            ("/tmp/", "execution_tmp"),
            ("rm -rf /", "destruction_systeme"),
            ("dd if=/dev/", "lecture_raw_device"),
            ("/dev/tcp/", "tcp_via_bash"),
            ("/dev/udp/", "udp_via_bash"),
        ]

        for pattern, tag in patterns_suspects:
            if pattern in cmdline:
                tags.append(tag)
                if criticite.value in ("info", "attention"):
                    criticite = CriticiteTelemetrie.SUSPECT

        # Détection de pipe vers shell (curl/wget + bash dans la même commande)
        contient_pipe_bash = (
            "| bash" in cmdline or "| sh" in cmdline or "|bash" in cmdline
        )
        if contient_pipe_bash:
            if "curl" in cmdline:
                tags.append("pipe_curl_bash")
                if criticite.value in ("info", "attention"):
                    criticite = CriticiteTelemetrie.SUSPECT
            if "wget" in cmdline:
                tags.append("pipe_wget_bash")
                if criticite.value in ("info", "attention"):
                    criticite = CriticiteTelemetrie.SUSPECT
            if not any(t in tags for t in ("pipe_curl_bash", "pipe_wget_bash")):
                tags.append("pipe_vers_bash")
                if criticite.value in ("info", "attention"):
                    criticite = CriticiteTelemetrie.SUSPECT

        # Exécution depuis répertoire temporaire
        if any(rep in cmdline for rep in ("/tmp/", "/dev/shm/", "/var/tmp/")):
            if "execution_tmp" not in tags:
                tags.append("execution_tmp")
            if criticite == CriticiteTelemetrie.INFO:
                criticite = CriticiteTelemetrie.ATTENTION

        contexte: Dict[str, object] = {
            "nom_processus": nom,
            "nb_tags_suspects": len([t for t in tags if t != "processus"]),
        }

        return TraceNormalisee(
            evenement=event,
            criticite=criticite,
            tags=tags,
            contexte=contexte,
        )

    def _normaliser_reseau(self, event: HostEvent) -> TraceNormalisee:
        """Normalise un événement de type RESEAU."""
        port_local = int(event.metadata.get("port_local", 0))
        port_remote = int(event.metadata.get("port_remote", 0))
        etat = str(event.metadata.get("etat", ""))
        tags: List[str] = ["reseau"]
        criticite = CriticiteTelemetrie.INFO

        # Ports suspects
        if port_local in _PORTS_SUSPECTS or port_remote in _PORTS_SUSPECTS:
            tags.append("port_suspect")
            criticite = CriticiteTelemetrie.SUSPECT

        # Connexions établies sur ports privilégiés élevés
        if etat == "ESTABLISHED":
            tags.append("connexion_etablie")

        # Ports d'écoute inhabituels (> 49152 = ports éphémères → suspect si LISTEN)
        if etat == "LISTEN" and port_local > 49152:
            tags.append("port_ephemere_en_ecoute")
            if criticite == CriticiteTelemetrie.INFO:
                criticite = CriticiteTelemetrie.ATTENTION

        # Connexion sortante vers port Tor
        if port_remote in (9001, 9050, 9150):
            tags.append("connexion_tor")
            criticite = CriticiteTelemetrie.SUSPECT

        contexte: Dict[str, object] = {
            "port_local": port_local,
            "port_remote": port_remote,
            "etat": etat,
        }

        return TraceNormalisee(
            evenement=event,
            criticite=criticite,
            tags=tags,
            contexte=contexte,
        )

    def filtrer_par_criticite(
        self,
        traces: List[TraceNormalisee],
        seuil: CriticiteTelemetrie = CriticiteTelemetrie.ATTENTION,
    ) -> List[TraceNormalisee]:
        """
        Filtre les traces au-delà d'un seuil de criticité.

        Ordre : INFO < ATTENTION < SUSPECT < CRITIQUE
        """
        ordre = [
            CriticiteTelemetrie.INFO,
            CriticiteTelemetrie.ATTENTION,
            CriticiteTelemetrie.SUSPECT,
            CriticiteTelemetrie.CRITIQUE,
        ]
        idx_seuil = ordre.index(seuil)
        return [t for t in traces if ordre.index(t.criticite) >= idx_seuil]

    def statistiques(self, traces: List[TraceNormalisee]) -> Dict[str, int]:
        """Retourne les statistiques de criticité pour un ensemble de traces."""
        stats: Dict[str, int] = {c.value: 0 for c in CriticiteTelemetrie}
        for trace in traces:
            stats[trace.criticite.value] += 1
        stats["total"] = len(traces)
        return stats

    def deduplication(
        self,
        traces: List[TraceNormalisee],
        fenetre_secondes: float = 60.0,
    ) -> List[TraceNormalisee]:
        """
        Supprime les doublons dans une fenêtre temporelle.

        Deux traces sont considérées identiques si elles ont la même source
        et les mêmes tags dans la fenêtre de temps donnée.
        """
        vues: Dict[str, float] = {}
        uniques: List[TraceNormalisee] = []

        for trace in traces:
            cle = f"{trace.evenement.source}:{'|'.join(sorted(trace.tags))}"
            derniere_vue = vues.get(cle)
            if derniere_vue is None or (
                trace.evenement.timestamp - derniere_vue > fenetre_secondes
            ):
                vues[cle] = trace.evenement.timestamp
                uniques.append(trace)

        return uniques

    def traces_suspectes(self, traces: List[TraceNormalisee]) -> List[TraceNormalisee]:
        """Raccourci : retourne uniquement les traces SUSPECT et CRITIQUE."""
        return self.filtrer_par_criticite(traces, CriticiteTelemetrie.SUSPECT)

    def rapport_telemetrie(self, traces: Optional[List[TraceNormalisee]] = None) -> str:
        """Génère un rapport ASCII de la télémétrie normalisée."""
        if traces is None:
            return "  ░  Aucune trace à afficher."

        stats = self.statistiques(traces)
        suspectes = self.traces_suspectes(traces)

        lignes = [
            "╔══════════════════════════════════════════════════╗",
            "║   PHI-SENTINEL — TÉLÉMÉTRIE NORMALISÉE           ║",
            "╚══════════════════════════════════════════════════╝",
            "",
            f"  Total traces     : {stats['total']}",
            f"  INFO             : {stats['info']}",
            f"  ATTENTION        : {stats['attention']}",
            f"  SUSPECT          : {stats['suspect']}",
            f"  CRITIQUE         : {stats['critique']}",
            "",
        ]

        if suspectes:
            lignes.append(f"  ⚠  TRACES SUSPECTES ({len(suspectes)}) :")
            for t in suspectes[:10]:  # Limite à 10 pour la lisibilité
                lignes.append(
                    f"    ◈  [{t.criticite.value.upper()}] {t.evenement.description}"
                )
                if t.tags:
                    lignes.append(f"       Tags: {', '.join(t.tags)}")
        else:
            lignes.append("  ✦  Aucune trace suspecte détectée.")

        lignes += [
            "",
            "  ─────────────────────────────────────────────────",
            "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
        ]
        return "\n".join(lignes)
