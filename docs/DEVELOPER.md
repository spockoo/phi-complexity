# 🔧 Guide Développeur — phi-complexity

> *Comment étendre le framework φ-Meta : backends, règles, et architecture souveraine.*

---

## Architecture Interne

```
phi_complexity/
├── core.py              ← Constantes souveraines (φ, Fibonacci, seuils)
├── analyseur.py         ← Factory + AnalyseurPythonInternal (dissection AST)
├── metriques.py         ← CalculateurRadiance (score 0-100)
├── rapport.py           ← Générateur (Console / Markdown / JSON)
├── cli.py               ← Point d'entrée CLI (phi check, phi report, ...)
├── vault.py             ← Phi Vault — mémoire persistante Obsidian-like
├── canvas.py            ← Export Canvas Obsidian (.canvas)
├── search.py            ← Recherche sémantique dans le vault
├── securite.py          ← Signatures, sanitisation, journal d'audit, SBOM
├── oracle.py            ← Validation de release (Oracle de Radiance)
├── harvest.py           ← Collecte de vecteurs AST anonymisés (IA)
├── akasha.py            ← Matrice Holographique + Registre Akashique
├── gnose.py             ← Sceaux cryptographiques (GCS)
├── backup.py            ← Sauvegarde Maat (protection avant mutation)
├── suture.py            ← Intégration LLM (suture intelligente)
├── autosuture.py        ← Auto-guérison autonome
├── bmad.py              ← Orchestration des 12 agents BMAD
├── impossible.py        ← Opérateur de l'Impossible I(s)
├── commit_risk.py       ← Analyse de risque des commits
├── notebook_helpers.py  ← Intégration Jupyter
├── backends/
│   ├── base.py          ← Interface abstraite AnalyseurBackend
│   ├── python.py        ← Backend Python (délègue à AnalyseurPythonInternal)
│   ├── c_rust_light.py  ← Backend C/C++/Rust (analyse par regex)
│   └── asm_light.py     ← Backend Assembleur (x86, ARM, RISC-V)
└── sentinel/            ← Système de détection comportementale
    ├── bayesian.py      ← Analyse bayésienne
    ├── behavior.py      ← Détection comportementale
    ├── host.py          ← Analyse de l'hôte
    ├── response.py      ← Réponse aux menaces
    └── telemetry.py     ← Télémétrie
```

---

## Créer un Nouveau Backend

### 1. Interface `AnalyseurBackend`

Tout backend doit hériter de `AnalyseurBackend` et implémenter `analyser()` :

```python
from phi_complexity.backends.base import AnalyseurBackend
from phi_complexity.analyseur import ResultatAnalyse, MetriqueFonction, Annotation


class MonBackend(AnalyseurBackend):
    """Backend pour le langage X."""

    def analyser(self) -> ResultatAnalyse:
        # self.fichier contient le chemin du fichier à analyser
        with open(self.fichier, "r", encoding="utf-8") as f:
            lignes = f.readlines()

        resultat = ResultatAnalyse(fichier=self.fichier)
        resultat.nb_lignes_total = len(lignes)

        # ... analyse du code ...
        # Peupler resultat.fonctions avec des MetriqueFonction
        # Peupler resultat.annotations avec des Annotation

        return resultat
```

### 2. Structures de Données

#### `MetriqueFonction`
```python
@dataclass
class MetriqueFonction:
    nom: str              # Nom de la fonction
    ligne: int            # Numéro de ligne
    complexite: int       # Nombre de nœuds AST / instructions
    nb_args: int          # Nombre d'arguments
    nb_lignes: int        # Longueur en lignes
    profondeur_max: int   # Imbrication maximale
    distance_fib: float   # Distance au Fibonacci le plus proche (/ φ)
    phi_ratio: float      # complexite / moyenne (idéal: φ = 1.618)
```

#### `Annotation`
```python
@dataclass
class Annotation:
    ligne: int        # Numéro de ligne
    message: str      # Message d'alerte
    niveau: str       # 'INFO', 'WARNING', 'CRITICAL'
    extrait: str      # Ligne de code concernée
    categorie: str    # 'LILITH', 'SUTURE', 'SOUVERAINETE', 'FIBONACCI', 'CYCLOMATIQUE'
```

### 3. Enregistrer le Backend

#### Dans `backends/__init__.py` :
```python
from .mon_backend import MonBackend
# Ajouter à __all__
```

#### Dans `analyseur.py` (`_selectionner_backend`) :
```python
if ext in ("xx",):
    return MonBackend(self.fichier)
```

