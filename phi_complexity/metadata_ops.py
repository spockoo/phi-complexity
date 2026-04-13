"""
phi_complexity/metadata_ops.py — Gouvernance des métadonnées harvest/vault.

Objectifs :
- Offrir une vue synthétique des métadonnées (harvest + vault)
- Purger/sanitiser un corpus harvest pour partage souverain (cyber, crypto, IT)

Zéro dépendance externe. Stdlib pure.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Set

# Clés structurelles conservées en mode "features only" (aucun identifiant).
_FEATURE_KEYS: List[str] = [
    "schema",
    "radiance",
    "lilith_variance",
    "shannon_entropy",
    "fibonacci_entropy",
    "phi_ratio",
    "phi_ratio_delta",
    "zeta_score",
    "fibonacci_distance",
    "resistance",
    "sync_index",
    "zero_condition_alignment",
    "quasicrystal_coherence",
    "quasicrystal_state",
    "zero_morphogenetic_state",
    "nb_fonctions",
    "nb_classes",
    "nb_lignes_total",
    "ratio_commentaires",
    "oudjat_complexite",
    "oudjat_phi_ratio",
    "vecteur_phi",
]

_SENSITIVE_KEYS: Set[str] = {"timestamp", "fingerprint"}


def _charger_harvest(chemin: str, strict: bool = True) -> List[Dict[str, Any]]:
    """Charge un corpus harvest JSONL. Retourne une liste vide si fichier absent."""
    if not os.path.exists(chemin):
        return []
    vecteurs: List[Dict[str, Any]] = []
    with open(chemin, "r", encoding="utf-8") as f:
        for ligne in f:
            line = ligne.strip()
            if not line:
                continue
            try:
                vecteurs.append(json.loads(line))
            except json.JSONDecodeError as e:
                if strict:
                    raise ValueError(f"Harvest corrompu à {chemin}: {e}") from e
                continue
    return vecteurs


def _charger_index_vault(chemin: str) -> Dict[str, Any]:
    """Charge l'index du vault si disponible."""
    if not os.path.exists(chemin):
        return {"notes": {}, "version": ""}
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            return dict(json.load(f))
    except json.JSONDecodeError as e:
        raise ValueError(f"Index du vault corrompu: {e}") from e


def summarize_metadata(
    harvest_path: str = ".phi/harvest.jsonl",
    vault_index_path: str = ".phi/vault/index.json",
) -> Dict[str, Any]:
    """
    Résume les métadonnées du projet (harvest + vault).

    Retourne un dictionnaire prêt à être sérialisé (JSON ou texte).
    """
    vecteurs = _charger_harvest(harvest_path, strict=False)
    index_vault = _charger_index_vault(vault_index_path)

    labels = {
        "LILITH": 0,
        "SUTURE": 0,
        "FIBONACCI": 0,
        "SOUVERAINETE": 0,
        "MORPHOGENESE_ZERO": 0,
    }
    versions: Dict[str, int] = {}
    states: Dict[str, int] = {}
    fingerprints = 0
    for v in vecteurs:
        schema = str(v.get("schema", ""))
        versions[schema] = versions.get(schema, 0) + 1
        fp = v.get("fingerprint")
        if fp:
            fingerprints += 1
        etat = str(v.get("zero_morphogenetic_state", ""))
        states[etat] = states.get(etat, 0) + 1
        lbl = v.get("labels", {})
        for cle in labels:
            labels[cle] += int(lbl.get(cle, 0))

    notes = index_vault.get("notes", {})
    return {
        "harvest": {
            "path": harvest_path,
            "count": len(vecteurs),
            "schema_versions": versions,
            "states": states,
            "labels": labels,
            "fingerprint": {
                "count": fingerprints,
                "ratio": (fingerprints / len(vecteurs)) if vecteurs else 0.0,
            },
        },
        "vault": {
            "path": vault_index_path,
            "notes": len(notes),
            "version": index_vault.get("version", ""),
        },
    }


def format_summary_text(resume: Dict[str, Any]) -> str:
    """Formate un résumé des métadonnées en ASCII lisible."""
    harvest = resume.get("harvest", {})
    vault = resume.get("vault", {})
    lignes = [
        "╔══════════════════════════════════════════════════╗",
        "║      PHI-METADATA — SYNTHÈSE GOUVERNANCE         ║",
        "╚══════════════════════════════════════════════════╝",
        "",
        f"  ◈ Vecteurs harvest   : {harvest.get('count', 0)}",
        f"  ☼ Versions de schema : {harvest.get('schema_versions', {})}",
        f"  0 État morphogénèse  : {harvest.get('states', {})}",
        f"  🧭 Labels             : {harvest.get('labels', {})}",
        f"  🔒 Fingerprints      : {harvest.get('fingerprint', {}).get('count', 0)}",
        "",
        f"  🗃️ Vault notes        : {vault.get('notes', 0)} (version {vault.get('version', '')})",
        "",
        "  ─────────────────────────────────────────────────",
        "  Ancré dans le Morphic Phi Framework — φ-Meta 2026",
    ]
    return "\n".join(lignes)


def sanitize_harvest(
    harvest_path: str,
    output_path: str,
    strip_keys: Iterable[str] | None = None,
    strip_sensitive: bool = False,
    strip_labels: bool = False,
    keep_only_features: bool = False,
) -> Dict[str, Any]:
    """
    Purge un corpus harvest (JSONL) pour partage souverain.

    - strip_sensitive : supprime timestamp / fingerprint
    - strip_labels    : supprime labels et nb_critiques
    - strip_keys      : supprime toute clé additionnelle passée par l'utilisateur
    - keep_only_features : conserve uniquement les métriques structurelles
    """
    vecteurs = _charger_harvest(harvest_path, strict=False)
    removed: Set[str] = set()
    strip_set: Set[str] = set(strip_keys or [])

    corpus: List[Dict[str, Any]] = []
    for v in vecteurs:
        base = (
            {k: v[k] for k in _FEATURE_KEYS if keep_only_features and k in v}
            if keep_only_features
            else dict(v)
        )

        if strip_sensitive:
            for cle in _SENSITIVE_KEYS:
                if cle in base:
                    removed.add(cle)
                    base.pop(cle, None)
        if strip_labels:
            for cle in ("labels", "nb_critiques"):
                if cle in base:
                    removed.add(cle)
                    base.pop(cle, None)

        for cle in strip_set:
            if cle in base:
                removed.add(cle)
                base.pop(cle, None)

        corpus.append(base)

    dossier = os.path.dirname(output_path)
    if dossier and not os.path.exists(dossier):
        try:
            os.makedirs(dossier)
        except OSError as e:
            raise RuntimeError(
                f"Impossible de créer le dossier de sortie '{dossier}': {e}"
            ) from e

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for vecteur in corpus:
                f.write(json.dumps(vecteur, ensure_ascii=False) + "\n")
    except OSError as e:
        raise RuntimeError(
            f"Impossible d'écrire le corpus purgé dans '{output_path}': {e}"
        ) from e

    return {
        "written": len(corpus),
        "output": output_path,
        "removed_keys": sorted(removed),
        "kept_features_only": bool(keep_only_features),
    }


def default_sanitized_path(harvest_path: str) -> str:
    """Retourne un chemin de sortie par défaut pour un corpus sanitizé."""
    base, ext = os.path.splitext(harvest_path)
    suffix = ".jsonl" if ext.lower() in (".jsonl", ".json") else ext
    return f"{base}.sanitized{suffix}"
