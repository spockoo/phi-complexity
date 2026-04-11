import ast
import inspect
import json
import os
import re
import subprocess
from urllib import error, parse, request

# ────────────────────────────────────────────────────────
# DURCISSEMENT CYBERSÉCURITAIRE
# CWE-807 / CWE-20  : validation stricte des entrées environnement
# CWE-362           : résolution sécurisée des chemins fichiers
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
    """Lecture sécurisée d'une variable d'environnement avec validation.

    Mitige CWE-807 (reliance on untrusted inputs in a security decision)
    et CWE-20 (improper input validation).
    """
    val = os.environ.get(nom, defaut)
    if not val:
        return defaut
    if len(val) > _MAX_ENV_LEN:
        return defaut
    pattern = _ENV_PATTERNS.get(nom, _ENV_BRANCH)
    if not pattern.match(val):
        return defaut
    return val


def _chemin_reel(chemin):
    """Résolution sécurisée d'un chemin fichier (CWE-362 / TOCTOU)."""
    return os.path.realpath(chemin)


class PhiArchitect:

    def __init__(self):
        self.phi = 1.61803398875
        self.filename = _chemin_reel(inspect.getfile(self.__class__))
        self.complexity_limit = 10

    def clean_merge_markers(self):
        if not os.path.exists(self.filename):
            return
        with open(self.filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
        clean_lines = [
            line
            for line in lines
            if not any((line.startswith(m) for m in ["<<<<<<<", "=======", ">>>>>>>"]))
        ]
        with open(self.filename, "w", encoding="utf-8") as f:
            f.writelines(clean_lines)

    def get_complexity(self, node):
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child,
                (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.IfExp),
            ):
                complexity += 1
        return complexity

    def clean_dead_code(self, tree):
        source = ast.unparse(tree)
        new_body = []
        for node in tree.body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) > 0
                and isinstance(node.targets[0], ast.Name)
            ):
                var_name = node.targets[0].id
                if var_name.startswith("static_sync_") and source.count(var_name) <= 1:
                    continue
            new_body.append(node)
        tree.body = new_body
        return tree

    def run_cycle(self):
        self.clean_merge_markers()
        with open(self.filename, "r", encoding="utf-8") as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                comp = self.get_complexity(node)
                if comp > self.complexity_limit:
                    return False
        nodes = list(ast.walk(tree))
        logic = [
            n
            for n in nodes
            if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With))
        ]
        data = [
            n
            for n in nodes
            if isinstance(n, (ast.Assign, ast.Constant, ast.List, ast.Dict))
        ]
        ratio = len(data) / len(logic) if logic else len(data)
        diff = self.phi - ratio
        if abs(diff) < 0.01:
            return False
        if diff > 0:
            new_var_name = f"static_sync_{len(data)}"
            new_data = ast.Assign(
                targets=[ast.Name(id=new_var_name, ctx=ast.Store())],
                value=ast.Constant(value=round(diff, 4)),
            )
            tree.body.insert(0, new_data)
        tree = self.clean_dead_code(tree)
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(ast.unparse(tree))
        return True


def handle_github_automation():
    """Gère l'automatisation GitHub : commit, push et création de PR."""
    event = _env_securise("GITHUB_EVENT_NAME")
    repo = _env_securise("GITHUB_REPOSITORY")
    token = _env_securise("GITHUB_TOKEN")
    if not token or not repo:
        print("Infos GitHub manquantes (TOKEN ou REPO).")
        return
    if event not in ["schedule", "workflow_dispatch"]:
        print("Événement sans création de PR automatique.")
        return
    branch_name = _env_securise("PHI_AUTOMATION_BRANCH", "evolution/phi-mutation")
    base_branch = _env_securise("PHI_BASE_BRANCH", "main")
    owner = repo.split("/")[0]
    try:
        subprocess.run(["git", "config", "user.name", "Phi-Architect-Bot"], check=True)
        subprocess.run(
            ["git", "config", "user.email", "phi-bot@outlook.fr"], check=True
        )
        subprocess.run(["git", "checkout", "-B", branch_name], check=True)
        subprocess.run(["git", "add", "."], check=True)
        diff_result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            check=False,
        )
        if diff_result.returncode not in {0, 1}:
            print(f"Erreur vérification des changements git pour {branch_name}.")
            return
        if diff_result.returncode == 0:
            print("Aucun changement à proposer en PR.")
            return
        subprocess.run(
            ["git", "commit", "-m", "🧬 [Cron] Harmonisation vers Ratio Phi"],
            check=True,
        )
        subprocess.run(
            ["git", "push", "--force-with-lease", "origin", branch_name],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Échec des opérations git pour {branch_name}: {exc}")
        return
    api_url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    query = parse.urlencode(
        {"state": "open", "head": f"{owner}:{branch_name}", "base": base_branch}
    )
    try:
        with request.urlopen(
            request.Request(f"{api_url}?{query}", headers=headers)
        ) as response:
            if json.loads(response.read().decode("utf-8")):
                print(f"PR déjà ouverte sur {branch_name}, mise à jour seulement.")
                return
        payload = json.dumps(
            {
                "title": "✨ Évolution Structurelle (Phi)",
                "head": branch_name,
                "base": base_branch,
                "body": "Rééquilibrage automatique et audit continu des commits non fusionnés.",
            }
        ).encode("utf-8")
        with request.urlopen(
            request.Request(
                api_url,
                data=payload,
                method="POST",
                headers={**headers, "Content-Type": "application/json"},
            )
        ):
            print(f"PR créée sur {branch_name}")
    except error.HTTPError as exc:
        print(
            f"Échec création/lecture PR pour {branch_name} dans {repo}: {exc.code} {exc.reason}"
        )
    except error.URLError as exc:
        print(
            f"Échec réseau création/lecture PR pour {branch_name} dans {repo}: {exc.reason}"
        )
    except json.JSONDecodeError:
        print(
            f"Réponse API invalide lors de la lecture des PR ouvertes pour {branch_name} dans {repo}."
        )


if __name__ == "__main__":
    architect = PhiArchitect()
    if architect.run_cycle():
        if _env_securise("GITHUB_ACTIONS"):
            handle_github_automation()
