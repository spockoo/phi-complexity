import ast
import inspect
import os


class PhiEngine:
    """
    Moteur récursif cherchant l'harmonie entre le flux (contrôle)
    et la forme (données) selon le nombre d'or.
    """

    def __init__(self):
        self.phi = (1 + 5**0.5) / 2  # 1.61803398875
        self.target_file = inspect.getfile(self.__class__)

    def get_metrics(self, node):
        """Parcourt l'AST de manière récursive pour compter les types de nœuds."""
        stats = {"logic": 0, "data": 0}

        for child in ast.walk(node):
            # Nœuds de contrôle (Complexité logique)
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                stats["logic"] += 1
            # Nœuds de données/action (Structure)
            elif isinstance(child, (ast.Assign, ast.Call, ast.BinOp, ast.Constant)):
                stats["data"] += 1
        return stats

    def evolve(self):
        """Analyse le fichier, calcule l'écart et applique une mutation corrective."""
        if not os.path.exists(self.target_file):
            return

        with open(self.target_file, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        metrics = self.get_metrics(tree)

        # Calcul du ratio actuel
        current_ratio = (
            metrics["data"] / metrics["logic"]
            if metrics["logic"] > 0
            else metrics["data"]
        )
        diff = self.phi - current_ratio

        print("--- Rapport d'évolution ---")
        print(f"Logique: {metrics['logic']} | Données: {metrics['data']}")
        print(f"Ratio actuel: {current_ratio:.4f} (Cible: {self.phi:.4f})")

        # Stratégie d'auto-amélioration :
        # Si le ratio est trop bas (trop de logique), on ajoute des constantes de données.
        # Si le ratio est trop haut, on simplifie (ici via un marqueur de stabilisation).
        if abs(diff) > 0.001:
            print(f"Écart de {diff:.4f} détecté. Mutation en cours...")

            with open(self.target_file, "a", encoding="utf-8") as f:
                if diff > 0:
                    # Ajoute un "Lest de Données" pour alourdir la structure vers Phi
                    f.write(
                        f"\n# PHI_STABILIZER_DATA = {list(range(int(diff * 10)))}\n"
                    )
                else:
                    # Note de simplification pour l'humain ou le prochain cycle
                    f.write("\n# TODO: Simplifier la logique. Ratio trop élevé.\n")
            return True

        print("Harmonie Phi atteinte. Aucune mutation requise.")
        return False


if __name__ == "__main__":
    engine = PhiEngine()
    engine.evolve()
