import ast
import inspect
import json
import os
import subprocess
from urllib import error, parse, request

class PhiArchitect:
    """
    Optimisé pour GitHub : Calcule le ratio d'or et auto-ajuste
    sa structure via AST. Nettoie les conflits de merge avant analyse.
    """

    def __init__(self):
        self.phi = 1.61803398875
        self.filename = inspect.getfile(self.__class__)

    def clean_merge_markers(self):
        """Supprime résidus de conflits Git (<<<<, ====, >>>>)."""
        if not os.path.exists(self.filename):
            return
        with open(self.filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        clean_lines = [l for l in lines if not any((l.startswith(m) for m in ['<<<<<<<', '=======', '>>>>>>>']))]
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.writelines(clean_lines)

    def run_cycle(self):
        self.clean_merge_markers()
        with open(self.filename, 'r', encoding='utf-8') as f:
            source = f.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            print('Erreur de syntaxe détectée. Nettoyage requis.')
            return False
        nodes = list(ast.walk(tree))
        logic_nodes = [n for n in nodes if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With))]
        data_nodes = [n for n in nodes if isinstance(n, (ast.Assign, ast.Constant, ast.List, ast.Dict))]
        ratio = len(data_nodes) / len(logic_nodes) if logic_nodes else len(data_nodes)
        diff = self.phi - ratio
        print(f'--- [PHI-ENGINE] Ratio: {ratio:.3f} | Cible: {self.phi:.3f} ---')
        if abs(diff) < 0.01:
            print('Harmonie atteinte.')
            return False
        if diff > 0:
            new_var_name = f'static_sync_{len(data_nodes)}'
            new_data = ast.Assign(targets=[ast.Name(id=new_var_name, ctx=ast.Store())], value=ast.Constant(value=round(diff, 4)))
            tree.body.insert(0, new_data)
            print(f'Injection : {new_var_name}')
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(ast.unparse(tree))
        return True

def handle_github_automation():
    """Gère l'évolution du code, le push ou la création de PR idempotente."""
    event = os.getenv('GITHUB_EVENT_NAME')
    repo = os.getenv('GITHUB_REPOSITORY')
    token = os.getenv('GITHUB_TOKEN')
    if not token or not repo:
        print('Infos GitHub manquantes (TOKEN ou REPO).')
        return
    owner = repo.split('/')[0]
    branch_name = 'evolution/phi-mutation'
    base_branch = 'main'
    subprocess.run(['git', 'config', 'user.name', 'Phi-Architect-Bot'])
    subprocess.run(['git', 'config', 'user.email', 'phi-bot@outlook.fr'])
    if event == 'push':
        print('Mode Push détecté : Mutation appliquée localement.')
        return
    try:
        subprocess.run(['git', 'checkout', '-B', branch_name], check=True)
        subprocess.run(['git', 'add', '.'], check=True)
        diff_check = subprocess.run(['git', 'diff', '--cached', '--quiet'], check=False)
        if diff_check.returncode == 0:
            print('Aucun changement structurel à proposer.')
            return
        subprocess.run(['git', 'commit', '-m', '🧬 evolution: mutation structurelle phi'], check=True)
        subprocess.run(['git', 'push', '--force', 'origin', branch_name], check=True)
    except Exception as e:
        print(f'Erreur Git : {e}')
        return
    query = parse.urlencode({'state': 'open', 'head': f'{owner}:{branch_name}', 'base': base_branch})
    api_url = f'https://api.github.com/repos/{repo}/pulls'
    try:
        req = request.Request(f'{api_url}?{query}')
        req.add_header('Authorization', f'token {token}')
        req.add_header('Accept', 'application/vnd.github.v3+json')
        with request.urlopen(req) as resp:
            open_prs = json.loads(resp.read().decode('utf-8'))
        if open_prs:
            print(f"PR déjà existante (# {open_prs[0]['number']}). Mise à jour effectuée.")
            return
        payload = json.dumps({'title': '✨ Évolution Structurelle (Phi)', 'head': branch_name, 'base': base_branch, 'body': "Mutation algorithmique vers le ratio d'or."}).encode('utf-8')
        post_req = request.Request(api_url, data=payload, method='POST')
        post_req.add_header('Authorization', f'token {token}')
        post_req.add_header('Content-Type', 'application/json')
        with request.urlopen(post_req) as resp:
            print('Nouvelle PR créée avec succès.')
    except error.HTTPError as e:
        print(f'Erreur API GitHub : {e.code} {e.reason}')
if __name__ == '__main__':
    architect = PhiArchitect()
    if architect.run_cycle():
        if os.getenv('GITHUB_ACTIONS'):
            handle_github_automation()