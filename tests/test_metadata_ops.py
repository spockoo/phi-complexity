import json
import os
from typing import List, Dict, Any

from phi_complexity.cli import _construire_parseur, _executer_metadata
from phi_complexity.metadata_ops import (
    default_sanitized_path,
    format_summary_text,
    sanitize_harvest,
    summarize_metadata,
)


def _write_harvest(path: str, vecteurs: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for v in vecteurs:
            f.write(json.dumps(v) + "\n")


def _read_harvest(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    result: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return result


def test_summarize_metadata_counts(tmp_path):
    harvest = tmp_path / "harvest.jsonl"
    vecteurs = [
        {
            "schema": "1.1",
            "radiance": 80.0,
            "labels": {"LILITH": 1},
            "zero_morphogenetic_state": "PRE_ZERO",
        },
        {
            "schema": "1.1",
            "radiance": 55.0,
            "labels": {"SUTURE": 2},
            "fingerprint": {"hash": "abc"},
            "zero_morphogenetic_state": "POST_RENAISSANCE",
        },
    ]
    _write_harvest(str(harvest), vecteurs)

    vault_index = tmp_path / "index.json"
    vault_index.write_text(
        json.dumps({"notes": {"a.py": {}, "b.py": {}}, "version": "16.0"})
    )

    resume = summarize_metadata(str(harvest), str(vault_index))
    assert resume["harvest"]["count"] == 2
    assert resume["harvest"]["labels"]["LILITH"] == 1
    assert resume["harvest"]["fingerprint"]["count"] == 1
    assert resume["vault"]["notes"] == 2

    texte = format_summary_text(resume)
    assert "PHI-METADATA" in texte
    assert "Vecteurs" in texte


def test_sanitize_harvest_removes_sensitive_and_labels(tmp_path):
    harvest = tmp_path / "harvest.jsonl"
    vecteur = {
        "schema": "1.1",
        "radiance": 90.0,
        "timestamp": 123456,
        "fingerprint": {"hash": "zzz"},
        "labels": {"LILITH": 1},
        "nb_critiques": 2,
        "custom": "keep-me?",
        "phi_ratio": 1.6,
    }
    _write_harvest(str(harvest), [vecteur])

    sortie = tmp_path / "sanitized.jsonl"
    resultat = sanitize_harvest(
        str(harvest),
        str(sortie),
        strip_keys={"custom"},
        strip_sensitive=True,
        strip_labels=True,
        keep_only_features=True,
    )

    assert resultat["written"] == 1
    contenu = _read_harvest(str(sortie))[0]
    assert "timestamp" not in contenu
    assert "fingerprint" not in contenu
    assert "labels" not in contenu
    assert "nb_critiques" not in contenu
    assert "custom" not in contenu
    assert "radiance" in contenu
    assert "phi_ratio" in contenu


def test_cli_metadata_purge_default_output(tmp_path, capsys):
    harvest = tmp_path / "harvest.jsonl"
    _write_harvest(
        str(harvest),
        [
            {
                "schema": "1.1",
                "radiance": 70.0,
                "fingerprint": {"hash": "abc"},
                "timestamp": 1,
            }
        ],
    )

    parser = _construire_parseur()
    args = parser.parse_args(
        ["metadata", "purge", "--harvest", str(harvest), "--strip-sensitive"]
    )
    code = _executer_metadata(args)
    out = capsys.readouterr().out

    sanitized_path = default_sanitized_path(str(harvest))
    assert code == 0
    assert os.path.exists(sanitized_path)
    contenu = _read_harvest(sanitized_path)[0]
    assert "fingerprint" not in contenu
    assert "timestamp" not in contenu
    assert "radiance" in contenu
    assert "Corpus purgé" in out


def test_cli_metadata_requires_action_manually():
    parser = _construire_parseur()
    args = parser.parse_args(["metadata"])
    assert getattr(args, "metadata_action", None) is None
    assert _executer_metadata(args) == 1


def test_sanitize_harvest_empty_file(tmp_path):
    harvest = tmp_path / "empty.jsonl"
    harvest.write_text("", encoding="utf-8")
    sortie = tmp_path / "sanitized_empty.jsonl"
    resultat = sanitize_harvest(str(harvest), str(sortie), strip_sensitive=True)
    assert resultat["written"] == 0
    assert _read_harvest(str(sortie)) == []


def test_cli_metadata_purge_missing_harvest(tmp_path, capsys):
    parser = _construire_parseur()
    args = parser.parse_args(
        [
            "metadata",
            "purge",
            "--harvest",
            str(tmp_path / "nonexistent.jsonl"),
            "--strip-sensitive",
        ]
    )
    code = _executer_metadata(args)
    assert code == 0
    sortie_path = default_sanitized_path(str(tmp_path / "nonexistent.jsonl"))
    contenu = _read_harvest(sortie_path)
    assert contenu == []


def test_sanitize_harvest_feature_only_preserves_features(tmp_path):
    harvest = tmp_path / "harvest_feat.jsonl"
    vecteur = {
        "schema": "1.1",
        "radiance": 85.0,
        "timestamp": 999,
        "fingerprint": {"hash": "abc"},
        "labels": {"LILITH": 1},
        "nb_critiques": 3,
        "phi_ratio": 1.618,
        "custom_key": "drop-me",
    }
    _write_harvest(str(harvest), [vecteur])
    sortie = tmp_path / "features.jsonl"
    resultat = sanitize_harvest(
        str(harvest),
        str(sortie),
        strip_keys={"radiance"},
        strip_sensitive=True,
        strip_labels=True,
        keep_only_features=True,
    )
    assert resultat["written"] == 1
    contenu = _read_harvest(str(sortie))[0]
    assert "radiance" in contenu
    assert "phi_ratio" in contenu
    assert "schema" in contenu
    assert "timestamp" not in contenu
    assert "fingerprint" not in contenu
    assert "labels" not in contenu
    assert "custom_key" not in contenu


def test_sanitize_harvest_skips_corrupted_lines(tmp_path):
    harvest = tmp_path / "harvest_corrupted.jsonl"
    harvest.write_text(
        '{"schema": "1.1", "radiance": 70.0}\n{invalid-json}\n{"schema":"1.2","radiance":75.0}\n',
        encoding="utf-8",
    )

    sortie = tmp_path / "sanitized_corrupted.jsonl"
    resultat = sanitize_harvest(str(harvest), str(sortie), strip_sensitive=True)

    assert resultat["written"] == 2
    contenu = _read_harvest(str(sortie))
    assert len(contenu) == 2
    assert contenu[0]["schema"] == "1.1"
    assert contenu[1]["schema"] == "1.2"
