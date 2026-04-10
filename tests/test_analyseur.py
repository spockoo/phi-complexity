"""
tests/test_analyseur.py — Tests d'intégration sur le moteur d'analyse AST.
"""

import os
import textwrap
import tempfile
from phi_complexity.analyseur import AnalyseurPhi
from phi_complexity import auditer


def creer_fichier_temp(code: str) -> str:
    """Crée un fichier Python temporaire avec le code donné. Retourne le chemin."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(textwrap.dedent(code))
        return f.name


class TestAnalyseurPhi:

    def test_charger_et_analyser(self):
        """L'analyseur peut charger et analyser un fichier simple."""
        code = """
        def bonjour():
            return "Hello, φ-Meta!"
        """
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            assert len(resultat.fonctions) == 1
            assert resultat.fonctions[0].nom == "bonjour"
        finally:
            os.unlink(fichier)

    def test_detection_oudjat(self):
        """La fonction la plus complexe est bien identifiée comme Oudjat."""
        code = """
        def simple():
            return 1

        def complexe(a, b, c):
            for i in range(a):
                for j in range(b):
                    if i > j:
                        c += i * j
            return c
        """
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            assert resultat.oudjat is not None
            assert resultat.oudjat.nom == "complexe"
        finally:
            os.unlink(fichier)

    def test_annotation_boucle_imbriquee(self):
        """Les boucles imbriquées doivent générer une annotation LILITH."""
        code = """
        def trop_imbrique():
            for i in range(10):
                for j in range(10):
                    pass
        """
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "LILITH" in categories
        finally:
            os.unlink(fichier)

    def test_annotation_open_sans_context(self):
        """Un open() sans 'with' doit générer une annotation SUTURE."""
        code = """
        def lire_fichier():
            f = open("data.txt", "r")
            contenu = f.read()
            f.close()
            return contenu
        """
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "SUTURE" in categories
        finally:
            os.unlink(fichier)

    def test_pas_d_annotation_open_avec_context(self):
        """Un open() avec 'with' ne doit PAS générer d'annotation SUTURE."""
        code = """
        def lire_proprement():
            with open("data.txt", "r") as f:
                return f.read()
        """
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "SUTURE" not in categories
        finally:
            os.unlink(fichier)

    def test_fichier_vide_sans_fonctions(self):
        """Un fichier sans fonctions retourne un résultat neutre."""
        code = """
        # Simple constante
        MA_CONSTANTE = 42
        """
        fichier = creer_fichier_temp(code)
        try:
            resultat_dict = auditer(fichier)
            assert resultat_dict["nb_fonctions"] == 0
            assert resultat_dict["radiance"] == 60.0  # Score neutre
        finally:
            os.unlink(fichier)


class TestCalculateurRadiance:

    def test_code_harmonieux_score_eleve(self):
        """Un code simple et propre doit avoir un score de radiance élevé."""
        code = """
        def calculer_phi(n: int) -> float:
            \"\"\"Retourne approximation de phi après n itérations Fibonacci.\"\"\"
            a, b = 1, 1
            for _ in range(n):
                a, b = b, a + b
            return b / a

        def normaliser(valeur: float, mini: float, maxi: float) -> float:
            \"\"\"Normalise une valeur entre 0 et 1.\"\"\"
            if maxi == mini:
                return 0.0
            return (valeur - mini) / (maxi - mini)
        """
        fichier = creer_fichier_temp(code)
        try:
            metriques = auditer(fichier)
            assert (
                metriques["radiance"] >= 70
            ), f"Code harmonieux devrait scorer >= 70, obtenu: {metriques['radiance']}"
        finally:
            os.unlink(fichier)

    def test_radiance_bornee_40_100(self):
        """Le score de radiance doit toujours être entre 40 et 100."""
        # Code très chaotique
        code = """
        def enfer(a,b,c,d,e,f,g):
            x=0
            for i in range(a):
                for j in range(b):
                    for k in range(c):
                        if i>j:
                            if j>k:
                                x+=i*j*k*d*e*f*g
            return x
        """
        fichier = creer_fichier_temp(code)
        try:
            metriques = auditer(fichier)
            assert 40 <= metriques["radiance"] <= 100
        finally:
            os.unlink(fichier)

    def test_phi_ratio_calcule(self):
        """Le phi_ratio doit être calculé et présent dans les métriques."""
        code = """
        def a(): return 1
        def b(x, y):
            for i in range(x):
                y += i
            return y
        """
        fichier = creer_fichier_temp(code)
        try:
            metriques = auditer(fichier)
            assert "phi_ratio" in metriques
            assert metriques["phi_ratio"] > 1.0  # La grande fonction domine
        finally:
            os.unlink(fichier)

    def test_zeta_score_present_et_valide(self):
        """Le zeta_score doit être entre 0 et 1."""
        code = """
        def f1(): pass
        def f2(): pass
        def f3(): pass
        """
        fichier = creer_fichier_temp(code)
        try:
            metriques = auditer(fichier)
            assert 0 <= metriques["zeta_score"] <= 1.0
        finally:
            os.unlink(fichier)


