"""
tests/test_harvest.py — Tests du moteur phi-harvest (Phase 14).
"""
import json
import os
import tempfile
import textwrap

from phi_complexity.harvest import HarvestEngine


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
        tmp = tempfile.NamedTemporaryFile(
            suffix=".jsonl", delete=False
        )
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
                assert vecteur["schema"] == "1.0"
                assert "radiance" in vecteur
                assert "lilith_variance" in vecteur
                assert "shannon_entropy" in vecteur
                assert "phi_ratio" in vecteur
                assert "labels" in vecteur
                assert "vecteur_phi" in vecteur
                assert len(vecteur["vecteur_phi"]) == 5
            finally:
                os.unlink(jsonl)
        finally:
            os.unlink(code_file)

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
                os.unlink(jsonl)
        finally:
            os.unlink(code_file)

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
                os.unlink(jsonl)
        finally:
            os.unlink(code_file)

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
                os.unlink(jsonl)
        finally:
            os.unlink(code_file)

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
                assert vecteurs[0]["schema"] == "1.0"
            finally:
                os.unlink(jsonl)
        finally:
            os.unlink(code_file)

    def test_charger_vecteurs_vide(self):
        """Le chargement d'un fichier inexistant retourne une liste vide."""
        engine = HarvestEngine(sortie="/tmp/n_existe_pas_harvest.jsonl")
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
                os.unlink(jsonl)
        finally:
            os.unlink(code_file)

    def test_rapport_harvest_vide(self):
        """Le rapport sur un corpus vide est un message informatif."""
        engine = HarvestEngine(sortie="/tmp/n_existe_pas_harvest2.jsonl")
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
                os.unlink(jsonl)
        finally:
            os.unlink(code_file)
