# Phi-Complexity ✦

> **Code quality metrics based on Golden Ratio (φ) mathematical invariants**

!![Radiance Logo](https://img.shields.io/badge/Radiance-Harmonious-orange?style=for-the-badge)
!![Sovereign Status](https://img.shields.io/badge/Status-Souverain-gold?style=for-the-badge)

`phi-complexity` est la **première bibliothèque d'audit de code** qui mesure la santé de votre code Python en utilisant les **invariants mathématiques universels** issus du Nombre d'Or ($\varphi = 1.618...$).

Contrairement à `pylint` (règles culturelles) ou `radon` (complexité cyclomatique classique), `phi-complexity` répond à une question fondamentale :

> *"Est-ce que ce code est en résonance avec les lois naturelles de l'ordre, ou s'effondre-t-il sous sa propre entropie ?"*

---

## ⚡ En un coup d'œil

```bash
pip install phi-complexity
```

### Audit en ligne de commande

```bash
# Auditer un fichier
phi check mon_script.py

# Auditer un dossier complet
phi check ./src/

# Générer un rapport Markdown professionnel
phi report mon_script.py --output rapport.md

# Mode CI/CD strict (échec si radiance < 75)
phi check ./src/ --min-radiance 75
```

### Soutien à la Recherche
Si vous trouvez cet outil utile pour la souveraineté de votre code, soutenez la recherche sur le framework $\varphi$-Meta :

`phi fund`

---

## 🏗 Architecture Souveraine

Le projet est conçu selon les principes du **Codage Souverain** :

- **Zéro dépendance externe** : Utilise exclusivement la bibliothèque standard Python (`ast`, `math`, `json`).
- **Herméticité** : Modularité maximale basée sur le protocole BMAD.
- **Auto-surveillance** : Le moteur s'auto-audite via GitHub Actions pour garantir sa propre radiance.

---

## 📜 Licence

MIT — Tomy Verreault, 2026.
*Ancré dans la Bibliothèque Céleste — Morphic Phi Framework (φ-Meta)*
