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
    """Crée/met à jour une branche d'évolution puis ouvre une seule PR idempotente."""
    event = os.getenv('GITHUB_EVENT_NAME')
    repo = os.getenv('GITHUB_REPOSITORY')
    token = os.getenv('GITHUB_TOKEN')
    if not token or not repo:
        print('Infos GitHub manquantes.')
        return
    if event not in ['schedule', 'workflow_dispatch']:
        print('Événement sans création de PR automatique.')
        return
    owner = repo.split('/')[0]
    branch_name = os.getenv('PHI_AUTOMATION_BRANCH', 'evolution/phi-mutation')
    subprocess.run(['git', 'config', 'user.name', 'Phi-Architect-Bot'])
    subprocess.run(['git', 'config', 'user.email', 'phi-bot@outlook.fr'])
    subprocess.run(['git', 'checkout', '-B', branch_name], check=True)
    subprocess.run(['git', 'add', '.'], check=True)
    has_changes = subprocess.run(
        ['git', 'diff', '--cached', '--quiet'],
        check=False,
    ).returncode != 0
    if not has_changes:
        print('Aucun changement à proposer en PR.')
        return
    subprocess.run(['git', 'commit', '-m', '🧬 [Cron] Harmonisation vers Ratio Phi'], check=True)
    subprocess.run(['git', 'push', '--force-with-lease', 'origin', branch_name], check=True)

    query = parse.urlencode({'state': 'open', 'head': f'{owner}:{branch_name}', 'base': 'main'})
    with request.urlopen(
        request.Request(
            f'https://api.github.com/repos/{repo}/pulls?{query}',
            headers={
                'Authorization': f'Bearer {token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
            },
        )
    ) as response:
        open_prs = json.loads(response.read().decode('utf-8'))
    if open_prs:
        print(f'PR déjà ouverte sur {branch_name}, mise à jour seulement.')
        return

    payload = json.dumps(
        {
            'title': '✨ Évolution Structurelle (Phi)',
            'head': branch_name,
            'base': 'main',
            'body': 'Rééquilibrage automatique et audit continu des commits non fusionnés.',
        }
    ).encode('utf-8')
    try:
        with request.urlopen(
            request.Request(
                f'https://api.github.com/repos/{repo}/pulls',
                data=payload,
                method='POST',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/vnd.github+json',
                    'Content-Type': 'application/json',
                    'X-GitHub-Api-Version': '2022-11-28',
                },
            )
        ):
            print(f'PR créée sur {branch_name}')
    except error.HTTPError as exc:
        print(f'Échec création PR: {exc.code} {exc.reason}')
if __name__ == '__main__':
    architect = PhiArchitect()
    if architect.run_cycle():
        if os.getenv('GITHUB_ACTIONS'):
            handle_github_automation()
