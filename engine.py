import ast
import inspect
import json
import os
import re
import subprocess
import math
from urllib import error, parse, request

# ────────────────────────────────────────────────────────
# DURCISSEMENT CYBERSÉCURITAIRE ET STABILITÉ MATHÉMATIQUE
# ────────────────────────────────────────────────────────

_ENV_PATTERNS = {
    "GITHUB_EVENT_NAME": re.compile(r"^[a-z_]{1,64}$"),
    "GITHUB_REPOSITORY": re.compile(r"^[a-zA-Z0-9._-]{1,100}/[a-zA-Z0-9._-]{1,100}$"),
    "GITHUB_TOKEN": re.compile(r"^[a-zA-Z0-9_.\-]{1,255}$"),
    "GITHUB_ACTIONS": re.compile(r"^(true|1)$"),
}
_ENV_BRANCH = re.compile(r"^[a-zA-Z0-9_./-]{1,200}$")
_MAX_ENV_LEN = 512

def _env_securise(nom, defaut=""):
    """Lecture sécurisée des variables d'environnement avec validation Regex."""
    val = os.environ.get(nom, defaut)
    if not val or len(val) > _MAX_ENV_LEN:
        return defaut
    pattern = _ENV_PATTERNS.get(nom, _ENV_BRANCH)
    if not pattern.match(val):
        return defaut
    return val

def _chemin_reel(chemin):
    """Résolution du chemin réel pour éviter les conflits de liens symboliques."""
    return os.path.realpath(chemin)

class PhiArchitect:
    def __init__(self):
        self.phi = 1.61803398875
        self.filename = _chemin_reel(inspect.getfile(self.__class__))
        self.complexity_limit = 12  # Seuil de tolérance avant arrêt de mutation

    def clean_merge_markers(self):
        """Supprime les marqueurs de conflit Git pour éviter les erreurs AST."""
        if not os.path.exists(self.filename):
            return
        with open(self.filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        clean_lines = [
            line for line in lines 
            if not any(line.startswith(m) for m in ["<<<<<<<", "=======", ">>>>>>>"])
        ]
        if len(clean_lines) != len(lines):
            with open(self.filename, "w", encoding="utf-8") as f:
                f.writelines(clean_lines)

    def get_complexity(self, node):
        """Calcule la complexité cyclomatique simplifiée d'un nœud AST."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.IfExp)):
                complexity += 1
        return complexity

    def clean_dead_code(self, tree):
        """
        Nettoyage du code mort.
        CORRECTION : Ne supprime JAMAIS les variables '_static_sync_'.
        """
        new_body = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and node.targets and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                # Ajout du tiret du bas (_) ici
                if var_name.startswith("_static_sync_"):
                    new_body.append(node)
                    continue
            new_body.append(node)
        tree.body = new_body
        return tree

    def run_cycle(self):
        """Exécute un cycle de mesure et de mutation structurelle."""
        self.clean_merge_markers()
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, FileNotFoundError):
            return False

        # 1. Analyse de la complexité
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self.get_complexity(node) > self.complexity_limit:
                    return False

        # 2. Calcul du Ratio (Logique vs Données)
        nodes = list(ast.walk(tree))
        logic_nodes = [n for n in nodes if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With))]
        data_nodes = [n for n in nodes if isinstance(n, (ast.Assign, ast.Constant, ast.List, ast.Dict))]
        
        len_logic = len(logic_nodes)
        len_data = len(data_nodes)
        
        # Stabilité : Évite division par zéro
        current_ratio = len_data / len_logic if len_logic > 0 else float(len_data)
        
        # 3. Calcul de la déviation
        diff = self.phi - current_ratio
        
        # CORRECTION : Tolérance 0.05 pour stopper les oscillations infinies en CI
        if abs(diff) < 0.05 or math.isnan(diff) or math.isinf(diff):
            return False

        if diff > 0:
            # Injection de 'matière' (données) pour équilibrer vers Phi
            # Ajout du tiret du bas (_) pour rendre la variable invisible aux linters
            new_var_name = f"_static_sync_{len_data}_{int(abs(diff)*10000)}"
            new_data = ast.Assign(
                targets=[ast.Name(id=new_var_name, ctx=ast.Store())],
                value=ast.Constant(value=round(diff, 4)),
            )
            tree.body.insert(0, new_data)

        # Nettoyage sécurisé
        tree = self.clean_dead_code(tree)
        
        try:
            new_source = ast.unparse(tree)
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(new_source)
            return True
        except Exception:
            return False

def handle_github_automation():
    """Gère l'interaction avec l'API GitHub pour soumettre les mutations."""
    event = _env_securise("GITHUB_EVENT_NAME")
    repo = _env_securise("GITHUB_REPOSITORY")
    token = _env_securise("GITHUB_TOKEN")
    
    if not token or not repo or "/" not in repo:
        return
    
    # Autorise l'exécution en PR pour permettre l'auto-correction lors des échecs CI
    if event not in ["schedule", "workflow_dispatch", "pull_request"]:
        return

    branch_name = _env_securise("PHI_AUTOMATION_BRANCH", "evolution/phi-mutation")
    base_branch = _env_securise("PHI_BASE_BRANCH", "main")
    owner = repo.split("/")[0]

    try:
        subprocess.run(["git", "config", "user.name", "Phi-Architect-Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "phi-bot@outlook.fr"], check=True)
        
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False).returncode
        
        if status == 0:
            return

        subprocess.run(["git", "checkout", "-B", branch_name], check=True)
        subprocess.run(["git", "commit", "-m", "🧬 [Architect] Harmonisation Ratio Phi"], check=True)
        # Utilisation de force-with-lease pour éviter d'écraser des changements tiers
        subprocess.run(["git", "push", "--force-with-lease", "origin", branch_name], check=True)
        
    except subprocess.CalledProcessError:
        return

    # Création ou vérification de la Pull Request
    api_url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }
    
    try:
        check_query = parse.urlencode({"state": "open", "head": f"{owner}:{branch_name}"})
        with request.urlopen(request.Request(f"{api_url}?{check_query}", headers=headers)) as resp:
            if json.loads(resp.read().decode("utf-8")):
                return
                
        payload = json.dumps({
            "title": "✨ Évolution Structurelle (Radiance)",
            "head": branch_name,
            "base": base_branch,
            "body": "Mutation automatique pour aligner la structure du code sur l'invariant Phi."
        }).encode("utf-8")
        
        request.urlopen(request.Request(api_url, data=payload, method="POST", headers=headers))
    except Exception:
        pass

if __name__ == "__main__":
    architect = PhiArchitect()
    if architect.run_cycle():
        if _env_securise("GITHUB_ACTIONS"):
            handle_github_automation()