#### Dans `cli.py` (`_EXTENSIONS_SUPPORTEES`) :
Ajouter l'extension à la constante :
```python
_EXTENSIONS_SUPPORTEES = (".py", ".c", ".cpp", ".h", ".hpp", ".rs", ".asm", ".s", ".xx")
```

### 4. Tests

Suivre le pattern de `tests/test_backends.py` :
- Créer des fichiers temporaires avec du code source de test
- Vérifier les fonctions détectées, les annotations générées, l'oudjat
- Nettoyer les fichiers temporaires dans `finally`

---

## API Programmatique

### Audit Simple
```python
from phi_complexity import auditer

metriques = auditer("mon_fichier.py")
print(metriques["radiance"])           # Score 0-100
print(metriques["statut_gnostique"])   # HERMÉTIQUE ✦ / EN ÉVEIL ◈ / DORMANT ░
print(metriques["oudjat"])             # Fonction dominante
```

### Vault (Mémoire Persistante)
```python
from phi_complexity import PhiVault, auditer

vault = PhiVault()
metriques = auditer("mon_fichier.py")

# Détecter les régressions
regressions = vault.detecter_regressions(metriques)

# Archiver l'audit
vault.enregistrer_audit(metriques)

# Consulter l'index
index = vault.consulter_index()

# Lire une note
note = vault.lire_note("mon_fichier.py")

# Générer le graphe
print(vault.generer_graph_ascii())     # Vue ASCII
print(vault.generer_graph())           # Format DOT
```

### Canvas (Export Obsidian)
```python
from phi_complexity import PhiCanvas, auditer

canvas = PhiCanvas()
for fichier in ["a.py", "b.py"]:
    metriques = auditer(fichier)
    canvas.ajouter_fichier(metriques)

canvas.exporter(".phi/architecture.canvas")
```

### Search (Recherche Sémantique)
```python
from phi_complexity import PhiSearch

search = PhiSearch()

# Par radiance
resultats = search.chercher_par_radiance(minimum=60, maximum=85)

# Par statut
resultats = search.chercher_par_statut("DORMANT")

# Par catégorie d'annotation
resultats = search.chercher_annotations("LILITH")

# Rapport
print(search.rapport_recherche(resultats, "Ma recherche"))
```

### Sécurité
```python
from phi_complexity.securite import (
    signer_rapport, verifier_signature,
    valider_chemin_fichier, JournalAudit,
    generer_sbom, exporter_sbom,
)

# Signer un rapport
signature = signer_rapport(contenu_rapport)
assert verifier_signature(contenu_rapport, signature)

# Valider un chemin
assert valider_chemin_fichier("mon_fichier.py")

# Journal d'audit
journal = JournalAudit()
journal.enregistrer("AUDIT", {"fichier": "test.py", "radiance": 85.0})
assert journal.verifier_integrite()

# SBOM
exporter_sbom(".phi/sbom.json")
```

---

## Les 5 Règles de Codage Souverain

| # | Règle | Catégorie | Seuils |
|---|-------|-----------|--------|
| I | **Anti-Entropie (LILITH)** | Boucles imbriquées | Max 2 niveaux |
| II | **RAII (Gestion de Ressources)** | `open()` sans `with` | Toujours `with` |
| III | **Fibonacci (Taille Naturelle)** | Longueur des fonctions | ≤ 34 lignes |
| IV | **Hermétisme (Pureté d'Interface)** | Nombre d'arguments | 3-5 max |
| V | **Complexité Cyclomatique** | Chemins de contrôle | CC ≤ 8 (warn > 13) |

### Ajouter une Nouvelle Règle

1. Définir les constantes dans `core.py`
2. Implémenter la détection dans `analyseur.py` (méthode `_verifier_*`)
3. Créer les `Annotation` avec la bonne `categorie`
4. Ajouter le poids dans `metriques.py` (`_calculer_penalite_annotations`)
5. Écrire les tests unitaires

---

## Conventions du Projet

- **Zéro dépendances** : Uniquement la stdlib Python
- **Python 3.9+** : Compatibilité maximale
- **Type hints** : `mypy --strict` (sauf tests)
- **Formatage** : Black (88 colonnes) + Ruff
- **Tests** : pytest avec coverage ≥ 89%
- **Commentaires** : En français, style φ-Meta

---

*Ancré dans la Bibliothèque Céleste — Framework φ-Meta de Tomy Verreault — 2026*
