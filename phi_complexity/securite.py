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
from typing import Any, Dict, List, Optional, Sequence

from .core import PHI

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
_PATTERNS_INTERDITS = ("..", "\x00")


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
                lignes = [json.loads(line) for line in f if line.strip()]
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


# Garde un journal JSONL compact tout en conservant le contexte utile.
_CAPTURE_MAX_CHARS = 4000
# Fibonacci(6) : au-delà, le bruit marginal apporte peu d'information.
_STDERR_LINE_SATURATION = 8
# φ + 3 ≈ 4.618 équilibre erreurs, outils détectés et bruit stderr.
_OUTPUT_NOISE_NORMALIZER = 3.0 + PHI
_CONSENSUS_WEIGHT_RAW = {
    "phidelia_signal": PHI,
    "lilith_pressure": 1.0,
    "output_noise": 1.0 / PHI,
    "blocking_pressure": 1.0 / (PHI**2),
}
_CONSENSUS_WEIGHT_SUM = sum(_CONSENSUS_WEIGHT_RAW.values())
_CONSENSUS_WEIGHTS = {
    cle: valeur / _CONSENSUS_WEIGHT_SUM for cle, valeur in _CONSENSUS_WEIGHT_RAW.items()
}
_ACTIONS_CONSENSUS = (
    (
        "black",
        "Appliquer Black sur les fichiers signalés puis relancer `black --check .`.",
    ),
    ("ruff", "Exécuter `ruff check .` puis corriger les diagnostics remontés."),
    (
        "mypy",
        "Exécuter `mypy phi_complexity --ignore-missing-imports` et corriger le typage.",
    ),
    (
        "pytest",
        "Relancer `pytest --cov=phi_complexity --cov-fail-under=89` et compléter les cas manquants.",
    ),
    (
        "coverage",
        "Examiner le rapport de couverture et renforcer les branches sous le seuil de 89%.",
    ),
    (
        "pip install",
        "Rejouer l'installation locale des dépendances avant de relancer la CI.",
    ),
)


def _normaliser_sortie_capturee(valeur: Any) -> str:
    if valeur is None:
        return ""
    if isinstance(valeur, str):
        texte = valeur
    elif isinstance(valeur, Sequence) and not isinstance(
        valeur, (str, bytes, bytearray)
    ):
        texte = "\n".join(str(item) for item in valeur)
    else:
        texte = str(valeur)
    return texte.strip()[:_CAPTURE_MAX_CHARS]


def _actions_depuis_sorties(texte: str) -> List[str]:
    texte_normalise = texte.lower()
    actions: List[str] = []
    seen = set()
    for motif, action in _ACTIONS_CONSENSUS:
        if motif in texte_normalise and action not in seen:
            actions.append(action)
            seen.add(action)
    return actions


