"""
tests/test_fingerprint.py — Tests pour le moteur φ-fingerprint (Phase 24).

Couvre :
    - Calcul de fingerprint depuis un fichier Python
    - Calcul depuis des métriques pré-calculées
    - Normalisation du vecteur [0, 1]
    - Score d'anomalie et classification
    - Similitude cosinus entre fingerprints
    - Détection de format source
    - Sérialisation to_dict()
"""

from __future__ import annotations

import os
import tempfile
import textwrap

from phi_complexity.fingerprint import (
    FingerprintEngine,
    PhiFingerprint,
    similitude_cosinus,
    _FINGERPRINT_DIM,
    _SEUIL_SUSPECT,
    _SEUIL_MALVEILLANT,
)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────


def _safe_unlink(path: str) -> None:
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


def _creer_fichier_temp(code: str, suffix: str = ".py") -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    ) as f:
        f.write(textwrap.dedent(code))
        return f.name


# ──────────────────────────────────────────────
# TESTS DU FINGERPRINT ENGINE
# ──────────────────────────────────────────────


class TestFingerprintEngine:
    def test_calculer_retourne_fingerprint(self):
        """calculer() retourne un PhiFingerprint valide."""
        code_file = _creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            assert isinstance(fp, PhiFingerprint)
            assert len(fp.vecteur) == _FINGERPRINT_DIM
        finally:
            _safe_unlink(code_file)

    def test_vecteur_normalise_entre_0_et_1(self):
        """Toutes les dimensions du vecteur sont dans [0, 1]."""
        code_file = _creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            for v in fp.vecteur:
                assert 0.0 <= v <= 1.0, f"Dimension hors bornes : {v}"
        finally:
            _safe_unlink(code_file)

    def test_vecteur_normalise_chaotique(self):
        """Le code chaotique a aussi un vecteur dans [0, 1]."""
        code_file = _creer_fichier_temp(CODE_CHAOTIQUE)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            for v in fp.vecteur:
                assert 0.0 <= v <= 1.0
        finally:
            _safe_unlink(code_file)

    def test_classification_code_harmonieux_est_sain(self):
        """Un code harmonieux est classifié 'SAIN'."""
        code_file = _creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            assert fp.classification == "SAIN"
        finally:
            _safe_unlink(code_file)

    def test_score_anomalie_positif(self):
        """Le score d'anomalie est positif (>= 0)."""
        code_file = _creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            assert fp.score_anomalie >= 0.0
        finally:
            _safe_unlink(code_file)

    def test_score_anomalie_borne(self):
        """Le score d'anomalie est borné à [0, 1]."""
        code_file = _creer_fichier_temp(CODE_CHAOTIQUE)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            assert 0.0 <= fp.score_anomalie <= 1.0
        finally:
            _safe_unlink(code_file)

    def test_format_source_python(self):
        """Un fichier .py est détecté comme 'python'."""
        code_file = _creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            assert fp.format_source == "python"
        finally:
            _safe_unlink(code_file)

    def test_nb_sections_correspond_nb_fonctions(self):
        """nb_sections correspond au nombre de fonctions dans le code."""
        code_file = _creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            assert fp.nb_sections == 2  # ratio() et distance()
        finally:
            _safe_unlink(code_file)

    def test_to_dict(self):
        """to_dict() produit un dictionnaire sérialisable."""
        code_file = _creer_fichier_temp(CODE_HARMONIEUX)
        try:
            engine = FingerprintEngine()
            fp = engine.calculer(code_file)
            d = fp.to_dict()
            assert "vecteur" in d
            assert "score_anomalie" in d
            assert "classification" in d
            assert "nb_sections" in d
            assert "format_source" in d
            assert "timestamp" in d
            assert len(d["vecteur"]) == _FINGERPRINT_DIM
        finally:
            _safe_unlink(code_file)

    def test_calculer_depuis_metriques(self):
        """calculer_depuis_metriques() produit un fingerprint valide."""
        metriques = {
            "radiance": 85.0,
            "lilith_variance": 100.0,
            "shannon_entropy": 2.5,
            "phi_ratio": 1.618,
            "phi_ratio_delta": 0.0,
            "fibonacci_distance": 5.0,
            "zeta_score": 0.6,
            "nb_fonctions": 5,
            "oudjat": {"complexite": 50, "phi_ratio": 1.618},
        }
        engine = FingerprintEngine()
        fp = engine.calculer_depuis_metriques(metriques, "test.py")
        assert isinstance(fp, PhiFingerprint)
        assert len(fp.vecteur) == _FINGERPRINT_DIM
        assert fp.format_source == "python"

    def test_code_harmonieux_score_plus_bas_que_chaotique(self):
        """Le code harmonieux a un score d'anomalie plus bas que le chaotique."""
        fichier_h = _creer_fichier_temp(CODE_HARMONIEUX)
        fichier_c = _creer_fichier_temp(CODE_CHAOTIQUE)
        try:
            engine = FingerprintEngine()
            fp_h = engine.calculer(fichier_h)
            fp_c = engine.calculer(fichier_c)
            assert fp_h.score_anomalie <= fp_c.score_anomalie
        finally:
            _safe_unlink(fichier_h)
            _safe_unlink(fichier_c)


