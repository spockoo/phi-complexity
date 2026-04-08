# phi-complexity

> *Code quality metrics based on Golden Ratio (φ) mathematical invariants*

[![PyPI version](https://img.shields.io/pypi/v/phi-complexity.svg)](https://pypi.org/project/phi-complexity/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/spockoo/phi-complexity/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/tests-26%20passed-brightgreen)](https://github.com/spockoo/phi-complexity/tree/main/tests)

`phi-complexity` is the **first code quality library** that measures the health of your Python code using **universal mathematical invariants** derived from the Golden Ratio (φ = 1.618...).

Unlike `pylint` (cultural rules) or `radon` (McCabe metrics), `phi-complexity` answers:

> *"Is this code in resonance with the natural laws of order, or is it collapsing under its own entropy?"*

---

## ⚡ Quick Start

```bash
pip install phi-complexity
```

```bash
# Audit a file
phi check my_script.py

# Audit a folder
phi check ./src/

# Generate a Markdown report
phi report my_script.py --output report.md

# CI/CD strict mode (exit 1 if radiance < 75)
phi check ./src/ --min-radiance 75
```

### Python API

```python
from phi_complexity import auditer, rapport_console, rapport_markdown

# Get metrics as a dict
metrics = auditer("my_script.py")
print(metrics["radiance"])          # → 82.4
print(metrics["statut_gnostique"])  # → "EN ÉVEIL ◈"
print(metrics["oudjat"])            # → {"nom": "process_data", "ligne": 42, ...}

# Print console report
print(rapport_console("my_script.py"))

# Save Markdown report
rapport_markdown("my_script.py", sortie="report.md")
```

---

## 📊 Metrics

| Metric | Description | Mathematical basis |
|---|---|---|
| **Radiance Score** | Global quality score (0–100) | `100 - f(Lilith) - g(H) - h(Anomalies) - i(Fib)` |
| **Variance de Lilith** | Structural instability | Population variance of function complexities |
| **Shannon Entropy** | Information density | `H = -Σ p·log₂(p)` |
| **φ-Ratio** | Dominant function ratio | `max_complexity / mean` → should tend toward φ |
| **Fibonacci Distance** | Natural size alignment | `Σ|n_i - Fib_k| / φ` |
| **Zeta-Score** | Global resonance | `ζ_meta(functions, φ)` converging series |

### Gnostic Status Levels

| Score | Status | Meaning |
|---|---|---|
| ≥ 85 | **HERMÉTIQUE ✦** | Stable, harmonious, production-ready |
| 60–84 | **EN ÉVEIL ◈** | Potential exists, some entropy zones |
| < 60 | **DORMANT ░** | Deep restructuring recommended |

---

## 🔍 Sample Output

```
╔══════════════════════════════════════════════════╗
║      PHI-COMPLEXITY — AUDIT DE RADIANCE          ║
╚══════════════════════════════════════════════════╝

  📄 Fichier : my_script.py
  📅 Date    : 2026-04-08 17:11

  ☼  RADIANCE     : ██████████████░░░░░░  72.6 / 100
  ⚖  LILITH       : 11221.9  (Structural variance)
  🌊 ENTROPIE     : 2.48 bits  (Shannon)
  ◈  PHI-RATIO    : 3.43  (ideal: φ = 1.618, Δ=1.81)
  ζ  ZETA-SCORE   : 0.3656  (Global resonance)

  STATUT : EN ÉVEIL ◈

  🔎 OUDJAT : 'process_data' (Line 42, Complexity: 376)

  ⚠  SUTURES IDENTIFIED (2):
  🟡 Line 18 [LILITH] : Nested loop (depth 2). Consider a helper function.
     >> for j in range(b):
  🔵 Line 67 [SOUVERAINETE] : 'load_data' receives 6 arguments. Encapsulate in an object.
     >> def load_data(path, sep, enc, cols, dtype, na):
```

---

## 🧮 Mathematical Foundations

The **Radiance Formula** is derived from:

- **φ-Meta Framework** (Tomy Verreault, 2026) — Axioms AX-A0 through AX-A58
- **Law of Antifragility** (EQ-AFR-BMAD): `φ_{t+1} = P_φ(φ_t + k·Var(E_t)·E_t)`
- **Cybernetics** (Korchounov, Mir, 1975) — Feedback and variance as control metrics
- **Shannon Information Theory** — Code as an information channel

The **Sovereign Coding Rules** are derived from:
- **The C Book** (Banahan, Brady, Doran) — Scope hermeticity, resource lifecycle
- **JaCaMo / Multi-Agent Programming** — Agent independence and encapsulation

Full mathematical proof: [docs/MATHEMATIQUES.md](https://github.com/spockoo/phi-complexity/blob/main/docs/MATHEMATIQUES.md)

---

## 🏗 Sovereign Architecture

```
Zero external dependencies.
Pure Python standard library (ast, math, json).
```

```
phi_complexity/
├── core.py        ← Golden constants (PHI, TAXE_SUTURE, ETA_GOLDEN...)
├── analyseur.py   ← AST fractal dissection
├── metriques.py   ← Radiance Index calculation
├── rapport.py     ← Console / Markdown / JSON rendering
└── cli.py         ← phi check / phi report
```

---

## 🔗 Integration

### Pre-commit Hook
```yaml
repos:
  - repo: https://github.com/spockoo/phi-complexity
    rev: v0.1.0
    hooks:
      - id: phi-check
        args: [--min-radiance, "70"]
```

### GitHub Action
```yaml
- name: Phi-Complexity Audit
  run: |
    pip install phi-complexity
    phi check ./src/ --min-radiance 75
```

---

## 📜 License

MIT — Tomy Verreault, 2026

*Anchored in the Bibliothèque Céleste — Morphic Phi Framework (φ-Meta)*
