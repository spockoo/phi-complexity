import ast
import inspect
import os

class PhiArchitect:
    """
    Optimisé pour GitHub : Calcule le ratio d'or et auto-ajuste 
    sa structure via AST avant le prochain commit.
    """
    def __init__(self):
        self.phi = 1.61803398875
        # Détection dynamique du fichier même sur le runner GitHub
        self.filename = inspect.getfile(self.__class__)

    def run_cycle(self):
        with open(self.filename, "r", encoding="utf-8") as f:
            source = f.read()
        
        tree = ast.parse(source)
        nodes = list(ast.walk(tree))
        
        # Séparation stricte Logique (Contrôle) vs Données (Structure)
        logic_nodes = [n for n in nodes if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With))]
        data_nodes = [n for n in nodes if isinstance(n, (ast.Assign, ast.Constant, ast.List, ast.Dict))]
        
        ratio = len(data_nodes) / len(logic_nodes) if logic_nodes else len(data_nodes)
        diff = self.phi - ratio

        print(f"--- [PHI-ENGINE] Ratio: {ratio:.3f} | Cible: {self.phi:.3f} ---")

        if abs(diff) < 0.01:
            print("Harmonie atteinte. Aucune mutation.")
            return False

        # Mutation par injection de constantes si le ratio est trop bas
        if diff > 0:
            new_data = ast.Assign(
                targets=[ast.Name(id=f"static_sync_{len(data_nodes)}", ctx=ast.Store())],
                value=ast.Constant(value=round(diff, 4))
            )
            # On injecte la donnée au début du module pour l'équilibre
            tree.body.insert(0, new_data)
            print(f"Injection de donnée détectée pour combler l'écart de {diff:.3f}")

        # Réécriture propre via AST (nettoie les commentaires inutiles au passage)
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(ast.unparse(tree))
        return True

if __name__ == "__main__":
    architect = PhiArchitect()
    mutated = architect.run_cycle()
    
    # Indique à GitHub Actions si une modification a eu lieu
    if mutated:
        print("Mutation complétée. Prêt pour commit.")
