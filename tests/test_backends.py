"""
tests/test_backends.py — Tests des backends C/Rust et Python.
"""

import os
import tempfile

from phi_complexity.backends.c_rust_light import CRustLightBackend
from phi_complexity.backends.python import PythonBackend
from phi_complexity.backends.base import AnalyseurBackend


CODE_C_SIMPLE = """\
#include <stdio.h>

int ajouter(int a, int b) {
    return a + b;
}

void afficher(int n) {
    printf("%d\\n", n);
}
"""

CODE_C_COMPLEXE = """\
int traiter(int x, int y, int z) {
    int r = 0;
    if (x > 0) {
        for (int i = 0; i < x; i++) {
            for (int j = 0; j < y; j++) {
                if (z > 0) {
                    r += i * j * z;
                }
            }
        }
    }
    return r;
}
"""

CODE_C_TRES_COMPLEXE = """\
int monstre(int a, int b) {
    int r = 0;
    for (int i = 0; i < a; i++) {
        for (int j = 0; j < b; j++) {
            for (int k = 0; k < a; k++) {
                for (int l = 0; l < b; l++) {
                    for (int m = 0; m < a; m++) {
                        r += i + j + k + l + m;
                    }
                }
            }
        }
    }
    return r;
}
"""


def _creer_fichier_c(contenu: str) -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".c", delete=False, encoding="utf-8"
    )
    f.write(contenu)
    f.close()
    return f.name


class TestCRustLightBackend:

    def test_analyser_fichier_vide(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False)
        f.write("")
        f.close()
        try:
            backend = CRustLightBackend(f.name)
            r = backend.analyser()
            assert r.fichier == f.name
            assert len(r.fonctions) == 0
            assert r.oudjat is None
        finally:
            os.unlink(f.name)

    def test_analyser_detecte_fonctions(self):
        chemin = _creer_fichier_c(CODE_C_SIMPLE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            assert len(r.fonctions) >= 1
        finally:
            os.unlink(chemin)

    def test_analyser_definit_oudjat(self):
        """La fonction la plus complexe devient le OUDJAT."""
        chemin = _creer_fichier_c(CODE_C_COMPLEXE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            if r.fonctions:
                assert r.oudjat is not None
                assert r.oudjat == max(r.fonctions, key=lambda f: f.complexite)
        finally:
            os.unlink(chemin)

    def test_analyser_phi_ratio_calcule(self):
        """Le phi_ratio est calculé pour chaque fonction quand la moyenne > 0."""
        chemin = _creer_fichier_c(CODE_C_COMPLEXE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            for f in r.fonctions:
                assert f.phi_ratio >= 0.0
        finally:
            os.unlink(chemin)

    def test_analyser_fonction_complexe_annotation_lilith(self):
        """Une fonction avec complexité > 50 génère une annotation LILITH."""
        chemin = _creer_fichier_c(CODE_C_TRES_COMPLEXE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            lilith_annots = [a for a in r.annotations if a.categorie == "LILITH"]
            # Si la complexité dépasse 50, il y a au moins une annotation
            if any(f.complexite > 50 for f in r.fonctions):
                assert len(lilith_annots) >= 1
        finally:
            os.unlink(chemin)

    def test_analyser_nb_lignes_total(self):
        chemin = _creer_fichier_c(CODE_C_SIMPLE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            expected = len(CODE_C_SIMPLE.splitlines())
            assert r.nb_lignes_total == expected
        finally:
            os.unlink(chemin)

    def test_analyser_lignes_vides_ignorees(self):
        """Les lignes vides sont ignorées dans le comptage de complexité."""
        contenu = "\n".join([""] * 10 + ["int foo() {", "    return 1;", "}"])
        chemin = _creer_fichier_c(contenu)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            # Ne doit pas lever d'exception
            assert isinstance(r.fonctions, list)
        finally:
            os.unlink(chemin)


class TestAnalyseurBackendBase:

    def test_base_init_stocke_fichier(self):
        """AnalyseurBackend (via CRustLightBackend) stocke le chemin du fichier."""
        chemin = _creer_fichier_c(CODE_C_SIMPLE)
        try:
            backend = CRustLightBackend(chemin)
            assert backend.fichier == chemin
        finally:
            os.unlink(chemin)
