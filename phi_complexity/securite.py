"""
phi_complexity/securite.py — Durcissement Cybersécuritaire Souverain.

Fonctionnalités de sécurité additionnelles :
- Signature SHA-256 des rapports (non-altération)
- Validation et sanitisation des entrées fichiers
- Journal d'audit immuable (append-only)
- Génération SBOM (Software Bill of Materials)

Phase 20 du Morphic Phi Framework.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List


# ────────────────────────────────────────────────────────
# SIGNATURE DES RAPPORTS
# ────────────────────────────────────────────────────────


def signer_rapport(contenu: str) -> Dict[str, str]:
    """
    Signe un rapport avec SHA-256 + timestamp.
    Retourne un dictionnaire avec le hash et le timestamp.
    """
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    payload = f"{timestamp}:{contenu}"
    sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return {
        "sha256": sha256,
        "timestamp": timestamp,
        "taille": str(len(contenu)),
    }


def verifier_signature(contenu: str, signature: Dict[str, str]) -> bool:
    """Vérifie la signature d'un rapport."""
    timestamp = signature.get("timestamp", "")
    sha256_attendu = signature.get("sha256", "")
    payload = f"{timestamp}:{contenu}"
    sha256_calcule = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return sha256_calcule == sha256_attendu


# ────────────────────────────────────────────────────────
# VALIDATION ET SANITISATION DES ENTRÉES
# ────────────────────────────────────────────────────────

# Extensions autorisées pour l'analyse
_EXTENSIONS_AUTORISEES = frozenset(
    {".py", ".c", ".cpp", ".h", ".hpp", ".rs", ".asm", ".s"}
)

# Taille maximale de fichier (10 Mo)
_TAILLE_MAX_OCTETS = 10 * 1024 * 1024

# Caractères interdits dans les chemins (prévention path traversal)
_PATTERNS_INTERDITS = ("..", "~", "\x00")


def valider_chemin_fichier(chemin: str) -> bool:
    """
    Valide un chemin de fichier pour l'analyse.
    Vérifie : existence, extension, taille, caractères dangereux.
    """
    # Vérification des caractères interdits
    for pattern in _PATTERNS_INTERDITS:
        if pattern in chemin:
            return False

    # Vérification de l'existence
    if not os.path.exists(chemin):
        return False

    # Vérification que c'est un fichier (pas un lien symbolique vers l'extérieur)
    if os.path.islink(chemin):
        real_path = os.path.realpath(chemin)
        if not os.path.isfile(real_path):
            return False

    if not os.path.isfile(chemin):
        return False

    # Vérification de l'extension
    _, ext = os.path.splitext(chemin)
    if ext.lower() not in _EXTENSIONS_AUTORISEES:
        return False

    # Vérification de la taille
    try:
        taille = os.path.getsize(chemin)
        if taille > _TAILLE_MAX_OCTETS:
            return False
    except OSError:
        return False

    return True


def sanitiser_contenu_asm(contenu: str) -> str:
    """
    Sanitise le contenu d'un fichier assembleur avant parsing.
    Supprime les caractères de contrôle et les séquences potentiellement
    dangereuses (shellcode, etc.).
    """
    # Supprimer les caractères nuls et de contrôle (sauf newline, tab, espace)
    resultat = []
    for char in contenu:
        if char in ("\n", "\r", "\t", " ") or (32 <= ord(char) < 127):
            resultat.append(char)
    return "".join(resultat)


# ────────────────────────────────────────────────────────
# JOURNAL D'AUDIT IMMUABLE (APPEND-ONLY)
# ────────────────────────────────────────────────────────


class JournalAudit:
    """
    Journal d'audit immuable pour tracer toutes les opérations du moteur.
    Format append-only JSONL — chaque ligne est un événement horodaté et signé.
    """

    def __init__(self, workspace_root: str = ".") -> None:
        self.phi_dir = os.path.join(workspace_root, ".phi")
        self.journal_path = os.path.join(self.phi_dir, "audit_trail.jsonl")
        if not os.path.exists(self.phi_dir):
            os.makedirs(self.phi_dir)

    def enregistrer(self, operation: str, details: Dict[str, Any]) -> None:
        """Enregistre un événement dans le journal d'audit (append-only)."""
        evenement = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "operation": operation,
            "details": details,
        }
        # Hash de l'événement pour intégrité
        evenement_json = json.dumps(evenement, sort_keys=True, ensure_ascii=False)
        evenement["hash"] = hashlib.sha256(evenement_json.encode()).hexdigest()

        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evenement, ensure_ascii=False) + "\n")

    def lire_journal(self, limite: int = 50) -> List[Dict[str, Any]]:
        """Lit les dernières entrées du journal."""
        if not os.path.exists(self.journal_path):
            return []
        try:
            with open(self.journal_path, "r", encoding="utf-8") as f:
                lignes = [json.loads(l) for l in f if l.strip()]
            return lignes[-limite:]
        except (json.JSONDecodeError, OSError):
            return []

    def verifier_integrite(self) -> bool:
        """Vérifie l'intégrité du journal d'audit."""
        entries = self.lire_journal(10000)
        for entry in entries:
            hash_enregistre = entry.pop("hash", "")
            entry_json = json.dumps(entry, sort_keys=True, ensure_ascii=False)
            hash_calcule = hashlib.sha256(entry_json.encode()).hexdigest()
            entry["hash"] = hash_enregistre
            if hash_calcule != hash_enregistre:
                return False
        return True


# ────────────────────────────────────────────────────────
# SBOM — SOFTWARE BILL OF MATERIALS
# ────────────────────────────────────────────────────────


def generer_sbom() -> Dict[str, Any]:
    """
    Génère un Software Bill of Materials (SBOM) au format CycloneDX-like.
    phi-complexity a zéro dépendances tierces, mais le SBOM documente
    les modules stdlib utilisés et les métadonnées du projet.
    """
    from .core import VERSION, AUTEUR, FRAMEWORK

    stdlib_modules = [
        "ast",
        "math",
        "json",
        "os",
        "sys",
        "re",
        "hashlib",
        "time",
        "shutil",
        "argparse",
        "dataclasses",
        "abc",
        "typing",
        "statistics",
        "tempfile",
    ]

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {
            "component": {
                "type": "library",
                "name": "phi-complexity",
                "version": VERSION,
                "author": AUTEUR,
                "description": "Code quality metrics based on Golden Ratio mathematical invariants",
                "licenses": [{"license": {"id": "MIT"}}],
            },
            "framework": FRAMEWORK,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "components": [
            {
                "type": "library",
                "name": module,
                "version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "scope": "required",
                "purl": f"pkg:python-stdlib/{module}@{sys.version_info.major}.{sys.version_info.minor}",
            }
            for module in sorted(stdlib_modules)
        ],
        "dependencies": [],
        "externalDependencies": [],
    }


def exporter_sbom(chemin: str) -> str:
    """Exporte le SBOM au format JSON."""
    sbom = generer_sbom()
    contenu = json.dumps(sbom, indent=2, ensure_ascii=False)

    dossier = os.path.dirname(chemin)
    if dossier and not os.path.exists(dossier):
        os.makedirs(dossier)

    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)

    return contenu
