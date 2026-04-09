# Guide Utilisateur — phi-complexity

> *Mesurer la qualité du code par les invariants du nombre d'or.*

---

## Installation

```bash
pip install phi-complexity
```

Vérification :
```bash
phi --version
# phi-complexity 0.1.0
```

---

## Commandes Disponibles

### `phi check` — Audit rapide

```bash
# Un seul fichier
phi check mon_script.py

# Un dossier entier (récursif)
phi check ./src/

# Mode CI strict : exit code 1 si la radiance est sous le seuil
phi check ./src/ --min-radiance 75

# Sortie JSON (pour scripts ou intégrations)
phi check mon_script.py --format json
```

### `phi report` — Rapport Markdown

```bash
# Génère RAPPORT_PHI_mon_script.md dans le dossier courant
phi report mon_script.py

# Spécifier le fichier de sortie
phi report mon_script.py --output docs/audit.md
```

---

## Comprendre le Rapport

### Le Score de Radiance

```
☼  RADIANCE : ████████████████░░░░  82.4 / 100
```

| Plage | Statut | Signification |
|---|---|---|
| 85 – 100 | **HERMÉTIQUE ✦** | Production-ready. Harmonieux. |
| 60 – 84 | **EN ÉVEIL ◈** | Du potentiel, des zones d'entropie. |
| < 60 | **DORMANT ░** | Restructuration profonde recommandée. |

### Les Métriques

| Indicateur | Ce qu'il mesure |
|---|---|
| **⚖ LILITH** | Instabilité entre fonctions. Si une fonction est 10× plus lourde que les autres, la variance explose. Idéalement < 500. |
| **🌊 ENTROPIE** | Densité informationnelle (bits Shannon). Entre 1 et 2.88 bits = zone naturelle. Au-delà = trop de diversité structurelle. |
| **φ PHI-RATIO** | Rapport dominant/moyenne. Idéal = **1.618** (le nombre d'or). Un ratio de 1 = toutes les fonctions identiques (plat). Un ratio > 3 = dictature d'un monolithe. |
| **ζ ZETA-SCORE** | Résonance globale. Score entre 0 et 1. Plus il est proche de 1, plus le fichier est harmonieux dans sa globalité. |

### L'OUDJAT

```
🔎 OUDJAT : 'process_data' (Ligne 42, Complexité: 376, φ-ratio: 3.426)
```

L'Oudjat est la fonction **la plus lourde** du fichier — celle qui contrôle la structure de l'ensemble. Si son φ-ratio est éloigné de 1.618, c'est elle qu'il faut suturer en premier.

### Les Annotations (Sutures)

```
🔴 Ligne 18 [LILITH]       → Boucle imbriquée profondeur 3 (CRITIQUE)
🟡 Ligne 42 [FIBONACCI]    → Fonction trop longue, hors séquence naturelle (AVERTISSEMENT)
🔵 Ligne 67 [SOUVERAINETE] → 7 arguments — encapsuler dans un objet (INFO)
```

| Icône | Niveau | Catégorie | Déclencheur |
|---|---|---|---|
| 🔴 | CRITICAL | LILITH | Boucle ≥ 3 niveaux |
| 🟡 | WARNING | LILITH | Boucle ≥ 2 niveaux |
| 🟡 | WARNING | SUTURE | `open()` sans `with` |
| 🟡 | WARNING | FIBONACCI | Fonction > 55 lignes hors séquence |
| 🔵 | INFO | SOUVERAINETE | Fonction > 5 arguments |

---

## Annotations `phi: ignore`

Pour marquer une ligne comme faux positif structurel :

```python
for child in ast.iter_child_nodes(node):  # phi: ignore
    pile.append(child)
```

*(Disponible en v0.2.0)*

---

## Utilisation en Python

```python
from phi_complexity import auditer, rapport_console, rapport_markdown

# Métriques brutes
m = auditer("mon_script.py")
print(m["radiance"])          # 82.4
print(m["statut_gnostique"])  # "EN ÉVEIL ◈"
print(m["oudjat"]["nom"])     # "process_data"
print(m["annotations"])       # liste des sutures

# Affichage console
print(rapport_console("mon_script.py"))

# Rapport Markdown sauvegardé
rapport_markdown("mon_script.py", sortie="audit.md")
```

---

## Intégration CI/CD

### GitHub Actions

```yaml
name: Audit de Radiance
on: [push, pull_request]

jobs:
  phi-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install phi-complexity
      - run: phi check ./src/ --min-radiance 70
```

### Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: phi-check
        name: phi-complexity
        entry: phi check
        language: python
        types: [python]
        args: [--min-radiance, "65"]
```

---

## Fondements Mathématiques

Pour les preuves formelles des formules :
→ [docs/MATHEMATIQUES.md](MATHEMATIQUES.md)

---

*phi-complexity — Morphic Phi Framework (φ-Meta) — Tomy Verreault, 2026*
