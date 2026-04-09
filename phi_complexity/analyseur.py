from __future__ import annotations
import ast
from dataclasses import dataclass, field
from typing import List, Optional, Any

from .core import fibonacci_plus_proche, distance_fibonacci


# ────────────────────────────────────────────────────────
# STRUCTURES DE DONNÉES (dataclasses immuables)
# ────────────────────────────────────────────────────────

@dataclass
class MetriqueFonction:
    """Représente une fonction analysée avec toutes ses métriques brutes."""
    nom: str
    ligne: int
    complexite: int       # Nombre de nœuds AST (pression morphique)
    nb_args: int          # Nombre d'arguments
    nb_lignes: int        # Longueur en lignes
    profondeur_max: int   # Imbrication maximale
    distance_fib: float   # Éloignement de la séquence naturelle
    phi_ratio: float      # Rapport complexité/moyenne (idéal: φ)


@dataclass
class Annotation:
    """Une observation chirurgicale sur une ligne spécifique du code."""
    ligne: int
    message: str
    niveau: str           # 'INFO', 'WARNING', 'CRITICAL'
    extrait: str          # La ligne de code concernée
    categorie: str        # 'LILITH', 'SUTURE', 'SOUVERAINETE', 'FIBONACCI'


@dataclass
class ResultatAnalyse:
    """Contient tous les résultats bruts d'une analyse de fichier."""
    fichier: str
    fonctions: List[MetriqueFonction] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    nb_classes: int = 0
    nb_imports: int = 0
    nb_lignes_total: int = 0
    nb_commentaires: int = 0
    oudjat: Optional[MetriqueFonction] = None


# ────────────────────────────────────────────────────────
# ANALYSEUR PRINCIPAL
# ────────────────────────────────────────────────────────

