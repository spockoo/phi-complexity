# Boucle de Zéro, Quasicristaux et IA OSS

## 1) Cadrage formel : axiome symbolique vs mesure calculable

| Formulation | Axiome symbolique | Mesures calculables dans `phi-complexity` |
|---|---|---|
| Opérateur de condition de zéro \( \mathcal{Z}_{\phi} \) | \( \int_{M_O}\zeta(s)\cdot\frac{1}{|\psi_g\rangle}\,ds = 0 \) | `zeta_score`, `phi_ratio_delta`, `zero_condition_tension`, `zero_condition_alignment` |
| Clamp de structure zéro | \( \phi[t+1] = \max(0,\phi[t+1]) \) | `zero_clamped_resistance`, plancher de radiance, stabilité des transitions |
| Loi de l'attracteur zéro | \( \Delta Chaos \to 0 \Rightarrow (R_{système}\to 0 \land E_{potentielle}\to \infty) \) | `resistance`, `sync_index`, `zero_attractor_convergence` |
| Théorème du zéro morphogénétique | \( \exists t,i:\phi_i[t]=0 \Rightarrow reset/renaissance \) | `zero_morphogenetic_state`, `zero_morphogenetic_trigger`, `quasicrystal_coherence` |

## 2) Cartographie avec les quasicristaux

La cohérence quasicristalline est modélisée par:

- **Ordre apériodique**: proximité au nombre d'or (`phi_ratio_delta` faible),
- **Résonance globale**: stabilisation du score zêta (`zeta_score` élevé),
- **Contrainte de stabilité**: tension Heisenberg-Phi autour du plancher naturel,
- **Convergence**: baisse de la résistance et montée du `sync_index`.

### Matrice d'interaction

| Relation | Implémentation |
|---|---|
| \( \mathcal{Z}_{\phi} \leftrightarrow \) zeta-score + écart φ | `zero_condition_tension`, `zero_condition_alignment` |
| Clamp \( \max(0,\cdot) \leftrightarrow \) plancher/stabilité | `zero_clamped_resistance` |
| Attracteur zéro \( \leftrightarrow \) résistance minimale + convergence | `zero_attractor_convergence`, `sync_index` |
| Zéro morphogénétique \( \leftrightarrow \) reset/renaissance | `zero_morphogenetic_state`, `zero_morphogenetic_trigger` |

## 3) Traduction opérationnelle

Les nouvelles métriques sont calculées dans `phi_complexity/metriques.py` sans modifier les métriques historiques.

Seuils de cohérence quasicristalline (`core.py`) :

- `QUASICRYSTAL_COHERENCE_EVEIL = 0.55`
- `QUASICRYSTAL_COHERENCE_HERMETIQUE = 0.78`
- `ZERO_CAUSAL_RESISTANCE_MAX = 0.08`
- `MORPHOGENESIS_RENAISSANCE_SYNC_MIN = 0.70`

## 4) Interfaçage IA open source

Le pipeline local est enrichi:

- `harvest` exporte les états `PRE_ZERO`, `ZERO_CAUSAL`, `POST_RENAISSANCE`,
- `search` permet de filtrer ces transitions (`--etat-zero`),
- `notebook_helpers` expose la matrice et un tableau de transitions.

## 5) Validation scientifique interne

Protocole recommandé:

1. corpus harmonieux (ordre),
2. corpus chaotique (désordre),
3. corpus suturé (renaissance),
4. vérification de stabilité/reproductibilité des états,
5. **falsification**: cas synthétiques où `zeta_score` est haut mais `phi_ratio_delta` élevé (ou inverse) et où l'état ne doit pas converger vers `POST_RENAISSANCE`.

## 6) Tableau d'interprétation des états

| État | Critères |
|---|---|
| `PRE_ZERO` | alignement insuffisant, résistance non minimale, cohérence faible |
| `ZERO_CAUSAL` | alignement suffisant + `resistance <= 0.08` |
| `POST_RENAISSANCE` | état zéro atteint + `sync_index >= 0.70` + cohérence hermétique |

Ce tableau est aussi générable via `tableau_zero_morphogenetique()` dans `notebook_helpers`.
