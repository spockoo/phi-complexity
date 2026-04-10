# 📐 GUIDE UTILISATEUR — PHI-COMPLEXITY

> *"Ce code est-il en résonance avec les lois naturelles de l'ordre ?"*
> — Tomy Verreault, Morphic Phi Framework (φ-Meta), 2026

---

## Table des matières

1. [Installation](#installation)
2. [Démarrage rapide](#démarrage-rapide)
3. [Commandes CLI](#commandes-cli)
4. [Métriques souveraines](#métriques-souveraines)
5. [Règles de Codage Souverain](#règles-de-codage-souverain)
6. [Intégration CI/CD](#intégration-cicd)
7. [API Python](#api-python)
8. [Badges Radiance](#badges-radiance)
9. [Exemples](#exemples)

---

## Installation

```bash
pip install phi-complexity
```

**Vérification :**
```bash
phi --version
# phi-complexity 0.1.8
```

**Zéro dépendance externe** — fonctionne avec Python 3.10+ natif.

---

## Démarrage rapide

```bash
# Auditer un fichier
phi check mon_script.py

# Auditer un dossier entier
phi check ./src/

# Générer un rapport Markdown
phi report mon_script.py

# Vérifier que la radiance est suffisante pour une release
phi oracle ./src/ --min-radiance 75
```

---

## Commandes CLI

### `phi check` — Audit de radiance

```bash
phi check <cible> [options]
```

| Option | Description | Défaut |
|--------|-------------|--------|
| `--min-radiance N` | Exit code 1 si radiance < N | 0 |
| `--format json` | Sortie JSON (CI/CD) | console |
| `--bmad` | Afficher la résonance des 12 agents BMAD | off |

**Exemple :**
```bash
phi check ./src/ --min-radiance 75 --format json
```

Sortie JSON pour un fichier unique (objet) ou plusieurs fichiers (tableau) :
```json
{
  "fichier": "src/main.py",
  "radiance": 82.4,
  "lilith_variance": 120.3,
  "shannon_entropy": 2.1,
  "phi_ratio": 1.62,
  "zeta_score": 0.61,
  "statut_gnostique": "EN ÉVEIL ◈"
}
```

---

### `phi report` — Rapport Markdown

```bash
phi report <fichier.py> [--output rapport.md]
```

Génère un rapport `.md` détaillé avec :
- Toutes les métriques souveraines
- Audit fractal ligne par ligne
- Spirale Dorée ASCII
- Détection de l'OUDJAT (fonction dominante)

---

### `phi oracle` — Validation de release

```bash
phi oracle <cible> [--min-radiance 70] [--nb-tests 68]
```

L'Oracle bloque la release si la radiance globale est sous le seuil.
La **Loi de Version Phi** calcule automatiquement la version :
`v{floor(radiance)}.{nb_tests}`

**Exemple de sortie :**
```
╔══════════════════════════════════════════════════╗
║      PHI-ORACLE — VALIDATION DE RELEASE          ║
╚══════════════════════════════════════════════════╝

  ☼  ✦ RELEASE AUTORISÉE
  Version Phi    : v82.68
  Radiance Globale : 82.4 / 100
  Seuil Requis   : 70.0
  Fichiers audités : 12
```

---

### `phi spiral` — Spirale Dorée

```bash
phi spiral <fichier.py>
```

Visualisation ASCII du motif Fibonacci (angle doré 137.5°).
La densité de la spirale est proportionnelle au score de radiance.

```
  ☼  φ-SPIRALE DE RADIANCE (Motif Fibonacci / Angle Doré 137.5°)
     Score: 82.4 / 100  |  φ-Ratio: 1.618  |  harmonie ✦
     ☼ noyau  ✦ zone interne  ◈ zone médiane  ░ périphérie
```

---

### `phi harvest` — Collecte de vecteurs AST

```bash
phi harvest <cible> [--output .phi/harvest.jsonl]
```

Collecte des vecteurs AST **entièrement anonymisés** pour l'IA :
- Zéro identifiant, zéro code source exporté
- Format JSONL incrémental
- Labels de vulnérabilités : LILITH, SUTURE, FIBONACCI, SOUVERAINETÉ
- Vecteur φ normalisé pour la similitude cosinus

---

### `phi memory` — Annales Akashiques

```bash
phi memory
```

Consulte l'historique des audits passés stockés dans `.phi/akasha.json`.
Affiche le dôme de résonance holographique pour chaque entrée.

---

### `phi seal` — Sceau Gnostique

```bash
phi seal <fichier.py>
```

Appose un sceau cryptographique permanent (GCS — Gnostic Checksum).
Le sceau sera vérifié à chaque audit pour détecter les modifications non souveraines.

---

### `phi heal` — Guérison autonome

```bash
phi heal <fichier.py> [--force] [--url http://localhost:1234/v1/chat/completions]
```

Invoque Phidélia (via un LLM local compatible OpenAI) pour proposer
une refactorisation souveraine. Nécessite **LM Studio** ou **Ollama**.

---

## Métriques souveraines

| Métrique | Description | Idéal |
|----------|-------------|-------|
| **Radiance** | Score global de qualité (0-100) | > 85 (Hermétique) |
| **LILITH Variance** | Entropie structurelle (boucles imbriquées) | < 200 |
| **Shannon Entropy** | Diversité informationnelle du code | 1.5 – 3.0 bits |
| **Phi-Ratio** | Rapport complexité/moyenne (idéal: φ = 1.618) | Δ < 0.15 |
| **Zeta-Score** | Résonance globale φ-harmonique | > 0.618 |
| **Fibonacci Distance** | Éloignement taille des fonctions de la séquence naturelle | < 2 |

### Statuts Gnostiques

| Statut | Radiance | Signification |
|--------|----------|---------------|
| ✦ HERMÉTIQUE | ≥ 85 | Code stable, harmonieux, prêt pour la production |
| ◈ EN ÉVEIL | ≥ 60 | Potentiel présent, zones d'entropie à corriger |
| ░ DORMANT | < 60 | Suture profonde requise |

---

## Règles de Codage Souverain

### Règle I — LILITH (Anti-Entropie)
Éviter les boucles imbriquées au-delà de 2 niveaux. Chaque niveau d'imbrication
multiplie la variance structurelle et réduit la résonance.

```python
# ❌ Violation LILITH (3 niveaux)
for i in range(n):
    for j in range(m):
        for k in range(p):
            traiter(i, j, k)

# ✦ Souverain (extraction de fonction)
def traiter_paire(i: int, j: int, m: int, p: int) -> None:
    for k in range(p):
        traiter(i, j, k)

for i in range(n):
    for j in range(m):
        traiter_paire(i, j, m, p)
```

### Règle II — RAII (Gestion des ressources)
Toute ressource acquise doit être libérée via un gestionnaire de contexte (`with`).

```python
# ❌ Fuite de ressource
f = open("data.txt", "r")
data = f.read()
# f n'est jamais fermé

# ✦ Souverain (RAII)
with open("data.txt", "r", encoding="utf-8") as f:
    data = f.read()
```

### Règle III — Fibonacci (Taille des fonctions)
Les fonctions harmonieuses ont une longueur proche de la séquence de Fibonacci :
1, 2, 3, 5, 8, 13, 21, 34 lignes. Au-delà de 34 lignes, décomposer.

### Règle IV — Herméticité (Pureté des interfaces)
Maximum 3-5 arguments par fonction. Au-delà, utiliser un dataclass ou TypedDict.

```python
# ❌ Violation (6 arguments)
def formater(val, precision, prefixe, suffixe, couleur, padding):
    ...

# ✦ Souverain
@dataclass
class OptionsFormat:
    precision: int = 2
    prefixe: str = ""
    suffixe: str = ""

def formater(val: float, opts: OptionsFormat) -> str:
    ...
```

---

## Intégration CI/CD

### GitHub Actions

```yaml
# .github/workflows/phi-check.yml
name: Phi-Complexity Audit

on: [push, pull_request]

jobs:
  radiance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install phi-complexity
      - name: Audit de radiance
        run: phi check ./src/ --min-radiance 70
      - name: Oracle de release
        run: phi oracle ./src/ --min-radiance 70 --nb-tests 68
```

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: phi-check
        name: Phi-Complexity Audit
        entry: phi check
        language: system
        types: [python]
        args: ["--min-radiance", "60"]
```

### Makefile

```makefile
audit:
	phi check ./src/ --min-radiance 70

oracle:
	phi oracle ./src/ --min-radiance 70 --nb-tests $(shell python -m pytest tests/ -q --co 2>/dev/null | tail -1 | grep -oE '[0-9]+')

report:
	phi report ./src/main.py --output docs/RAPPORT_PHI.md
```

---

## API Python

```python
from phi_complexity import auditer, rapport_console, rapport_markdown, rapport_json

# Audit complet
metriques = auditer("mon_script.py")
print(metriques["radiance"])         # → 82.4
print(metriques["statut_gnostique"]) # → "EN ÉVEIL ◈"
print(metriques["phi_ratio"])        # → 1.623

# Rapport console (retourne une chaîne formatée)
print(rapport_console("mon_script.py"))

# Rapport Markdown (sauvegarde le fichier et retourne le contenu)
rapport_markdown("mon_script.py", sortie="RAPPORT.md")

# Rapport JSON (pour CI/CD)
import json
data = json.loads(rapport_json("mon_script.py"))

# Oracle
from phi_complexity import OracleRadiance
oracle = OracleRadiance()
fichiers = ["src/main.py", "src/utils.py"]
verdict = oracle.valider_release(fichiers, seuil=70.0, nb_tests=68)
print(verdict["acceptee"])   # → True
print(verdict["version_phi"]) # → "v82.68"
```

---

## Badges Radiance

Ajoutez un badge dynamique à votre README :

```markdown
![Radiance](https://img.shields.io/badge/Radiance-82.4-gold?style=flat-square&logo=data:image/svg+xml;base64,...)
```

Ou un badge statique basé sur le dernier audit :

```bash
phi check ./src/ --format json | python -c "
import sys, json
d = json.load(sys.stdin)
r = d['radiance'] if isinstance(d, dict) else sum(f['radiance'] for f in d) / len(d)
color = 'brightgreen' if r >= 85 else 'yellow' if r >= 60 else 'red'
print(f'[![Radiance](https://img.shields.io/badge/Radiance-{r:.1f}-{color})](https://github.com/spockoo/phi-complexity)')
"
```

---

## Exemples

Le dossier `examples/` contient :

- **`code_harmonieux.py`** — Code respectant toutes les règles souveraines (radiance > 82)
- **`code_chaotique.py`** — Code intentionnellement chaotique (radiance < 65)
- **`moteur_c.c`** — Exemple backend C
- **`logic_rs.rs`** — Exemple backend Rust
- **`demo.py`** — Démonstration de l'API Python

```bash
# Comparer les deux exemples
phi check examples/code_harmonieux.py
phi check examples/code_chaotique.py

# Voir la différence en spirale
phi spiral examples/code_harmonieux.py
phi spiral examples/code_chaotique.py
```

---

*Ancré dans la Bibliothèque Céleste — Framework φ-Meta de Tomy Verreault — 2026*