class TestPhiIgnore:
    """Tests pour la directive inline `# phi: ignore`."""

    def test_ignore_global_supprime_annotation_lilith(self):
        """# phi: ignore sur la ligne de la boucle intérieure supprime l'annotation LILITH."""
        code = """\
def f():
    for i in range(10):
        for j in range(10):  # phi: ignore
            pass
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "LILITH" not in categories
        finally:
            os.unlink(fichier)

    def test_ignore_global_supprime_annotation_suture(self):
        """# phi: ignore sur un open() supprime l'annotation SUTURE."""
        code = """\
def lire():
    f = open("x.txt")  # phi: ignore
    return f.read()
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "SUTURE" not in categories
        finally:
            os.unlink(fichier)

    def test_ignore_cible_supprime_uniquement_categorie_ciblee(self):
        """# phi: ignore[SUTURE] supprime SUTURE mais laisse LILITH."""
        code = """\
def f():
    for i in range(10):
        for j in range(10):
            pass
    fic = open("out.txt", "w")  # phi: ignore[SUTURE]
    fic.write("x")
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "SUTURE" not in categories
            assert "LILITH" in categories
        finally:
            os.unlink(fichier)

    def test_ignore_multiple_categories(self):
        """# phi: ignore[LILITH,SUTURE] supprime les deux catégories."""
        code = """\
def f():
    for i in range(10):
        for j in range(10):  # phi: ignore[LILITH,SUTURE]
            pass
    fic = open("out.txt")  # phi: ignore[LILITH,SUTURE]
    fic.write("x")
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "LILITH" not in categories
            assert "SUTURE" not in categories
        finally:
            os.unlink(fichier)

    def test_ignore_insensible_casse(self):
        """La directive est insensible à la casse."""
        code = """\
def f():
    for i in range(10):
        for j in range(10):  # PHI: IGNORE
            pass
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "LILITH" not in categories
        finally:
            os.unlink(fichier)

    def test_sans_ignore_annote_normalement(self):
        """Sans directive, les annotations apparaissent normalement."""
        code = """\
def f():
    for i in range(10):
        for j in range(10):
            pass
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "LILITH" in categories
        finally:
            os.unlink(fichier)


class TestRegleV_Cyclomatique:
    """Tests pour la Règle V — Complexité Cyclomatique."""

    def test_complexite_harmonieuse_pas_d_annotation(self):
        """Une fonction simple (CC ≤ 8) ne génère pas d'annotation CYCLOMATIQUE."""
        code = """\
def f(x):
    if x > 0:
        return x
    return -x
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "CYCLOMATIQUE" not in categories
        finally:
            os.unlink(fichier)

    def test_complexite_elevee_genere_warning(self):
        """Une fonction avec CC entre 9 et 13 génère un WARNING CYCLOMATIQUE."""
        # Génère CC > 8 avec des if/elif/for
        code = """\