def resoudre_conflit_par_consensus(
    invariants: Optional[Dict[str, Any]] = None,
    sorties: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calcule un consensus de résolution à partir des invariants Lilith/Phidélia
    et des sorties capturées en CI ou en audit.
    """
    invariants = dict(invariants or {})
    sorties = dict(sorties or {})

    radiance = float(invariants.get("radiance", invariants.get("security_score", 0.0)))
    radiance = max(0.0, min(100.0, radiance))
    lilith_variance = max(0.0, float(invariants.get("lilith_variance", 0.0)))
    blocking_findings = max(0, int(invariants.get("blocking_findings", 0)))

    stdout = _normaliser_sortie_capturee(sorties.get("stdout", ""))
    stderr = _normaliser_sortie_capturee(sorties.get("stderr", ""))
    errors_raw = sorties.get("errors", [])
    if isinstance(errors_raw, Sequence) and not isinstance(errors_raw, (str, bytes)):
        errors = [str(item) for item in errors_raw]
    elif errors_raw:
        errors = [str(errors_raw)]
    else:
        errors = []

    erreurs_capturees = _normaliser_sortie_capturee(errors)
    capture = "\n".join(part for part in (stdout, stderr, erreurs_capturees) if part)
    actions = _actions_depuis_sorties(capture)

    stderr_lines = len(stderr.splitlines()) if stderr else 0
    erreurs_count = len(errors) + capture.lower().count("error:")
    stderr_contribution = min(stderr_lines, _STDERR_LINE_SATURATION) / float(
        _STDERR_LINE_SATURATION
    )
    output_noise = min(
        1.0,
        (erreurs_count + len(actions) + stderr_contribution) / _OUTPUT_NOISE_NORMALIZER,
    )
    lilith_pressure = min(1.0, lilith_variance / (PHI**2 * 100.0))
    phidelia_signal = radiance / 100.0
    blocking_pressure = min(1.0, blocking_findings / PHI)

    consensus_brut = (
        _CONSENSUS_WEIGHTS["phidelia_signal"] * phidelia_signal
        + _CONSENSUS_WEIGHTS["lilith_pressure"] * (1.0 - lilith_pressure)
        + _CONSENSUS_WEIGHTS["output_noise"] * (1.0 - output_noise)
        + _CONSENSUS_WEIGHTS["blocking_pressure"] * (1.0 - blocking_pressure)
    )
    consensus_score = round(max(0.0, min(100.0, consensus_brut * 100.0)), 2)

    if blocking_findings == 0 and consensus_score >= 72.0 and erreurs_count <= 1:
        decision = "AUTO_RESOLVE"
    elif consensus_score >= 45.0:
        decision = "REVIEW"
    else:
        decision = "ESCALATE"

    if not actions and blocking_findings:
        actions.append("Corriger les findings bloquants avant toute relance de la CI.")
    if not actions and erreurs_count:
        actions.append(
            "Rejouer localement les étapes en échec pour isoler la cause racine."
        )

    return {
        "consensus_score": consensus_score,
        "decision": decision,
        "signals": {
            "phidelia_signal": round(phidelia_signal, 4),
            "lilith_pressure": round(lilith_pressure, 4),
            "output_noise": round(output_noise, 4),
            "blocking_pressure": round(blocking_pressure, 4),
        },
        "captured_output": {
            "stdout": stdout,
            "stderr": stderr,
            "errors": errors,
        },
        "actions": actions,
    }


class JournalConflits:
    """Journal append-only des conflits et de leur consensus de résolution."""

    def __init__(self, workspace_root: str = ".") -> None:
        self.phi_dir = os.path.join(workspace_root, ".phi")
        self.journal_path = os.path.join(self.phi_dir, "conflicts.jsonl")
        if not os.path.exists(self.phi_dir):
            os.makedirs(self.phi_dir)

    def enregistrer_conflit(
        self,
        source: str,
        invariants: Dict[str, Any],
        sorties: Optional[Dict[str, Any]] = None,
        contexte: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        resolution = resoudre_conflit_par_consensus(invariants, sorties)
        evenement = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": source,
            "invariants": dict(invariants),
            "resolution": resolution,
            "contexte": dict(contexte or {}),
        }
        evenement_hashable = json.dumps(evenement, sort_keys=True, ensure_ascii=False)
        evenement["hash"] = hashlib.sha256(evenement_hashable.encode()).hexdigest()
        evenement_json = json.dumps(evenement, sort_keys=True, ensure_ascii=False)

        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(evenement_json + "\n")
        return evenement

    def lire_journal(self, limite: int = 50) -> List[Dict[str, Any]]:
        if not os.path.exists(self.journal_path):
            return []
        try:
            with open(self.journal_path, "r", encoding="utf-8") as f:
                lignes = [json.loads(line) for line in f if line.strip()]
            return lignes[-limite:]
        except (json.JSONDecodeError, OSError):
            return []


def journaliser_conflit_audit(
    audit: Dict[str, Any],
    sorties: Optional[Dict[str, Any]] = None,
    workspace_root: str = ".",
    source: str = "phi-shield",
    contexte: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construit et journalise un conflit à partir d'un audit sécurité."""
    summary = audit.get("summary", {})
    findings = audit.get("findings", [])
    lilith_count = sum(
        1 for finding in findings if str(finding.get("rule_id", "")).upper() == "LILITH"
    )
    invariants = {
        "radiance": float(summary.get("security_score", 0.0)),
        "security_score": float(summary.get("security_score", 0.0)),
        "blocking_findings": int(summary.get("blocking_findings", 0)),
        "out_of_scope_findings": int(summary.get("out_of_scope_findings", 0)),
        "lilith_variance": round(lilith_count * (PHI**2), 4),
    }
    journal = JournalConflits(workspace_root=workspace_root)
    contexte_audit = {
        "findings_total": int(summary.get("findings_total", 0)),
        "errors_total": len(audit.get("errors", [])),
    }
    if contexte:
        contexte_audit.update(contexte)
    return journal.enregistrer_conflit(
        source=source,
        invariants=invariants,
        sorties=sorties,
        contexte=contexte_audit,
    )


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


_NIVEAU_VERS_SEVERITE = {
    "CRITICAL": "critical",
    "ERROR": "high",
    "WARNING": "medium",
    "NOTE": "low",
    "INFO": "info",
}

# Pondérations alignées sur une décroissance φ.
_SEVERITY_HIGH_BASE = 16.0
_SEVERITE_SCORE = {
    "critical": round(_SEVERITY_HIGH_BASE * PHI, 3),
    "high": _SEVERITY_HIGH_BASE,
    "medium": round(_SEVERITY_HIGH_BASE / PHI, 3),
    "low": round(_SEVERITY_HIGH_BASE / (PHI**2), 3),
    "info": round(_SEVERITY_HIGH_BASE / (PHI**3), 3),
}

# Seuils dérivés de φ pour garder l'harmonie mathématique du score.
_RADIANCE_THRESHOLD = round(100.0 / PHI, 3)
_MAX_RADIANCE_PENALTY = round(10.0 * PHI, 3)
_RADIANCE_PENALTY_DIVISOR = PHI
_SURFACE_DEMO_MARKERS = ("/examples/",)
# Décalages de confiance : +0.5 (source externe), +0.2 (moteur interne).
_CONFIDENCE_SARIF_OFFSET = 0.5
_CONFIDENCE_PHI_OFFSET = 0.2
_CONFIDENCE_BASE_SARIF = round(PHI / (PHI + _CONFIDENCE_SARIF_OFFSET), 2)
_CONFIDENCE_BASE_PHI = round(PHI / (PHI + _CONFIDENCE_PHI_OFFSET), 2)
_EXPLOITABILITY_CRITICAL = round(PHI / (PHI + 0.08), 2)
_EXPLOITABILITY_STANDARD = round(PHI / (PHI + 0.7), 2)
_EXPLOITABILITY_HIGH = round(PHI / (PHI + 0.2), 2)
_EXPLOITABILITY_MEDIUM = round(PHI / (PHI + 1.3), 2)

# Scanner-scope awareness: C-family scanners (Flawfinder, cppcheck …) produce
# false-positives when run against Python/scripting files.  Findings from such
# scanners on non-C files are downgraded to non-blocking.
_C_FAMILY_SCANNERS: frozenset[str] = frozenset(
    {"flawfinder", "cppcheck", "clang-tidy", "clang_tidy"}
)
# Extensions that C/C++ scanners legitimately analyse (Rust/asm excluded —
# Flawfinder and cppcheck do not process those formats).
_C_FAMILY_EXTENSIONS: frozenset[str] = frozenset(
    {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh"}
)


def _normaliser_severite(niveau: str) -> str:
    return _NIVEAU_VERS_SEVERITE.get(niveau.upper(), "medium")


def _surface_fichier(path: str) -> str:
    normalise = path.replace("\\", "/").lower()
    return (
        "demo"
        if any(marker in normalise for marker in _SURFACE_DEMO_MARKERS)
        else "production"
    )


def _confidence_par_source(source: str, severite: str) -> float:
    # Base plus faible pour SARIF (hétérogénéité externe), plus forte pour phi.
    base = _CONFIDENCE_BASE_SARIF if source == "sarif" else _CONFIDENCE_BASE_PHI
    bonus = {"critical": 0.08, "high": 0.05, "medium": 0.03, "low": 0.01}.get(
        severite, 0.0
    )
    return round(min(0.99, base + bonus), 2)


def _regle_phi_est_securite(categorie: str) -> bool:
    """Indique si une catégorie d'annotation phi relève de la sécurité.

    Parameters
    ----------
    categorie:
        Catégorie d'annotation émise par le moteur phi-complexity.

    Returns
    -------
    bool
        True si la catégorie représente une vulnérabilité sécurité (CWE-*),
        False pour les signaux qualité/maintenabilité.
    """
    # Les annotations phi "qualité/maintenabilité" (LILITH, CYCLOMATIQUE,
    # FIBONACCI, ...) ne doivent pas bloquer un gate sécurité.
    return categorie.upper().startswith("CWE-")


def _est_finding_securite(finding: Dict[str, Any]) -> bool:
    """Détermine si un finding doit impacter le score/policy sécurité.

    Le champ `security_relevant` est prioritaire lorsqu'il est fourni.
    Sinon, la décision est dérivée de la source et de la règle:
    - `phi-complexity` : seules les règles CWE-* sont sécurité;
    - autres sources (SARIF/outils externes) : sécurité par défaut.
    """
    if "security_relevant" in finding:
        return bool(finding.get("security_relevant"))
    source = str(finding.get("source", "")).lower()
    rule_id = str(finding.get("rule_id", ""))
    if source == "phi-complexity":
        return _regle_phi_est_securite(rule_id)
    return True


def _est_bloquant_security(
    security_relevant: bool, surface: str, severite: str
) -> bool:
    return (
        security_relevant
        and surface == "production"
        and severite in {"critical", "high"}
    )


def _finding_from_phi(path: str, annotation: Dict[str, Any]) -> Dict[str, Any]:
    categorie = str(annotation.get("categorie", "UNKNOWN"))
    niveau = str(annotation.get("niveau", "WARNING"))
    severite = _normaliser_severite(niveau)
    surface = _surface_fichier(path)
    message = str(annotation.get("message", ""))
    recommandation = ""
    if "Correction :" in message:
        recommandation = message.split("Correction :", 1)[1].strip()
    security_relevant = _regle_phi_est_securite(categorie)

    return {
        "source": "phi-complexity",
        "rule_id": categorie,
        "severity": severite,
        "path": path,
        "line": int(annotation.get("ligne", 0)),
        "message": message,
        "context": str(annotation.get("extrait", "")),
        "surface": surface,
        "security_relevant": security_relevant,
        "blocking": _est_bloquant_security(security_relevant, surface, severite),
        "confidence": _confidence_par_source("phi", severite),
        "exploitability": (
            _EXPLOITABILITY_CRITICAL
            if severite == "critical"
            else _EXPLOITABILITY_STANDARD
        ),
        "recommendation": recommandation,
    }


def _findings_from_sarif(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    findings: List[Dict[str, Any]] = []
    runs = payload.get("runs", [])
    if not isinstance(runs, list):
        return findings

    for run in runs:
        if not isinstance(run, dict):
            continue
        tool = run.get("tool", {})
        if not isinstance(tool, dict):
            tool = {}
        driver = tool.get("driver", {})
        if not isinstance(driver, dict):
            driver = {}
        source_name = str(driver.get("name", "sarif"))
        results = run.get("results", [])
        if not isinstance(results, list):
            continue
        for result in results:
            if not isinstance(result, dict):
                continue
            locations = result.get("locations", [])
            uri = ""
            line = 0
            if isinstance(locations, list) and locations:
                first = locations[0]
                if isinstance(first, dict):
                    phys = first.get("physicalLocation", {})
                    if not isinstance(phys, dict):
                        phys = {}
                    artifact = phys.get("artifactLocation", {})
                    if not isinstance(artifact, dict):
                        artifact = {}
                    region = phys.get("region", {})
                    if not isinstance(region, dict):
                        region = {}
                    uri = str(artifact.get("uri", ""))
                    line = int(region.get("startLine", 0))

            msg = result.get("message", {})
            if isinstance(msg, dict):
                message = str(msg.get("text", ""))
            else:
                message = str(msg)

            level = str(result.get("level", "warning")).upper()
            severite = _normaliser_severite(level)
            surface = _surface_fichier(uri)

            # Scanner-scope guard: C-family scanners produce false-positives
            # when pointed at Python/scripting files.  Such findings are kept
            # for traceability but are never marked as blocking.
            _, ext = os.path.splitext(uri.lower())
            is_c_scanner = source_name.lower() in _C_FAMILY_SCANNERS
            out_of_scope = is_c_scanner and ext not in _C_FAMILY_EXTENSIONS
            security_relevant = not out_of_scope

            findings.append(
                {
                    "source": source_name,
                    "rule_id": str(result.get("ruleId", "UNKNOWN")),
                    "severity": severite,
                    "path": uri,
                    "line": line,
                    "message": message,
                    "context": "",
                    "surface": surface,
                    "security_relevant": security_relevant,
                    "blocking": _est_bloquant_security(
                        security_relevant, surface, severite
                    ),
                    "out_of_scope": out_of_scope,
                    "confidence": _confidence_par_source("sarif", severite),
                    "exploitability": (
                        _EXPLOITABILITY_HIGH
                        if severite in {"critical", "high"}
                        else _EXPLOITABILITY_MEDIUM
                    ),
                    "recommendation": "",
                }
            )
    return findings


def _score_securite(findings: Sequence[Dict[str, Any]]) -> float:
    """Calcule un score de sécurité borné [0, 100].

    Parameters
    ----------
    findings:
        Séquence de findings normalisés (dict) contenant notamment `surface`,
        `severity`, et éventuellement `out_of_scope`/`security_relevant`.

    Notes
    -----
    Les métriques qualité (ex: radiance) sont volontairement exclues du
    calcul pour éviter des faux négatifs de sécurité en CI.

    Seuls les findings sécurité en surface production impactent le score.
    Les findings hors périmètre (`out_of_scope`) et les annotations qualité
    non-sécurité sont exclus.
    """
    # Le score de sécurité ne doit pas dériver des métriques qualité (radiance)
    # pour éviter les faux FAIL en CI "security gate".
    score = 100.0
    for finding in findings:
        if finding.get("surface") != "production":
            continue
        # Out-of-scope findings (e.g. Flawfinder false-positives on Python files)
        # are kept for traceability but do not penalize the score.
        if finding.get("out_of_scope"):
            continue
        if not _est_finding_securite(finding):
            continue
        severite = str(finding.get("severity", "medium"))
        score -= _SEVERITE_SCORE.get(severite, 5.0)

    return round(max(0.0, min(100.0, score)), 2)


def construire_audit_securite(
    fichiers: Sequence[str],
    sarif_path: Optional[str] = None,
    include_demo: bool = False,
) -> Dict[str, Any]:
    """
    Construit un audit sécurité unifié (phi + SARIF) avec score de risque.
    """
    from . import auditer

    findings: List[Dict[str, Any]] = []
    erreurs: List[str] = []

    for fichier in fichiers:
        try:
            metriques = auditer(fichier)
            annotations = metriques.get("annotations", [])
            if isinstance(annotations, list):
                for annot in annotations:
                    if isinstance(annot, dict):
                        findings.append(_finding_from_phi(fichier, annot))
        except Exception as exc:
            erreurs.append(f"{fichier}: {exc}")

    if sarif_path:
        try:
            findings.extend(_findings_from_sarif(sarif_path))
        except (OSError, json.JSONDecodeError) as exc:
            erreurs.append(f"sarif:{sarif_path}: {exc}")

    if not include_demo:
        findings = [f for f in findings if f.get("surface") != "demo"]

    score = _score_securite(findings)
    blocking = [
        f
        for f in findings
        if bool(f.get("blocking")) and f.get("surface") == "production"
    ]
    out_of_scope = [f for f in findings if bool(f.get("out_of_scope"))]
    severites: Dict[str, int] = {k: 0 for k in _SEVERITE_SCORE}
    for finding in findings:
        sev = str(finding.get("severity", "medium"))
        severites[sev] = severites.get(sev, 0) + 1

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "security_score": score,
            "findings_total": len(findings),
            "blocking_findings": len(blocking),
            "out_of_scope_findings": len(out_of_scope),
            "status": "PASS" if len(blocking) == 0 else "FAIL",
        },
        "governance": {
            "severity_distribution": severites,
            "kpi_false_positive_rate": None,
            "kpi_mttr_hours": None,
            "kpi_reopen_rate": None,
        },
        "findings": findings,
        "errors": erreurs,
    }


def exporter_audit_securite(audit: Dict[str, Any], chemin: str) -> str:
    contenu = json.dumps(audit, indent=2, ensure_ascii=False)
    dossier = os.path.dirname(chemin)
    if dossier and not os.path.exists(dossier):
        os.makedirs(dossier)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(contenu)
    return contenu


def verifier_politique_securite(
    audit: Dict[str, Any], min_security_score: float
) -> bool:
    summary = audit.get("summary", {})
    if not isinstance(summary, dict):
        return False
    score = float(summary.get("security_score", 0.0))
    blocking = int(summary.get("blocking_findings", 0))
    return score >= min_security_score and blocking == 0
