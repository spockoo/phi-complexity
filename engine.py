import ast
import inspect
import json
import os
import subprocess
from urllib import error, parse, request

class PhiArchitect:

    def __init__(self):
        self.phi = 1.61803398875
        self.filename = inspect.getfile(self.__class__)
        self.complexity_limit = 10

    def clean_merge_markers(self):
        if not os.path.exists(self.filename):
            return
        with open(self.filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        clean_lines = [l for l in lines if not any((l.startswith(m) for m in ['<<<<<<<', '=======', '>>>>>>>']))]
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.writelines(clean_lines)

    def get_complexity(self, node):
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.IfExp)):
                complexity += 1
        return complexity

    def clean_dead_code(self, tree):
        source = ast.unparse(tree)
        new_body = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) > 0 and isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                if var_name.startswith('static_sync_') and source.count(var_name) <= 1:
                    continue
            new_body.append(node)
        tree.body = new_body
        return tree

    def run_cycle(self):
        self.clean_merge_markers()
        with open(self.filename, 'r', encoding='utf-8') as f:
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
        logic = [n for n in nodes if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With))]
        data = [n for n in nodes if isinstance(n, (ast.Assign, ast.Constant, ast.List, ast.Dict))]
        ratio = len(data) / len(logic) if logic else len(data)
        diff = self.phi - ratio
        if abs(diff) < 0.01:
            return False
        if diff > 0:
            new_var_name = f'static_sync_{len(data)}'
            new_data = ast.Assign(targets=[ast.Name(id=new_var_name, ctx=ast.Store())], value=ast.Constant(value=round(diff, 4)))
            tree.body.insert(0, new_data)
        tree = self.clean_dead_code(tree)
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(ast.unparse(tree))
        return True

def handle_github_automation():
    event = os.getenv('GITHUB_EVENT_NAME')
    repo = os.getenv('GITHUB_REPOSITORY')
    token = os.getenv('GITHUB_TOKEN')
    if not token or not repo:
        return
    branch_name = 'evolution/phi-mutation'
    base_branch = 'main'
    owner = repo.split('/')[0]
    subprocess.run(['git', 'config', 'user.name', 'Phi-Architect-Bot'])
    subprocess.run(['git', 'config', 'user.email', 'phi-bot@outlook.fr'])
    if event == 'push':
        return
    try:
        subprocess.run(['git', 'checkout', '-B', branch_name], check=True)
        subprocess.run(['git', 'add', '.'], check=True)
        if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode == 0:
            return
        subprocess.run(['git', 'commit', '-m', '🧬 evolution: mutation structurelle phi'], check=True)
        subprocess.run(['git', 'push', '--force', 'origin', branch_name], check=True)
    except:
        return
    api_url = f'https://://github.com{repo}/pulls'
    try:
        check_req = request.Request(f'{api_url}?state=open&head={owner}:{branch_name}')
        check_req.add_header('Authorization', f'token {token}')
        with request.urlopen(check_req) as r:
            if json.loads(r.read().decode()):
                return
        payload = json.dumps({'title': '✨ Évolution Structurelle (Phi)', 'head': branch_name, 'base': base_branch, 'body': "Mutation automatique basée sur le ratio d'or."}).encode()
        post_req = request.Request(api_url, data=payload, method='POST')
        post_req.add_header('Authorization', f'token {token}')
        post_req.add_header('Content-Type', 'application/json')
        with request.urlopen(post_req):
            pass
    except:
        pass
if __name__ == '__main__':
    architect = PhiArchitect()
    if architect.run_cycle():
        if os.getenv('GITHUB_ACTIONS'):
            handle_github_automation()