from __future__ import annotations
import re
from typing import Optional
from ..analyseur import ResultatAnalyse, MetriqueFonction, Annotation
from .base import AnalyseurBackend
from ..core import distance_fibonacci

class CRustLightBackend(AnalyseurBackend):
    """
    Backend souverain pour C, C++ et Rust.
    Analyse "Light" basée sur la profondeur des accolades et les patterns de fonctions.
    Zéro dépendances.
    """

    def analyser(self) -> ResultatAnalyse:
        with open(self.fichier, "r", encoding="utf-8") as f:
            lignes = f.readlines()
        
        resultat = ResultatAnalyse(fichier=self.fichier)
        resultat.nb_lignes_total = len(lignes)
        
        # Détection simple de fonctions (pattern: type nom(args) {)
        pattern_func = re.compile(r"^\s*(?:[\w<>:]+\s+)+(\w+)\s*\([^)]*\)\s*\{?")
        
        current_func_name: Optional[str] = None
        current_func_start: int = 0
        current_func_complexity: int = 0
        depth: int = 0
        
        for i, ligne in enumerate(lignes):
            ligne_strip = ligne.strip()
            if not ligne_strip:
                continue
            
            # Analyse des accolades
            prev_depth = depth
            depth += ligne_strip.count("{")
            depth -= ligne_strip.count("}")
            
            # Détection début de fonction
            if prev_depth == 0 and depth > 0:
                match = pattern_func.match(ligne_strip)
                if match:
                    current_func_name = match.group(1)
                    current_func_start = i + 1
                    current_func_complexity = 0
            
            # Comptage complexité
            if depth > 0:
                current_func_complexity += 1
                if depth > 2:
                    current_func_complexity += (depth - 2) * 2
            
            # Fin de fonction
            if prev_depth > 0 and depth == 0 and current_func_name:
                nb_lignes = (i + 1) - current_func_start + 1
                metrique = MetriqueFonction(
                    nom=current_func_name,
                    ligne=current_func_start,
                    complexite=current_func_complexity,
                    nb_args=0,
                    nb_lignes=nb_lignes,
                    profondeur_max=0,
                    distance_fib=distance_fibonacci(nb_lignes),
                    phi_ratio=1.0
                )
                resultat.fonctions.append(metrique)
                
                if current_func_complexity > 50:
                    resultat.annotations.append(Annotation(
                        ligne=current_func_start,
                        message=f"LILITH : Fonction '{current_func_name}' trop complexe pour le bas niveau ({current_func_complexity} nœuds).",
                        niveau="WARNING",
                        extrait=ligne_strip,
                        categorie="LILITH"
                    ))
                
                current_func_name = None

        if resultat.fonctions:
            resultat.oudjat = max(resultat.fonctions, key=lambda f: f.complexite)
            moyenne = sum(f.complexite for f in resultat.fonctions) / len(resultat.fonctions)
            if moyenne > 0:
                for f in resultat.fonctions:
                    f.phi_ratio = f.complexite / moyenne
        
        return resultat
