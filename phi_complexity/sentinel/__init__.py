"""
phi_complexity/sentinel/__init__.py — Module Sentinel (Phases C & D)

Architecture en 5 couches pour l'analyse comportementale des systèmes,
orientée détection de menaces open source.

Couches :
    1. host      — Collecte des événements système (processus, fichiers, réseau)
    2. telemetry — Normalisation des traces brutes
    3. behavior  — Extraction de patterns comportementaux
    4. bayesian  — Corrélation bayésienne multi-signaux
    5. response  — Alerting, rapport et export OSS

Philosophie : zéro dépendance externe, stdlib pure, zéro identification.
Ancré dans le Morphic Phi Framework — φ-Meta 2026
"""

from .host import HostCollector, HostEvent, EventType
from .telemetry import TelemetryNormalizer, TraceNormalisee
from .behavior import BehaviorAnalyzer, SignalComportemental, TypeBehavior
from .bayesian import BayesianCorrelator, ScoreSentinel
from .response import SentinelResponse, NiveauAlerte

__all__ = [
    # Couche 1
    "HostCollector",
    "HostEvent",
    "EventType",
    # Couche 2
    "TelemetryNormalizer",
    "TraceNormalisee",
    # Couche 3
    "BehaviorAnalyzer",
    "SignalComportemental",
    "TypeBehavior",
    # Couche 4
    "BayesianCorrelator",
    "ScoreSentinel",
    # Couche 5
    "SentinelResponse",
    "NiveauAlerte",
]
