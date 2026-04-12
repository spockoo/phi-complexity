"""
Tests pour phi_complexity/consensus.py — Consensus par Rétroaction Positive Récursive.
"""

from __future__ import annotations

import json
import os
import tempfile

from phi_complexity.consensus import (
    ALPHA_RETROACTION,
    EPSILON_CONVERGENCE,
    MAX_ITERATIONS,
    SEUIL_CONSENSUS_FORT,
    SEUIL_CONSENSUS_MODERE,
    JournalConsensus,
    MoteurConsensus,
    ResultatConsensus,
    SignalConsensus,
    consensus_rapide,
)
from phi_complexity.core import PHI_INV

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────


class TestConstantes:
    """Vérification des constantes du module."""

    def test_epsilon_convergence(self) -> None:
        assert EPSILON_CONVERGENCE == 1e-4

    def test_max_iterations(self) -> None:
        assert MAX_ITERATIONS == 200

    def test_alpha_retroaction_equals_phi_inv(self) -> None:
        assert ALPHA_RETROACTION == PHI_INV

    def test_seuil_consensus_fort(self) -> None:
        assert SEUIL_CONSENSUS_FORT == 0.85

    def test_seuil_consensus_modere(self) -> None:
        assert SEUIL_CONSENSUS_MODERE == 0.60


# ──────────────────────────────────────────────
# SIGNAL CONSENSUS
# ──────────────────────────────────────────────


class TestSignalConsensus:
    """Tests du dataclass SignalConsensus."""

    def test_creation_basique(self) -> None:
        s = SignalConsensus("securite", 0.85, 0.9)
        assert s.source == "securite"
        assert s.score == 0.85
        assert s.confiance == 0.9

    def test_clamping_score_max(self) -> None:
        s = SignalConsensus("test", 1.5)
        assert s.score == 1.0

    def test_clamping_score_min(self) -> None:
        s = SignalConsensus("test", -0.3)
        assert s.score == 0.0

    def test_clamping_confiance_max(self) -> None:
        s = SignalConsensus("test", 0.5, 2.0)
        assert s.confiance == 1.0

    def test_clamping_confiance_min(self) -> None:
        s = SignalConsensus("test", 0.5, -0.5)
        assert s.confiance == 0.0

    def test_confiance_defaut(self) -> None:
        s = SignalConsensus("test", 0.5)
        assert s.confiance == 0.8

    def test_metadata_vide_par_defaut(self) -> None:
        s = SignalConsensus("test", 0.5)
        assert s.metadata == {}

    def test_metadata_personnalisee(self) -> None:
        s = SignalConsensus("test", 0.5, metadata={"cle": "valeur"})
        assert s.metadata == {"cle": "valeur"}


# ──────────────────────────────────────────────
# RESULTAT CONSENSUS
# ──────────────────────────────────────────────


class TestResultatConsensus:
    """Tests du dataclass ResultatConsensus."""

    def test_to_dict_serialisation(self) -> None:
        r = ResultatConsensus(
            score_consensus=0.83456789,
            niveau="FORT ✦",
            iterations=12,
            convergent=True,
            delta_final=1e-7,
            poids_finaux={"sec": 0.4, "qual": 0.6},
            signaux=[SignalConsensus("sec", 0.85), SignalConsensus("qual", 0.80)],
            historique=[0.82, 0.83, 0.834],
            hash_consensus="abc123",
            timestamp="2026-01-01T00:00:00Z",
        )
        d = r.to_dict()
        assert d["score_consensus"] == 0.834568
        assert d["niveau"] == "FORT ✦"
        assert d["iterations"] == 12
        assert d["convergent"] is True
        assert len(d["signaux"]) == 2
        assert len(d["historique"]) == 3
        assert d["hash_consensus"] == "abc123"

    def test_to_dict_est_json_serialisable(self) -> None:
        r = ResultatConsensus(
            score_consensus=0.5,
            niveau="MODÉRÉ ◈",
            iterations=5,
            convergent=True,
            delta_final=0.0,
            poids_finaux={"a": 1.0},
            signaux=[SignalConsensus("a", 0.5)],
        )
        json_str = json.dumps(r.to_dict(), ensure_ascii=False)
        assert "MODÉRÉ" in json_str


