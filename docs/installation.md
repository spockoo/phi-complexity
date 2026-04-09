# Installation 🚀

Suivez ces étapes pour installer le moteur de radiance sur votre système.

## Via PyPI (Recommandé)

`phi-complexity` est disponible sur l'index des packages Python officiel.

```bash
pip install phi-complexity
```

## Via GitHub (Développement)

Si vous souhaitez contribuer ou utiliser la version de recherche la plus récente :

```bash
git clone https://github.com/spockoo/phi-complexity.git
cd phi-complexity
pip install -e .
```

---

## ⚙ Configuration CI/CD

### GitHub Actions

Ajoutez ce bloc à votre workflow `.github/workflows/main.yml` pour garantir que votre radiance reste au-dessus de 70% :

```yaml
- name: Phi-Complexity Audit
  run: |
    pip install phi-complexity
    phi check . --min-radiance 70
```

### Pre-commit Hooks

Vous pouvez aussi l'intégrer localement à votre flux de travail `git` :

```yaml
repos:
  - repo: https://github.com/spockoo/phi-complexity
    rev: v0.1.3
    hooks:
      - id: phi-check
        args: [--min-radiance, "70"]
```