class AnalyseurPhi:
    """
    Analyseur fractal basé sur AST.
    Dissèque le code Python pour extraire ses métriques souveraines.
    """

    def __init__(self, fichier: str):
        self.fichier = fichier
        self.tree: Optional[ast.AST] = None
        self.lignes: List[str] = []
        self.resultat = ResultatAnalyse(fichier=fichier)

    def charger(self) -> AnalyseurPhi:
        """Charge et parse le fichier Python avec gestionnaire de contexte (Règle II)."""
        with open(self.fichier, "r", encoding="utf-8") as f:
            contenu = f.read()
        self.lignes = contenu.splitlines()
        self.tree = ast.parse(contenu, filename=self.fichier)
        self._injecter_parents()
        return self

    def analyser(self) -> ResultatAnalyse:
        """Lance l'analyse complète. Orchestre — ne calcule pas directement."""
        if self.tree is None:
            self.charger()
        self.resultat.nb_lignes_total = len(self.lignes)
        self._compter_elements_globaux()
        self._analyser_fonctions()
        self._appliquer_regles_souveraines()
        self._identifier_oudjat()
        return self.resultat

    # ────────────────────────────────────────────────────────
    # PRÉPARATION DE L'ARBRE AST
    # ────────────────────────────────────────────────────────

    def _injecter_parents(self) -> None:
        """Injecte les références parent dans l'arbre AST pour la remontée."""
        if self.tree is None:
            return
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                setattr(child, "parent", node)

    def _compter_elements_globaux(self) -> None:
        """Compte classes, imports et commentaires (éléments macro)."""
        if self.tree is None:
            return
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                self.resultat.nb_classes += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self.resultat.nb_imports += 1
        self.resultat.nb_commentaires = sum(
            1 for ligne in self.lignes if ligne.strip().startswith("#")
        )

    # ────────────────────────────────────────────────────────
    # ANALYSE DES FONCTIONS
    # ────────────────────────────────────────────────────────

    def _analyser_fonctions(self) -> None:
        """Extrait les métriques de chaque fonction définie dans le fichier."""
        if self.tree is None:
            return
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrique = self._mesurer_fonction(node)
                self.resultat.fonctions.append(metrique)

    def _mesurer_fonction(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> MetriqueFonction:
        """Calcule toutes les métriques d'une seule fonction."""
        end_line: int = getattr(node, "end_lineno", node.lineno)
        nb_lignes: int = end_line - node.lineno + 1
        return MetriqueFonction(
            nom=node.name,
            ligne=node.lineno,
            complexite=len(list(ast.walk(node))),
            nb_args=len(node.args.args),
            nb_lignes=nb_lignes,
            profondeur_max=self._profondeur_imbrication(node),
            distance_fib=distance_fibonacci(nb_lignes),
            phi_ratio=1.0,  # Calculé après, quand la moyenne est connue
        )

    def _identifier_oudjat(self) -> None:
        """Identifie la fonction dominante et calcule les φ-ratios."""
        if not self.resultat.fonctions:
            return
        self.resultat.oudjat = max(
            self.resultat.fonctions, key=lambda f: f.complexite
        )
        self._calculer_phi_ratios()

    def _calculer_phi_ratios(self) -> None:
        """Normalise la complexité de chaque fonction par la moyenne."""
        moyenne: float = sum(f.complexite for f in self.resultat.fonctions) / len(
            self.resultat.fonctions
        )
        if moyenne == 0:
            return
        for f in self.resultat.fonctions:
            f.phi_ratio = f.complexite / moyenne

    # ────────────────────────────────────────────────────────
    # RÈGLES DE CODAGE SOUVERAIN (4 règles hermétiques)
    # ────────────────────────────────────────────────────────

    def _appliquer_regles_souveraines(self) -> None:
        """Applique les 4 règles souveraines à chaque nœud de l'AST."""
        if self.tree is None:
            return
        for node in ast.walk(self.tree):
            self._regle_lilith(node)
            self._regle_raii(node)
            self._regle_fibonacci(node)
            self._regle_hermeticite(node)

    def _regle_lilith(self, node: ast.AST) -> None:
        """Règle I — Nœuds d'Entropie : détecte les boucles trop imbriquées."""
        if not isinstance(node, (ast.For, ast.While)):
            return
        depth: int = self._profondeur_noeud(node)
        if depth >= 2:
            self._annoter(
                node.lineno,
                f"LILITH : Boucle imbriquée (profondeur {depth}). "
                "La variance s'accumule — envisagez une fonction auxiliaire.",
                "CRITICAL" if depth >= 3 else "WARNING",
                "LILITH"
            )

    def _regle_raii(self, node: ast.AST) -> None:
        """Règle II — Intégrité du Cycle de Vie : open() exige un gestionnaire."""
        if not isinstance(node, ast.Call):
            return
        if not self._est_appel_open(node):
            return
        parent: Any = getattr(node, "parent", None)
        grand_parent: Any = getattr(parent, "parent", None) if parent else None
        if isinstance(parent, ast.withitem) or isinstance(grand_parent, ast.With):
            return
        self._annoter(
            node.lineno,
            "SUTURE : 'open()' sans gestionnaire de contexte (with). "
            "Risque de traînée d'entropie (fuite de ressource).",
            "WARNING",
            "SUTURE"
        )

    def _regle_fibonacci(self, node: ast.AST) -> None:
        """Règle III — Taille Naturelle : les fonctions suivent Fibonacci."""
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        end_line: int = getattr(node, "end_lineno", node.lineno)
        nb_lignes: int = end_line - node.lineno + 1
        fib_proche: int = fibonacci_plus_proche(nb_lignes)
        if nb_lignes > 55 and abs(nb_lignes - fib_proche) > 10:
            self._annoter(
                node.lineno,
                f"FIBONACCI : '{node.name}' ({nb_lignes} lignes) s'éloigne "
                f"de la séquence naturelle (idéal: {fib_proche}). "
                "Scinder pour réduire la pression morphique.",
                "WARNING",
                "FIBONACCI"
            )

    def _regle_hermeticite(self, node: ast.AST) -> None:
        """Règle IV — Herméticité : une fonction ne reçoit pas plus de 5 args."""
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        nb_args: int = len(node.args.args)
        if nb_args > 5:
            self._annoter(
                node.lineno,
                f"SOUVERAINETÉ : '{node.name}' reçoit {nb_args} arguments. "
                "Encapsuler dans un objet (max: 5 / idéal φ: 3).",
                "INFO",
                "SOUVERAINETE"
            )

    # ────────────────────────────────────────────────────────
    # UTILITAIRES (fonctions pures, sans effets de bord)
    # ────────────────────────────────────────────────────────

    def _est_appel_open(self, node: ast.Call) -> bool:
        """Retourne True si le nœud est un appel à open()."""
        func = node.func
        if isinstance(func, ast.Name):
            return func.id == "open"
        if isinstance(func, ast.Attribute):
            return func.attr == "open"
        return False

    def _annoter(self, ligne: int, msg: str, niveau: str, categorie: str) -> None:
        """Enregistre une annotation chirurgicale sur une ligne de code."""
        extrait: str = self.lignes[ligne - 1].strip() if ligne <= len(self.lignes) else ""
        self.resultat.annotations.append(
            Annotation(ligne=ligne, message=msg, niveau=niveau,
                       extrait=extrait, categorie=categorie)
        )

    def _profondeur_imbrication(self, fn_node: ast.AST) -> int:
        """
        Profondeur max d'imbrication à l'intérieur d'une fonction.
        Utilise une pile explicite (pas de récursion) — Règle III (Fibonacci).
        """
        _NOEUD_CONTROLE = (ast.For, ast.While, ast.If, ast.With)
        pile = [(fn_node, 0)]
        max_depth = 0
        while pile:
            noeud, depth = pile.pop()
            est_controle = isinstance(noeud, _NOEUD_CONTROLE)
            profondeur_courante = depth + 1 if est_controle else depth
            max_depth = max(max_depth, profondeur_courante if est_controle else depth)
            for child in ast.iter_child_nodes(noeud):
                pile.append((child, profondeur_courante))
        return max_depth

    def _profondeur_noeud(self, node: ast.AST) -> int:
        """Profondeur globale d'un nœud via remontée des parents injectés."""
        _NOEUD_COMPTABLE = (ast.For, ast.While, ast.If, ast.FunctionDef)
        ancetres = self._remonter_parents(node)
        return sum(1 for a in ancetres if isinstance(a, _NOEUD_COMPTABLE))

    def _remonter_parents(self, node: ast.AST) -> List[ast.AST]:
        """Retourne la liste des nœuds ancêtres en remontant l'arbre."""
        ancetres: List[ast.AST] = []
        curr: Any = getattr(node, "parent", None)
        while curr is not None:
            ancetres.append(curr)
            curr = getattr(curr, "parent", None)
        return ancetres