# ──────────────────────────────────────────────
# TESTS DE LA SIMILITUDE COSINUS
# ──────────────────────────────────────────────


class TestSimilitudeCosinus:
    def test_vecteurs_identiques(self):
        """Deux vecteurs identiques → similitude = 1.0."""
        v = [0.5, 0.3, 0.7, 0.1, 0.9, 0.4, 0.6, 0.2]
        assert abs(similitude_cosinus(v, v) - 1.0) < 1e-6

    def test_vecteurs_orthogonaux(self):
        """Vecteurs orthogonaux → similitude = 0.0."""
        a = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        assert abs(similitude_cosinus(a, b)) < 1e-6

    def test_vecteurs_vides(self):
        assert similitude_cosinus([], []) == 0.0

    def test_vecteurs_tailles_differentes(self):
        assert similitude_cosinus([1.0, 0.0], [1.0]) == 0.0

    def test_vecteur_nul(self):
        """Vecteur nul → similitude = 0.0."""
        a = [0.0] * 8
        b = [0.5] * 8
        assert similitude_cosinus(a, b) == 0.0

    def test_similitude_entre_0_et_1(self):
        """La similitude est toujours dans [0, 1]."""
        a = [0.3, 0.5, 0.7, 0.1, 0.9, 0.2, 0.4, 0.8]
        b = [0.8, 0.2, 0.4, 0.6, 0.3, 0.7, 0.1, 0.5]
        sim = similitude_cosinus(a, b)
        assert 0.0 <= sim <= 1.0

    def test_similitude_fichiers_python(self):
        """Deux fichiers Python ont une similitude significative."""
        fichier_h = _creer_fichier_temp(CODE_HARMONIEUX)
        fichier_c = _creer_fichier_temp(CODE_CHAOTIQUE)
        try:
            engine = FingerprintEngine()
            fp_h = engine.calculer(fichier_h)
            fp_c = engine.calculer(fichier_c)
            sim = similitude_cosinus(fp_h.vecteur, fp_c.vecteur)
            # Both are Python files so they should have some similarity
            assert sim > 0.0
        finally:
            _safe_unlink(fichier_h)
            _safe_unlink(fichier_c)


# ──────────────────────────────────────────────
# TESTS DE CLASSIFICATION
# ──────────────────────────────────────────────


class TestClassification:
    def test_sain(self):
        engine = FingerprintEngine()
        assert engine._classifier(0.3) == "SAIN"

    def test_suspect(self):
        engine = FingerprintEngine()
        assert engine._classifier(_SEUIL_SUSPECT) == "SUSPECT"

    def test_malveillant(self):
        engine = FingerprintEngine()
        assert engine._classifier(_SEUIL_MALVEILLANT) == "MALVEILLANT"

    def test_seuils_coherents(self):
        assert _SEUIL_SUSPECT < _SEUIL_MALVEILLANT


class TestDetecterFormat:
    def test_formats_connus(self):
        engine = FingerprintEngine()
        assert engine._detecter_format("py") == "python"
        assert engine._detecter_format("c") == "c"
        assert engine._detecter_format("elf") == "elf"
        assert engine._detecter_format("exe") == "pe"
        assert engine._detecter_format("asm") == "assembleur"
        assert engine._detecter_format("dylib") == "macho-dylib"

    def test_format_inconnu(self):
        engine = FingerprintEngine()
        assert engine._detecter_format("xyz") == "inconnu"