# ──────────────────────────────────────────────
# JOURNAL CONSENSUS
# ──────────────────────────────────────────────


class TestJournalConsensus:
    """Tests du journal structuré."""

    def test_enregistrer_et_lire(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            j = JournalConsensus(tmpdir)
            j.enregistrer("test_event", {"cle": "valeur"})
            entries = j.lire()
            assert len(entries) == 1
            assert entries[0]["evenement"] == "test_event"
            assert entries[0]["details"]["cle"] == "valeur"
            assert "hash" in entries[0]
            assert "timestamp" in entries[0]

    def test_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            j = JournalConsensus(tmpdir)
            j.enregistrer("event_1", {})
            j.enregistrer("event_2", {})
            j.enregistrer("event_3", {})
            entries = j.lire()
            assert len(entries) == 3

    def test_lire_journal_inexistant(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            j = JournalConsensus(tmpdir)
            entries = j.lire()
            assert entries == []

    def test_lire_avec_limite(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            j = JournalConsensus(tmpdir)
            for i in range(10):
                j.enregistrer(f"event_{i}", {"i": i})
            entries = j.lire(limite=3)
            assert len(entries) == 3
            assert entries[0]["details"]["i"] == 7
            assert entries[2]["details"]["i"] == 9

    def test_verifier_integrite_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            j = JournalConsensus(tmpdir)
            j.enregistrer("test", {"v": 42})
            j.enregistrer("test2", {"v": 99})
            assert j.verifier_integrite() is True

    def test_verifier_integrite_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            j = JournalConsensus(tmpdir)
            j.enregistrer("test", {"v": 42})

            # Corrompre le journal
            with open(j.journal_path, "r") as f:
                content = f.read()
            content = content.replace('"v": 42', '"v": 999')
            with open(j.journal_path, "w") as f:
                f.write(content)

            assert j.verifier_integrite() is False

    def test_cree_repertoire_consensus(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            JournalConsensus(tmpdir)
            assert os.path.isdir(os.path.join(tmpdir, ".phi", "consensus"))


# ──────────────────────────────────────────────
# MOTEUR CONSENSUS
# ──────────────────────────────────────────────


class TestMoteurConsensus:
    """Tests du moteur de consensus RPR."""

    def test_consensus_vide(self) -> None:
        m = MoteurConsensus()
        r = m.calculer_consensus([])
        assert r.score_consensus == 0.0
        assert r.niveau == "VIDE"
        assert r.convergent is True
        assert r.iterations == 0

    def test_consensus_signal_unique(self) -> None:
        m = MoteurConsensus()
        r = m.calculer_consensus([SignalConsensus("sec", 0.80)])
        assert abs(r.score_consensus - 0.80) < 1e-6
        assert r.convergent is True
        assert "sec" in r.poids_finaux

    def test_consensus_signaux_identiques(self) -> None:
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("a", 0.90, 0.8),
            SignalConsensus("b", 0.90, 0.8),
            SignalConsensus("c", 0.90, 0.8),
        ]
        r = m.calculer_consensus(signaux)
        assert abs(r.score_consensus - 0.90) < 1e-6
        assert r.convergent is True
        assert r.niveau == "FORT ✦"

    def test_consensus_convergence(self) -> None:
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("securite", 0.85, 0.9),
            SignalConsensus("qualite", 0.78, 0.85),
            SignalConsensus("crypto", 0.90, 0.75),
        ]
        r = m.calculer_consensus(signaux)
        assert r.convergent is True
        assert r.iterations > 0
        assert r.delta_final < EPSILON_CONVERGENCE

    def test_consensus_renforce_accords(self) -> None:
        """Les signaux proches du consensus voient leur poids renforcé."""
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("a", 0.80, 0.5),
            SignalConsensus("b", 0.82, 0.5),
            SignalConsensus("c", 0.30, 0.5),  # Outlier
        ]
        r = m.calculer_consensus(signaux)
        # Les signaux "a" et "b" (concordants) devraient avoir
        # des poids plus élevés que "c" (divergent)
        assert r.poids_finaux["a"] > r.poids_finaux["c"]
        assert r.poids_finaux["b"] > r.poids_finaux["c"]

    def test_consensus_hash_integrite(self) -> None:
        m = MoteurConsensus()
        r = m.calculer_consensus([SignalConsensus("sec", 0.80)])
        assert len(r.hash_consensus) == 64  # SHA-256

    def test_consensus_timestamp(self) -> None:
        m = MoteurConsensus()
        r = m.calculer_consensus([SignalConsensus("sec", 0.80)])
        assert "T" in r.timestamp
        assert r.timestamp.endswith("Z")

    def test_consensus_historique(self) -> None:
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("a", 0.80, 0.9),
            SignalConsensus("b", 0.70, 0.8),
        ]
        r = m.calculer_consensus(signaux)
        # L'historique contient au minimum μ₀ et le score final
        assert len(r.historique) >= 2

    def test_classification_fort(self) -> None:
        m = MoteurConsensus()
        r = m.calculer_consensus(
            [SignalConsensus("a", 0.95), SignalConsensus("b", 0.92)]
        )
        assert "FORT" in r.niveau

    def test_classification_modere(self) -> None:
        m = MoteurConsensus()
        r = m.calculer_consensus(
            [SignalConsensus("a", 0.70), SignalConsensus("b", 0.65)]
        )
        assert "MODÉRÉ" in r.niveau

    def test_classification_faible(self) -> None:
        m = MoteurConsensus()
        r = m.calculer_consensus(
            [SignalConsensus("a", 0.30), SignalConsensus("b", 0.20)]
        )
        assert "FAIBLE" in r.niveau

    def test_max_iterations_atteint(self) -> None:
        """Avec un epsilon très petit, le moteur atteint max_iterations."""
        m = MoteurConsensus(epsilon=1e-30, max_iterations=5)
        signaux = [
            SignalConsensus("a", 0.90, 0.9),
            SignalConsensus("b", 0.50, 0.8),
        ]
        r = m.calculer_consensus(signaux)
        assert r.iterations == 5

    def test_avec_journalisation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            journal = JournalConsensus(tmpdir)
            m = MoteurConsensus(journal=journal)
            signaux = [
                SignalConsensus("sec", 0.85, 0.9),
                SignalConsensus("qual", 0.80, 0.8),
            ]
            m.calculer_consensus(signaux)
            entries = journal.lire(limite=10000)
            # Au minimum : debut + iteration_0 + iterations_1..N + fin
            assert len(entries) >= 3
            assert entries[0]["evenement"] == "consensus_debut"
            assert entries[-1]["evenement"] == "consensus_fin"

    def test_rapport_consensus_ascii(self) -> None:
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("securite", 0.85, 0.9),
            SignalConsensus("qualite", 0.78, 0.85),
        ]
        r = m.calculer_consensus(signaux)
        rapport = m.rapport_consensus(r)
        assert "PHI-CONSENSUS" in rapport
        assert "RÉTROACTION" in rapport
        assert "securite" in rapport
        assert "qualite" in rapport
        assert "█" in rapport

    def test_rapport_consensus_vide(self) -> None:
        m = MoteurConsensus()
        r = m.calculer_consensus([])
        rapport = m.rapport_consensus(r)
        assert "VIDE" in rapport

    def test_exporter_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            m = MoteurConsensus()
            signaux = [SignalConsensus("sec", 0.85)]
            r = m.calculer_consensus(signaux)
            chemin = os.path.join(tmpdir, "consensus.json")
            m.exporter_json(r, chemin)
            assert os.path.exists(chemin)
            with open(chemin) as f:
                data = json.load(f)
            assert "score_consensus" in data
            assert data["convergent"] is True

    def test_exporter_json_cree_repertoires(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            m = MoteurConsensus()
            r = m.calculer_consensus([SignalConsensus("a", 0.5)])
            chemin = os.path.join(tmpdir, "sub", "dir", "c.json")
            m.exporter_json(r, chemin)
            assert os.path.exists(chemin)

    def test_poids_zero_confiance(self) -> None:
        """Signaux avec confiance zéro → poids uniformes."""
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("a", 0.80, 0.0),
            SignalConsensus("b", 0.60, 0.0),
        ]
        r = m.calculer_consensus(signaux)
        assert r.convergent is True
        assert 0.0 <= r.score_consensus <= 1.0


