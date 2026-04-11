"""
phi_complexity/sentinel/host.py — Couche 1 : Collecte des Événements Système

Collecte les événements de bas niveau depuis le système d'exploitation :
- Processus en cours d'exécution (PID, nom, ligne de commande)
- Connexions réseau actives (ports, adresses, états)
- Accès aux fichiers récents (si disponibles via /proc)

Fonctionnement multi-plateforme avec dégradation gracieuse :
- Linux  : lecture directe de /proc (précis et sans privilèges root)
- Autres : appel aux commandes système standard (ps, netstat)

Zéro dépendance externe. Stdlib pure. Aucun identifiant utilisateur collecté.
Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class EventType(Enum):
    """Types d'événements système collectés par le HostCollector."""

    PROCESSUS = "processus"
    RESEAU = "reseau"
    FICHIER = "fichier"
    INCONNU = "inconnu"


@dataclass
class HostEvent:
    """
    Représentation d'un événement système brut.

    Attributs :
        type        : Catégorie de l'événement (PROCESSUS, RESEAU, FICHIER).
        timestamp   : Epoch UNIX de la collecte (secondes).
        source      : Origine de l'événement (ex: "pid:1234", "port:443").
        description : Description courte lisible par un humain.
        metadata    : Données brutes supplémentaires (dépend du type).
    """

    type: EventType
    timestamp: float
    source: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────
# COLLECTE LINUX (/proc)
# ──────────────────────────────────────────────


def _lire_proc_status(pid: int) -> dict[str, str]:
    """
    Lit /proc/{pid}/status et retourne un dict des champs clés.
    Retourne un dict vide si le fichier n'est pas accessible.
    """
    chemin = f"/proc/{pid}/status"
    result: dict[str, str] = {}
    try:
        with open(chemin, "r", encoding="utf-8", errors="replace") as f:
            for ligne in f:
                if ":" in ligne:
                    cle, _, val = ligne.partition(":")
                    result[cle.strip()] = val.strip()
    except OSError:
        pass
    return result


def _lire_proc_cmdline(pid: int) -> str:
    """Lit /proc/{pid}/cmdline et retourne la ligne de commande nettoyée."""
    chemin = f"/proc/{pid}/cmdline"
    try:
        with open(chemin, "rb") as f:
            contenu = f.read()
        return contenu.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()
    except OSError:
        return ""


def _collecter_processus_linux() -> List[HostEvent]:
    """Collecte les processus actifs via /proc sur Linux."""
    events: List[HostEvent] = []
    ts = time.time()
    try:
        pids = [int(nom) for nom in os.listdir("/proc") if nom.isdigit()]
    except OSError:
        return events

    for pid in pids:
        status = _lire_proc_status(pid)
        if not status:
            continue
        nom = status.get("Name", "inconnu")
        cmdline = _lire_proc_cmdline(pid)
        events.append(
            HostEvent(
                type=EventType.PROCESSUS,
                timestamp=ts,
                source=f"pid:{pid}",
                description=f"Processus: {nom}",
                metadata={
                    "pid": pid,
                    "nom": nom,
                    "cmdline": cmdline[
                        :256
                    ],  # Tronqué pour éviter les données trop longues
                    "vmrss_kb": (
                        status.get("VmRSS", "0").split()[0]
                        if "VmRSS" in status
                        else "0"
                    ),
                },
            )
        )
    return events


def _collecter_reseau_linux() -> List[HostEvent]:
    """Collecte les connexions réseau via /proc/net/tcp et /proc/net/tcp6."""
    events: List[HostEvent] = []
    ts = time.time()

    for proto_fichier in ("/proc/net/tcp", "/proc/net/tcp6", "/proc/net/udp"):
        try:
            with open(proto_fichier, "r", encoding="utf-8", errors="replace") as f:
                lignes = f.readlines()[1:]  # Ignorer l'en-tête
        except OSError:
            continue

        proto = os.path.basename(proto_fichier)
        for ligne in lignes:
            parties = ligne.split()
            if len(parties) < 4:
                continue
            local_addr = parties[1]
            remote_addr = parties[2]
            etat_hex = parties[3]
            # Décoder le port depuis l'adresse hexadécimale "00000000:1F90"
            try:
                port_local = int(local_addr.split(":")[1], 16)
                port_remote = int(remote_addr.split(":")[1], 16)
            except (IndexError, ValueError):
                continue
            # État TCP: 01=ESTABLISHED, 0A=LISTEN
            etats_tcp = {
                "01": "ESTABLISHED",
                "02": "SYN_SENT",
                "03": "SYN_RECV",
                "04": "FIN_WAIT1",
                "05": "FIN_WAIT2",
                "06": "TIME_WAIT",
                "07": "CLOSE",
                "08": "CLOSE_WAIT",
                "09": "LAST_ACK",
                "0A": "LISTEN",
                "0B": "CLOSING",
            }
            etat = etats_tcp.get(etat_hex.upper(), etat_hex)
            events.append(
                HostEvent(
                    type=EventType.RESEAU,
                    timestamp=ts,
                    source=f"port:{port_local}",
                    description=f"{proto} port {port_local} → {port_remote} [{etat}]",
                    metadata={
                        "protocole": proto,
                        "port_local": port_local,
                        "port_remote": port_remote,
                        "etat": etat,
                    },
                )
            )
    return events


