import ast
import inspect
import os
import subprocess

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
    """Gère le push direct ou la création de PR via API GitHub."""
    event = os.getenv('GITHUB_EVENT_NAME')
    repo = os.getenv('GITHUB_REPOSITORY')
    token = os.getenv('GITHUB_TOKEN')
    if not token or not repo:
        print('Infos GitHub manquantes.')
        return
    subprocess.run(['git', 'config', 'user.name', 'Phi-Architect-Bot'])
    subprocess.run(['git', 'config', 'user.email', 'phi-bot@outlook.fr'])
    if event in ['schedule', 'workflow_dispatch']:
        branch_name = f"phi-evolution-{os.getenv('GITHUB_RUN_ID')}"
        subprocess.run(['git', 'checkout', '-b', branch_name])
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', '🧬 [Cron] Harmonisation vers Ratio Phi'])
        subprocess.run(['git', 'push', 'origin', branch_name])
        pr_payload = f'{{"title":"✨ Évolution Structurelle (Phi)","head":"{branch_name}","base":"main","body":"Rééquilibrage automatique."}}'
        api_url = f'https://github.com{repo}/pulls'
        subprocess.run(['curl', '-X', 'POST', '-H', f'Authorization: token {token}', '-H', 'Accept: application/vnd.github.v3+json', api_url, '-d', pr_payload])
        print(f'PR créée sur {branch_name}')
    else:
        print('Mutation effectuée pour le workflow de push.')
if __name__ == '__main__':
    architect = PhiArchitect()
    if architect.run_cycle():
        if os.getenv('GITHUB_ACTIONS'):
            handle_github_automation()