# ──────────────────────────────────────────────
# CONSENSUS RAPIDE
# ──────────────────────────────────────────────


class TestConsensusRapide:
    """Tests de la fonction raccourci consensus_rapide."""

    def test_usage_basique(self) -> None:
        r = consensus_rapide({"securite": 0.85, "qualite": 0.78, "crypto": 0.92})
        assert r.convergent is True
        assert 0.0 <= r.score_consensus <= 1.0
        assert r.niveau != "VIDE"

    def test_avec_confiances(self) -> None:
        r = consensus_rapide(
            {"a": 0.90, "b": 0.80},
            confiances={"a": 0.95, "b": 0.60},
        )
        assert 0.0 <= r.score_consensus <= 1.0
        # Signal "a" plus fiable → score plus proche de 0.90
        assert r.score_consensus > 0.83

    def test_scores_vides(self) -> None:
        r = consensus_rapide({})
        assert r.score_consensus == 0.0
        assert r.niveau == "VIDE"

    def test_score_unique(self) -> None:
        r = consensus_rapide({"seul": 0.75})
        assert abs(r.score_consensus - 0.75) < 1e-6


# ──────────────────────────────────────────────
# PROPRIÉTÉS MATHÉMATIQUES
# ──────────────────────────────────────────────


class TestProprietesRPR:
    """Vérification des propriétés mathématiques du consensus RPR."""

    def test_idempotence(self) -> None:
        """Un consensus recalculé sur le même résultat converge au même score."""
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("a", 0.80, 0.9),
            SignalConsensus("b", 0.75, 0.85),
        ]
        r1 = m.calculer_consensus(signaux)
        r2 = m.calculer_consensus(signaux)
        assert abs(r1.score_consensus - r2.score_consensus) < 1e-9

    def test_monotonie_convergence(self) -> None:
        """Les deltas successifs diminuent globalement (tendance convergente)."""
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("a", 0.90, 0.9),
            SignalConsensus("b", 0.70, 0.8),
            SignalConsensus("c", 0.85, 0.7),
        ]
        r = m.calculer_consensus(signaux)
        if len(r.historique) >= 3:
            deltas = [abs(b - a) for a, b in zip(r.historique, r.historique[1:])]
            # Le score converge : les derniers deltas sont faibles
            assert deltas[-1] < 1e-4

    def test_bornes_score(self) -> None:
        """Le score de consensus reste dans [0, 1]."""
        m = MoteurConsensus()
        for score_val in [0.0, 0.1, 0.5, 0.9, 1.0]:
            signaux = [
                SignalConsensus("a", score_val, 0.9),
                SignalConsensus("b", score_val * 0.95, 0.8),
            ]
            r = m.calculer_consensus(signaux)
            assert 0.0 <= r.score_consensus <= 1.0

    def test_symetrie(self) -> None:
        """Le consensus est symétrique par rapport à l'ordre des signaux."""
        m = MoteurConsensus()
        s1 = [SignalConsensus("a", 0.80, 0.9), SignalConsensus("b", 0.70, 0.8)]
        s2 = [SignalConsensus("b", 0.70, 0.8), SignalConsensus("a", 0.80, 0.9)]
        r1 = m.calculer_consensus(s1)
        r2 = m.calculer_consensus(s2)
        assert abs(r1.score_consensus - r2.score_consensus) < 1e-9

    def test_poids_normalises(self) -> None:
        """Les poids finaux sont normalisés (∑ = 1)."""
        m = MoteurConsensus()
        signaux = [
            SignalConsensus("a", 0.80, 0.9),
            SignalConsensus("b", 0.70, 0.8),
            SignalConsensus("c", 0.85, 0.7),
        ]
        r = m.calculer_consensus(signaux)
        somme = sum(r.poids_finaux.values())
        assert abs(somme - 1.0) < 1e-9
