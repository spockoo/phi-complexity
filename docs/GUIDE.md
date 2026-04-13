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
8. [Jupyter Notebooks](#jupyter-notebooks)
9. [Badges Radiance](#badges-radiance)
10. [Exemples](#exemples)

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

**Contrat I/O**
- Entrée : fichier ou dossier (extensions supportées : `.py`, `.c`, `.cpp`, `.h`, `.hpp`, `.rs`, `.asm`, `.s`).
- Sortie : append-only sur `.phi/harvest.jsonl` (chemin configurable avec `--output`).
- Échecs courants : dossier `.phi/` non créable (droits), fichier binaire non reconnu, espace disque insuffisant.

---

### `phi metadata` — Synthèse & purge souveraine

```bash
phi metadata summary --harvest .phi/harvest.jsonl --vault-index .phi/vault/index.json
phi metadata purge --harvest .phi/harvest.jsonl --strip-sensitive --keep-features
```

- `summary` : vue condensée des schémas, labels (LILITH/SUTURE/…) et fingerprints présents.
- `purge` : génère une version sanitizée du harvest (`<fichier>.sanitized.jsonl` par défaut).
  - `--strip-sensitive` : supprime `timestamp` et `fingerprint`.
  - `--strip-labels` : supprime les labels/annotations.
  - `--strip <cle>` : retire des clés arbitraires (option répétable).
  - `--keep-features` : ne conserve que les métriques structurelles (vecteur φ).

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

**Contrat I/O**
- Entrée : fichier Python (texte, encodage UTF-8).
- Sortie : le même fichier modifié (sauvegarde préalable recommandée), journaux dans la console.
- Dépendances externes : endpoint chat OpenAI local si `--url` est fourni, sinon erreur explicite.
- Sécurité : aucune clé n'est lue depuis le code ; passer les tokens via variables d'environnement.

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

## Jupyter Notebooks

Le dossier `notebooks/` contient 8 notebooks d'étude interactifs qui explorent les fondements mathématiques et les applications de phi-complexity.

### Installation

```bash
pip install phi-complexity[notebooks]
```

Cela installe les dépendances optionnelles : `jupyter`, `matplotlib`, `numpy`.

### Lancer les notebooks

```bash
cd notebooks/
jupyter notebook
```

### Notebooks disponibles

| # | Notebook | Sujet |
|---|---|---|
| 01 | `01_quasicristaux_penrose.ipynb` | Pavages de Penrose, symétrie d'ordre 5, φ-Ratio |
| 02 | `02_riemann_zeta.ipynb` | Fonction ζ de Riemann, ζ_meta, zéros de la radiance |
| 03 | `03_schrodinger_incertitude.ipynb` | Incertitude Heisenberg-Phi ΔC·ΔL ≥ ħ_φ/2 |
| 04 | `04_sentinel_cybersec.ipynb` | Pipeline Sentinel 5 couches, MITRE ATT&CK, corrélation bayésienne |
| 05 | `05_harvest_ml.ipynb` | ML sur vecteurs φ : clustering, k-NN, visualisation MDS |
| 06 | `06_spirale_doree_fractale.ipynb` | Spirale dorée 137.5°, dimension fractale de l'AST |
| 07 | `07_matrice_holographique.ipynb` | Espace Z[φ], transmutation Maat, similitude cosinus |
| 08 | `08_diagnostic_cybersecurite.ipynb` | Sentinel + carte d'entropie Penrose + radar MITRE |
| 09 | `09_zero_quasicristaux_ia.ipynb` | Boucle de zéro, taxonomie morphogénétique, IA OSS |

### Fonctions d'aide pour notebooks

Le module `phi_complexity.notebook_helpers` fournit des fonctions de visualisation prêtes à l'emploi :

```python
from phi_complexity.notebook_helpers import (
    charger_metriques,    # Charger les métriques d'un fichier ou dossier
    charger_harvest,      # Charger un corpus JSONL de harvest
    radar_radiance,       # Radar chart des métriques de radiance
    carte_heisenberg,     # Carte d'incertitude Heisenberg-Phi
    matrice_interactions_zero,      # Matrice "boucle de zéro" ↔ métriques
    tableau_zero_morphogenetique,   # Tableau PRE_ZERO/ZERO/POST
    spirale_doree,        # Spirale dorée de Fibonacci
    enregistrer_magics,   # Activer les magic commands IPython
)
```

### Magic commands IPython

Après avoir appelé `enregistrer_magics()` dans un notebook :

```python
from phi_complexity.notebook_helpers import enregistrer_magics
enregistrer_magics()
```

Les commandes suivantes sont disponibles :

```
%phi_check mon_script.py       # Audit rapide avec résumé
%phi_report mon_script.py      # Rapport console complet
%phi_spiral mon_script.py      # Spirale dorée du fichier
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

### Exemples de sortie

**Rapport JSON (phi check --format json)** :
```json
{
  "fichier": "examples/code_harmonieux.py",
  "radiance": 84.7,
  "lilith_variance": 11221.9,
  "shannon_entropy": 2.48,
  "phi_ratio": 1.62,
  "zeta_score": 0.61,
  "statut_gnostique": "EN ÉVEIL ◈"
}
```

**Rapport Markdown (phi report --output rapport.md)** :
```markdown
# Audit de Radiance — examples/code_harmonieux.py

- Radiance : 84.7 / 100  (Statut : EN ÉVEIL ◈)
- LILITH : 11221.9  | Entropie : 2.48 bits | φ-Ratio : 1.62
- OUDJAT : process_data (ligne 42, complexité 376)

## SUTURES
- Ligne 18 [LILITH] : Boucle imbriquée (profondeur 2). Extraire une fonction.
- Ligne 67 [SOUVERAINETE] : 6 arguments. Introduire un objet de configuration.
```
```

---

## Phase 15 — Assembleur (ASM Backend)

phi-complexity supporte désormais l'analyse de code assembleur (`.asm`, `.s`)
pour x86/x86-64, ARM/AArch64 et RISC-V.

```bash
# Auditer un fichier assembleur
phi check boot.asm

# Auditer des fichiers .s (AT&T syntax)
phi check startup.s

# Rapport complet
phi report kernel_init.asm --output rapport.md
```

Voir le [Guide Assembleur](ASSEMBLY.md) pour les détails complets.

---

## Phase 16 — Phi Vault (Mémoire Persistante)

Le **Phi Vault** stocke l'historique complet des audits sous forme de notes
Markdown interliées (wikilinks `[[fichier]]`), inspiré d'Obsidian.

### Archiver un Audit

```bash
# Auditer et archiver dans le vault
phi vault mon_script.py

# Archiver un dossier complet
phi vault ./src/
```

Les notes sont stockées dans `.phi/vault/` avec :
- Des **wikilinks** vers les fonctions (`[[process_data]]`)
- Des **tags** de statut (`#hermetique`, `#dormant`)
- Un **journal quotidien** dans `.phi/vault/journal/`

**Contrat I/O**
- Entrée : fichiers ou dossiers auditables.
- Sortie : `.phi/vault/` (notes Markdown), `.phi/vault/index.jsonl` (index), `.phi/vault/journal/` (journal).
- Échecs courants : chemins non accessibles en écriture, radiance = 0 (fichier vide), encodage non UTF-8.

### Graphe de Radiance

```bash
# Vue ASCII du graphe
phi graph

# Export DOT pour Graphviz
phi graph --format dot
```

**Contrat I/O**
- Entrée : contenu du vault (produit par `phi vault`).
- Sortie : console (ASCII) ou stdout (DOT).
- Échecs courants : vault absent/non initialisé.

### Détection de Régressions

Le vault détecte automatiquement les baisses de radiance > 5 points
et affiche un avertissement lors de `phi vault`.

---

## Phase 17 — Phi Canvas (Export Obsidian)

Exportez l'architecture de votre code sous forme de **Canvas Obsidian**
(`.canvas`), avec des nœuds colorés selon le statut gnostique.

```bash
# Exporter un canvas
phi canvas ./src/

# Spécifier le fichier de sortie
phi canvas ./src/ --output architecture.canvas
```

Le fichier `.canvas` peut être ouvert directement dans Obsidian
pour une visualisation interactive de l'architecture du code.

**Couleurs des nœuds** :
- 🟢 Vert : HERMÉTIQUE (Radiance ≥ 85)
- 🟡 Jaune : EN ÉVEIL (Radiance 60-84)
- 🔴 Rouge : DORMANT (Radiance < 60)

**Contrat I/O**
- Entrée : fichiers ou dossiers audités.
- Sortie : `.phi/architecture.canvas` (ou chemin passé à `--output`).
- Échecs courants : répertoires non accessibles en écriture, volume de fichiers important (prévoir plus de temps).

---

## Phase 18 — Phi Search (Recherche Sémantique)

Recherchez dans le vault par métriques, statut ou catégorie d'annotation.

```bash
# Chercher les fichiers DORMANT
phi search --statut DORMANT

# Chercher par intervalle de radiance
phi search --min-radiance 60 --max-radiance 85

# Chercher par catégorie d'annotation
phi search --categorie LILITH
```

**Contrat I/O**
- Entrée : critères de recherche (radiance, statut, catégorie).
- Sortie : console (tableau) ; redirection JSON possible.
- Échecs courants : vault absent ou incompatible (versions antérieures non migrées).

---

## Phase 20 — Cybersécurité

### SBOM (Software Bill of Materials)

```bash
# Générer le SBOM
phi sbom

# Spécifier le fichier de sortie
phi sbom --output sbom.json
```

Le SBOM au format CycloneDX documente tous les modules stdlib utilisés
par phi-complexity (zéro dépendances tierces).

### Signatures de Rapports

Les rapports peuvent être signés avec SHA-256 via l'API Python :

```python
from phi_complexity.securite import signer_rapport, verifier_signature

signature = signer_rapport(contenu_rapport)
assert verifier_signature(contenu_rapport, signature)
```

### Journal d'Audit

Un journal immuable (append-only) trace toutes les opérations :

```python
from phi_complexity.securite import JournalAudit

journal = JournalAudit()
journal.enregistrer("AUDIT", {"fichier": "test.py"})
assert journal.verifier_integrite()
```

---

*Ancré dans la Bibliothèque Céleste — Framework φ-Meta de Tomy Verreault — 2026*