# ──────────────────────────────────────────────
# FALLBACK MULTI-PLATEFORME (subprocess)
# ──────────────────────────────────────────────


def _collecter_processus_subprocess() -> List[HostEvent]:
    """Collecte les processus via `ps` (fallback non-Linux)."""
    events: List[HostEvent] = []
    ts = time.time()
    try:
        sortie = subprocess.run(
            ["ps", "axo", "pid,comm,args"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for ligne in sortie.stdout.splitlines()[1:]:
            parties = ligne.split(None, 2)
            if len(parties) < 2:
                continue
            pid_str, nom = parties[0], parties[1]
            cmdline = parties[2] if len(parties) > 2 else ""
            try:
                pid = int(pid_str)
            except ValueError:
                continue
            events.append(
                HostEvent(
                    type=EventType.PROCESSUS,
                    timestamp=ts,
                    source=f"pid:{pid}",
                    description=f"Processus: {nom}",
                    metadata={"pid": pid, "nom": nom, "cmdline": cmdline[:256]},
                )
            )
    except (OSError, subprocess.TimeoutExpired):
        pass
    return events


def _collecter_reseau_subprocess() -> List[HostEvent]:
    """Collecte les connexions réseau via `ss` ou `netstat` (fallback)."""
    events: List[HostEvent] = []
    ts = time.time()
    # Essai avec ss (plus moderne), puis netstat
    for cmd in [["ss", "-tnp"], ["netstat", "-tn"]]:
        try:
            sortie = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            for ligne in sortie.stdout.splitlines()[1:]:
                parties = ligne.split()
                if len(parties) < 4:
                    continue
                events.append(
                    HostEvent(
                        type=EventType.RESEAU,
                        timestamp=ts,
                        source="reseau",
                        description=f"Connexion: {' '.join(parties[:5])}",
                        metadata={"raw": ligne[:128]},
                    )
                )
            break  # Si ss fonctionne, pas besoin de netstat
        except (OSError, subprocess.TimeoutExpired):
            continue
    return events


# ──────────────────────────────────────────────
# COLLECTEUR PRINCIPAL
# ──────────────────────────────────────────────


class HostCollector:
    """
    Couche 1 — Collecteur d'événements système.

    Sélectionne automatiquement la méthode de collecte optimale selon la plateforme.
    Toutes les méthodes sont non-destructives et ne nécessitent pas de privilèges root.

    Usage :
        collector = HostCollector()
        events = collector.collecter_tout()
    """

    def __init__(self, utiliser_proc: Optional[bool] = None) -> None:
        """
        Args:
            utiliser_proc: Force l'utilisation de /proc (None = auto-détection).
        """
        if utiliser_proc is None:
            self._utiliser_proc = os.path.exists("/proc/version")
        else:
            self._utiliser_proc = utiliser_proc

    def collecter_processus(self) -> List[HostEvent]:
        """Collecte la liste des processus actifs."""
        if self._utiliser_proc:
            return _collecter_processus_linux()
        return _collecter_processus_subprocess()

    def collecter_reseau(self) -> List[HostEvent]:
        """Collecte les connexions réseau actives."""
        if self._utiliser_proc:
            return _collecter_reseau_linux()
        return _collecter_reseau_subprocess()

    def collecter_tout(self) -> List[HostEvent]:
        """Collecte l'ensemble des événements système disponibles."""
        events: List[HostEvent] = []
        events.extend(self.collecter_processus())
        events.extend(self.collecter_reseau())
        return events

    def resume(self) -> dict[str, Any]:
        """Retourne un résumé compact de la collecte (pour logs/rapports)."""
        events = self.collecter_tout()
        nb_proc = sum(1 for e in events if e.type == EventType.PROCESSUS)
        nb_reseau = sum(1 for e in events if e.type == EventType.RESEAU)
        return {
            "total": len(events),
            "processus": nb_proc,
            "reseau": nb_reseau,
            "timestamp": time.time(),
            "methode": "proc" if self._utiliser_proc else "subprocess",
        }
