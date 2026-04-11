"""
tests/test_backends.py — Tests des backends C/Rust et Python.
"""

import os
import tempfile

from phi_complexity.backends.c_rust_light import CRustLightBackend

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


# ── Tests CWE-134 (Format String Vulnerability) ──────────────────


CODE_C_CWE134_VULNERABLE = """\
#include <stdio.h>

void log_msg(char *msg) {
    printf(msg);
}

void log_err(char *buf) {
    fprintf(stderr, buf);
    sprintf(buf, buf);
}
"""

CODE_C_CWE134_SAFE = """\
#include <stdio.h>

void afficher(const char *msg) {
    printf("%s\\n", msg);
    fprintf(stderr, "%s", msg);
    sprintf(buf, "%d", 42);
    snprintf(buf, sizeof(buf), "test %d", val);
}
"""

CODE_C_CWE134_MIXTE = """\
#include <stdio.h>

void mixte(char *user_input) {
    printf("Bienvenue %s\\n", user_input);
    printf(user_input);
    fprintf(stderr, "Erreur: %d\\n", code);
    fprintf(stderr, user_input);
}
"""


class TestCWE134Detection:
    """Tests pour la détection de CWE-134 (Format String Vulnerability)."""

    def test_detecte_printf_variable(self):
        """printf(variable) doit être signalé comme CWE-134."""
        chemin = _creer_fichier_c(CODE_C_CWE134_VULNERABLE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            assert len(cwe_annots) >= 1
            assert any("printf" in a.message for a in cwe_annots)
        finally:
            os.unlink(chemin)

    def test_detecte_fprintf_variable(self):
        """fprintf(stderr, variable) doit être signalé comme CWE-134."""
        chemin = _creer_fichier_c(CODE_C_CWE134_VULNERABLE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            assert any("fprintf" in a.message for a in cwe_annots)
        finally:
            os.unlink(chemin)

    def test_detecte_sprintf_variable(self):
        """sprintf(buf, variable) doit être signalé comme CWE-134."""
        chemin = _creer_fichier_c(CODE_C_CWE134_VULNERABLE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            assert any("sprintf" in a.message for a in cwe_annots)
        finally:
            os.unlink(chemin)

    def test_pas_faux_positif_format_litteral(self):
        """printf("%s", var) ne doit PAS être signalé."""
        chemin = _creer_fichier_c(CODE_C_CWE134_SAFE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            assert len(cwe_annots) == 0
        finally:
            os.unlink(chemin)

    def test_detecte_mixte_uniquement_vulnerable(self):
        """Seuls les appels avec format non-littéral sont signalés."""
        chemin = _creer_fichier_c(CODE_C_CWE134_MIXTE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            # Deux vulnérabilités : printf(user_input) et fprintf(stderr, user_input)
            assert len(cwe_annots) == 2
        finally:
            os.unlink(chemin)

    def test_cwe134_niveau_critical(self):
        """Les annotations CWE-134 doivent avoir le niveau CRITICAL."""
        chemin = _creer_fichier_c(CODE_C_CWE134_VULNERABLE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            for annot in cwe_annots:
                assert annot.niveau == "CRITICAL"
        finally:
            os.unlink(chemin)

    def test_cwe134_message_correction(self):
        """Le message CWE-134 doit proposer une correction."""
        chemin = _creer_fichier_c(CODE_C_CWE134_VULNERABLE)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            for annot in cwe_annots:
                assert "Correction" in annot.message or "correction" in annot.message
        finally:
            os.unlink(chemin)

    def test_cwe134_sur_moteur_c_exemple(self):
        """Le fichier examples/moteur_c.c contient des vulnérabilités CWE-134."""
        chemin = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "examples", "moteur_c.c"
        )
        if not os.path.exists(chemin):
            return  # Skip si le fichier n'existe pas
        backend = CRustLightBackend(chemin)
        r = backend.analyser()
        cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
        # Au moins 3 vulnérabilités dans moteur_c.c
        assert len(cwe_annots) >= 3

    def test_cwe134_commentaire_ignore(self):
        """Les lignes de commentaire ne déclenchent pas de faux positifs."""
        code = """\
#include <stdio.h>
void f() {
    // printf(buf);
    /* fprintf(stderr, buf); */
    printf("%s", "ok");
}
"""
        chemin = _creer_fichier_c(code)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            assert len(cwe_annots) == 0
        finally:
            os.unlink(chemin)

    def test_cwe134_snprintf_safe(self):
        """snprintf(buf, size, 'format', ...) est sûr avec un littéral."""
        code = """\
#include <stdio.h>
void f() {
    char buf[256];
    snprintf(buf, sizeof(buf), "valeur: %d", 42);
}
"""
        chemin = _creer_fichier_c(code)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            assert len(cwe_annots) == 0
        finally:
            os.unlink(chemin)

    def test_cwe134_snprintf_vulnerable(self):
        """snprintf(buf, size, variable) est vulnérable."""
        code = """\
#include <stdio.h>
void f(char *fmt) {
    char buf[256];
    snprintf(buf, sizeof(buf), fmt);
}
"""
        chemin = _creer_fichier_c(code)
        try:
            backend = CRustLightBackend(chemin)
            r = backend.analyser()
            cwe_annots = [a for a in r.annotations if a.categorie == "CWE-134"]
            assert len(cwe_annots) == 1
            assert "snprintf" in cwe_annots[0].message
        finally:
            os.unlink(chemin)


class TestDetecterCWE134Fonction:
    """Tests unitaires pour la fonction detecter_cwe_134 directement."""

    def test_ligne_vide(self):
        """Les lignes vides ne produisent rien."""
        from phi_complexity.backends.c_rust_light import detecter_cwe_134

        assert detecter_cwe_134([""]) == []

    def test_format_litteral(self):
        """Un format littéral ne produit aucun résultat."""
        from phi_complexity.backends.c_rust_light import detecter_cwe_134

        assert detecter_cwe_134(['    printf("hello %d\\n", x);']) == []

    def test_format_variable(self):
        """Un format variable produit un résultat."""
        from phi_complexity.backends.c_rust_light import detecter_cwe_134

        r = detecter_cwe_134(["    printf(buf);"])
        assert len(r) == 1
        assert r[0][0] == 1  # ligne 1
        assert r[0][1] == "printf"
