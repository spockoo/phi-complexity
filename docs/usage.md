# Usage de la CLI 🛠

L'outil `phi` est votre interface principale pour interagir avec le framework.

## Commande `check`

La commande la plus importante. Elle scanne votre code et calcule sa radiance.

```bash
# Audit d'un fichier unique
phi check script.py

# Audit en mode JSON (pour intégration machine)
phi check script.py --format json
```

### Options de `check`

- `--min-radiance <float>` : Définit un seuil critique. Si le score est inférieur, `phi` se terminera avec un code d'erreur (exit 1).
- `--format {console,json}` : Définit le style de sortie.

---

## Commande `report`

Génère un rapport complet en Markdown, incluant les "Sutures" (corrections suggérées).

```bash
phi report mon_code.py --output RADIANCE.md
```

Le rapport contient :
1. Un résumé des métriques $\varphi$.
2. L'identification de l'**Oudjat** (la fonction la plus complexe).
3. Une liste exhaustive des ruptures de radiance (boucles imbriquées, fonctions trop longues, etc.).

---

## Commande `fund` 🚀

Affiche les informations pour soutenir la recherche souveraine.

```bash
phi fund
```

---

## Guide des Messages (Sutures)

Lorsque `phi` détecte une anomalie, il affiche un message de suture :

- **LILITH (Variance)** : Indique une fonction trop complexe par rapport aux autres.
- **SOUVERAINETÉ** : Indique une violation des principes d'herméticité (ex: trop d'arguments).
- **ENTROPIE** : Indique une accumulation de désordre structurel.
- **FIBONACCI** : Indique que la taille de la fonction n'est pas "naturelle".