def traiter(a, b, c, d, e):
    if a > 0:
        pass
    if b > 0:
        pass
    if c > 0:
        pass
    if d > 0:
        pass
    if e > 0:
        pass
    for i in range(a):
        pass
    for j in range(b):
        pass
    for k in range(c):
        pass
    return a + b
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            annotations_cc = [
                a for a in resultat.annotations if a.categorie == "CYCLOMATIQUE"
            ]
            assert len(annotations_cc) > 0
        finally:
            os.unlink(fichier)

    def test_complexite_critique_genere_critical(self):
        """Une fonction avec CC > 13 génère une annotation CRITICAL."""
        code = """\
def monstre(a, b, c, d, e):
    if a > 0:
        pass
    elif a < 0:
        pass
    if b > 0:
        pass
    elif b < 0:
        pass
    if c > 0:
        pass
    elif c < 0:
        pass
    if d > 0:
        pass
    elif d < 0:
        pass
    if e > 0:
        pass
    elif e < 0:
        pass
    for i in range(a):
        pass
    for j in range(b):
        pass
    for k in range(c):
        pass
    return a
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            annotations_cc = [
                a for a in resultat.annotations if a.categorie == "CYCLOMATIQUE"
            ]
            niveaux = [a.niveau for a in annotations_cc]
            assert "CRITICAL" in niveaux
        finally:
            os.unlink(fichier)

    def test_ignore_cyclomatique_supprime_annotation(self):
        """# phi: ignore[CYCLOMATIQUE] supprime l'annotation Règle V."""
        code = """\
def traiter(a, b, c, d, e):  # phi: ignore[CYCLOMATIQUE]
    if a > 0:
        pass
    if b > 0:
        pass
    if c > 0:
        pass
    if d > 0:
        pass
    if e > 0:
        pass
    for i in range(a):
        pass
    for j in range(b):
        pass
    for k in range(c):
        pass
    return a + b
"""
        fichier = creer_fichier_temp(code)
        try:
            analyseur = AnalyseurPhi(fichier)
            resultat = analyseur.analyser()
            categories = [a.categorie for a in resultat.annotations]
            assert "CYCLOMATIQUE" not in categories
        finally:
            os.unlink(fichier)

    def test_compter_cyclomatique_base(self):
        """_compter_cyclomatique retourne au moins 1 (chemin de base)."""
        import ast as ast_mod
        from phi_complexity.analyseur import AnalyseurPythonInternal

        code = "def f(): return 1\n"
        fichier = creer_fichier_temp(code)
        try:
            a = AnalyseurPythonInternal(fichier)
            a.charger()
            assert a.tree is not None
            fn = next(
                (n for n in ast_mod.walk(a.tree) if isinstance(n, ast_mod.FunctionDef)),
                None,
            )
            assert fn is not None
            assert a._compter_cyclomatique(fn) == 1
        finally:
            os.unlink(fichier)

    def test_compter_cyclomatique_with_if(self):
        """CC d'une fonction avec un if = 2."""
        import ast as ast_mod
        from phi_complexity.analyseur import AnalyseurPythonInternal

        code = "def f(x):\n    if x:\n        return 1\n    return 0\n"
        fichier = creer_fichier_temp(code)
        try:
            a = AnalyseurPythonInternal(fichier)
            a.charger()
            assert a.tree is not None
            fn = next(
                (n for n in ast_mod.walk(a.tree) if isinstance(n, ast_mod.FunctionDef)),
                None,
            )
            assert fn is not None
            assert a._compter_cyclomatique(fn) == 2
        finally:
            os.unlink(fichier)

    def test_compter_cyclomatique_nested_function_excluded(self):
        """CC d'une fonction externe n'inclut pas les décisions des fonctions imbriquées."""
        import ast as ast_mod
        from phi_complexity.analyseur import AnalyseurPythonInternal

        code = (
            "def outer(x):\n"
            "    def inner(y):\n"
            "        if y > 0:\n"
            "            return y\n"
            "        if y < 0:\n"
            "            return -y\n"
            "        return 0\n"
            "    return inner(x)\n"
        )
        fichier = creer_fichier_temp(code)
        try:
            a = AnalyseurPythonInternal(fichier)
            a.charger()
            assert a.tree is not None
            fn = next(
                (
                    n
                    for n in ast_mod.walk(a.tree)
                    if isinstance(n, ast_mod.FunctionDef) and n.name == "outer"
                ),
                None,
            )
            assert fn is not None
            # outer a un seul chemin de base, sans décision propre → CC = 1
            assert a._compter_cyclomatique(fn) == 1
        finally:
            os.unlink(fichier)

    def test_compter_cyclomatique_comprehension_if(self):
        """CC d'une fonction avec une compréhension à filtre 'if' = 1 + nb_if."""
        import ast as ast_mod
        from phi_complexity.analyseur import AnalyseurPythonInternal

        # [x for x in lst if x > 0] → 1 filtre if → CC = 1 + 1 = 2
        code = "def f(lst):\n    return [x for x in lst if x > 0]\n"
        fichier = creer_fichier_temp(code)
        try:
            a = AnalyseurPythonInternal(fichier)
            a.charger()
            assert a.tree is not None
            fn = next(
                (n for n in ast_mod.walk(a.tree) if isinstance(n, ast_mod.FunctionDef)),
                None,
            )
            assert fn is not None
            assert a._compter_cyclomatique(fn) == 2
        finally:
            os.unlink(fichier)

    def test_compter_cyclomatique_boolop(self):
        """CC augmente d'un par opérande supplémentaire dans un BoolOp (and/or)."""
        import ast as ast_mod
        from phi_complexity.analyseur import AnalyseurPythonInternal

        # if a and b and c → BoolOp(values=[a, b, c]) → +2 (len-1=2) + 1 (If) = 3
        code = (
            "def f(a, b, c):\n    if a and b and c:\n        return 1\n    return 0\n"
        )
        fichier = creer_fichier_temp(code)
        try:
            a = AnalyseurPythonInternal(fichier)
            a.charger()
            assert a.tree is not None
            fn = next(
                (n for n in ast_mod.walk(a.tree) if isinstance(n, ast_mod.FunctionDef)),
                None,
            )
            assert fn is not None
            assert a._compter_cyclomatique(fn) == 4
        finally:
            os.unlink(fichier)

    def test_compter_cyclomatique_comp_sans_if(self):
        """Une compréhension sans clause 'if' n'incrémente pas CC."""
        import ast as ast_mod
        from phi_complexity.analyseur import AnalyseurPythonInternal

        code = "def f(xs):\n    return [x for x in xs]\n"
        fichier = creer_fichier_temp(code)
        try:
            a = AnalyseurPythonInternal(fichier)
            a.charger()
            assert a.tree is not None
            fn = next(
                (n for n in ast_mod.walk(a.tree) if isinstance(n, ast_mod.FunctionDef)),
                None,
            )
            assert fn is not None
            assert a._compter_cyclomatique(fn) == 1
        finally:
            os.unlink(fichier)

    def test_compter_cyclomatique_comp_avec_if(self):
        """Chaque clause 'if' dans une compréhension incrémente CC de 1."""
        import ast as ast_mod
        from phi_complexity.analyseur import AnalyseurPythonInternal

        # Two 'if' filters → CC = 1 (base) + 2
        code = "def f(xs):\n    return [x for x in xs if x > 0 if x < 10]\n"
        fichier = creer_fichier_temp(code)
        try:
            a = AnalyseurPythonInternal(fichier)
            a.charger()
            assert a.tree is not None
            fn = next(
                (n for n in ast_mod.walk(a.tree) if isinstance(n, ast_mod.FunctionDef)),
                None,
            )
            assert fn is not None
            assert a._compter_cyclomatique(fn) == 3
        finally:
            os.unlink(fichier)
