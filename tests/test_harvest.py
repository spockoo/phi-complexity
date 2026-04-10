"""
tests/test_harvest.py — Tests du moteur phi-harvest (Phase 14).
"""

import json
import os
import tempfile
import textwrap

from phi_complexity.harvest import HarvestEngine


def _safe_unlink(path: str) -> None:
    """Supprime un fichier sans lever d'exception s'il n'existe pas."""
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


CODE_HARMONIEUX = """
def ratio(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("zero")
    return a / b

def distance(valeur: float) -> float:
    phi = 1.618
    return abs(valeur - phi)
"""

CODE_CHAOTIQUE = """
def tout(a,b,c,d,e,f,g):
    res = []
    for i in range(a):
        for j in range(b):
            for k in range(c):
                res.append(i*j*k*d*e*f*g)
    fic = open("out.txt", "w")
    fic.write(str(res))
    return res
"""


def creer_fichier_temp(code: str) -> str:
    """Crée un fichier Python temporaire. Retourne le chemin."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(textwrap.dedent(code))
        return f.name


class TestHarvestEngine:

    def _engine_temp(self) -> tuple:
        """Crée un engine avec un fichier JSONL temporaire. Retourne (engine, path)."""
        tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        tmp.close()
        engine = HarvestEngine(sortie=tmp.name)
        return engine, tmp.name

    def test_collecter_produit_schema_valide(self):
        """Un vecteur collecté contient toutes les clés attendues."""
        code_file = creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine, jsonl = self._engine_temp()
            try:
                vecteur = engine.collecter(code_file)
                assert vecteur["schema"] == "1.1"
                assert "radiance" in vecteur
                assert "lilith_variance" in vecteur
                assert "shannon_entropy" in vecteur
                assert "fibonacci_entropy" in vecteur
                assert "phi_ratio" in vecteur
                assert "labels" in vecteur
                assert "vecteur_phi" in vecteur
                assert len(vecteur["vecteur_phi"]) == 5
            finally:
                _safe_unlink(jsonl)
        finally:
            _safe_unlink(code_file)

    def test_anonymisation_sans_identifiant(self):
        """Le vecteur ne contient pas le nom du fichier source."""
        code_file = creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine, jsonl = self._engine_temp()
            try:
                vecteur = engine.collecter(code_file)
                # Aucune trace du chemin du fichier dans le vecteur
                assert "fichier" not in vecteur
                assert code_file not in json.dumps(vecteur)
            finally:
                _safe_unlink(jsonl)
        finally:
            _safe_unlink(code_file)

    def test_labels_chaotique_detecte_violations(self):
        """Le code chaotique génère des labels de violation non nuls."""
        code_file = creer_fichier_temp(CODE_CHAOTIQUE)
        try:
            engine, jsonl = self._engine_temp()
            try:
                vecteur = engine.collecter(code_file)
                labels = vecteur["labels"]
                # Le code chaotique doit avoir au moins une violation
                total = sum(labels.values())
                assert total > 0
            finally:
                _safe_unlink(jsonl)
        finally:
            _safe_unlink(code_file)

    def test_exporter_et_compter(self):
        """L'export JSONL incrémente correctement le compteur."""
        code_file = creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine, jsonl = self._engine_temp()
            try:
                assert engine.compter_vecteurs() == 0
                engine.collecter_et_exporter(code_file)
                assert engine.compter_vecteurs() == 1
                engine.collecter_et_exporter(code_file)
                assert engine.compter_vecteurs() == 2
            finally:
                _safe_unlink(jsonl)
        finally:
            _safe_unlink(code_file)

    def test_charger_vecteurs(self):
        """Les vecteurs exportés sont rechargés correctement."""
        code_file = creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine, jsonl = self._engine_temp()
            try:
                engine.collecter_et_exporter(code_file)
                vecteurs = engine.charger_vecteurs()
                assert len(vecteurs) == 1
                assert "radiance" in vecteurs[0]
                assert vecteurs[0]["schema"] == "1.1"
            finally:
                _safe_unlink(jsonl)
        finally:
            _safe_unlink(code_file)

    def test_charger_vecteurs_vide(self):
        """Le chargement d'un fichier inexistant retourne une liste vide."""
        chemin = os.path.join(tempfile.gettempdir(), "phi_n_existe_pas_harvest.jsonl")
        engine = HarvestEngine(sortie=chemin)
        assert engine.charger_vecteurs() == []
        assert engine.compter_vecteurs() == 0

    def test_vecteur_phi_normalise(self):
        """Le vecteur φ est normalisé entre 0 et 1."""
        code_file = creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine, jsonl = self._engine_temp()
            try:
                vecteur = engine.collecter(code_file)
                for val in vecteur["vecteur_phi"]:
                    assert 0.0 <= val <= 1.0
            finally:
                _safe_unlink(jsonl)
        finally:
            _safe_unlink(code_file)

    def test_vecteur_phi_utilise_fibonacci_entropy(self):
        """Le vecteur φ utilise strictement l'entropie Fibonacci (H_F), pas Shannon."""
        code_file = creer_fichier_temp(CODE_CHAOTIQUE)
        try:
            engine, jsonl = self._engine_temp()
            try:
                vecteur = engine.collecter(code_file)
                # La composante [2] du vecteur_phi doit correspondre à fibonacci_entropy
                fib_ent = vecteur["fibonacci_entropy"]
                from phi_complexity.harvest import _NORM_ENTROPIE_FIB

                expected = min(1.0, fib_ent / _NORM_ENTROPIE_FIB)
                assert abs(vecteur["vecteur_phi"][2] - expected) < 1e-9
            finally:
                _safe_unlink(jsonl)
        finally:
            _safe_unlink(code_file)

    def test_fibonacci_entropy_non_negative(self):
        """L'entropie Fibonacci est toujours >= 0."""
        for code in (CODE_HARMONIEUX, CODE_CHAOTIQUE):
            code_file = creer_fichier_temp(code)
            try:
                engine, jsonl = self._engine_temp()
                try:
                    vecteur = engine.collecter(code_file)
                    assert vecteur["fibonacci_entropy"] >= 0.0
                finally:
                    _safe_unlink(jsonl)
            finally:
                _safe_unlink(code_file)

    def test_rapport_harvest_vide(self):
        """Le rapport sur un corpus vide est un message informatif."""
        chemin = os.path.join(tempfile.gettempdir(), "phi_n_existe_pas_harvest2.jsonl")
        engine = HarvestEngine(sortie=chemin)
        rapport = engine.rapport_harvest()
        assert "vide" in rapport.lower() or "harvest" in rapport.lower()

    def test_rapport_harvest_avec_donnees(self):
        """Le rapport avec données contient les métriques du corpus."""
        code_file = creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine, jsonl = self._engine_temp()
            try:
                engine.collecter_et_exporter(code_file)
                rapport = engine.rapport_harvest()
                assert "1" in rapport  # 1 vecteur collecté
                assert "HARVEST" in rapport
            finally:
                _safe_unlink(jsonl)
        finally:
            _safe_unlink(code_file)

    def test_assurer_dossier_cree_sous_dossier(self, tmp_path):
        """HarvestEngine crée le dossier de sortie s'il n'existe pas."""
        sous_dossier = tmp_path / "nouveau" / "sous"
        HarvestEngine(sortie=str(sous_dossier / "out.jsonl"))
        assert sous_dossier.exists()

    def test_exporter_leve_oserror(self, tmp_path):
        """exporter() lève OSError si le fichier est inaccessible."""
        from unittest.mock import patch
        engine = HarvestEngine(sortie=str(tmp_path / "out.jsonl"))
        with patch("builtins.open", side_effect=OSError("disk full")):
            try:
                engine.exporter({"test": 1})
                assert False, "OSError attendue"
            except OSError as exc:
                assert "Impossible d'écrire" in str(exc)

    def test_compter_vecteurs_oserror_retourne_zero(self, tmp_path):
        """compter_vecteurs() retourne 0 en cas d'OSError à la lecture."""
        from unittest.mock import patch
        jsonl = tmp_path / "test.jsonl"
        jsonl.write_text('{"a": 1}\n')
        engine = HarvestEngine(sortie=str(jsonl))
        with patch("builtins.open", side_effect=OSError("read error")):
            assert engine.compter_vecteurs() == 0

    def test_charger_vecteurs_oserror_retourne_liste_vide(self, tmp_path):
        """charger_vecteurs() retourne [] en cas d'OSError à la lecture."""
        from unittest.mock import patch
        jsonl = tmp_path / "test.jsonl"
        jsonl.write_text('{"a": 1}\n')
        engine = HarvestEngine(sortie=str(jsonl))
        with patch("builtins.open", side_effect=OSError("read error")):
            assert engine.charger_vecteurs() == []
