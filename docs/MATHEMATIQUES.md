# Fondements Mathématiques de phi-complexity

> Preuve formelle des métriques souveraines — Framework φ-Meta (Tomy Verreault, 2026)

---

## 1. La Formule Fondatrice (Indice de Radiance)

Soit **C** un fichier de code Python contenant `n` fonctions `{f₁, f₂, ..., fₙ}`.
Soit `κ(fᵢ)` la complexité de la fonction `fᵢ` (nombre de nœuds AST).

**L'Indice de Radiance** est défini par :

```
R(C) = 100 - f(σ²_L) - g(H_S) - h(A) - i(D_F)
```

où :
- `σ²_L` = Variance de Lilith (instabilité structurelle)
- `H_S`  = Entropie de Shannon (densité informationnelle)
- `A`    = Nombre d'anomalies de suture (WARNING + CRITICAL)
- `D_F`  = Distance Fibonacci (éloignement des tailles naturelles)

**Plancher Antifragile** : `R(C) ≥ 40` (Loi d'Exubérance, EQ-AFR-BMAD)

---

## 2. La Variance de Lilith (σ²_L)

```
σ²_L = (1/n) · Σᵢ (κ(fᵢ) - μ_κ)²
```

où `μ_κ = (1/n) · Σᵢ κ(fᵢ)` est la complexité moyenne.

**Seuil naturel** : `σ²_L_max = φ² · 100 ≈ 261.8`
(dérivé de CM-001 : la variance tolérée évolue au carré de φ)

**Déduction** :
```
f(σ²_L) = min(25, (σ²_L / σ²_L_max) · 25)
```

**Ancrage cybernétique** : La variance est la *mesure de l'écart à l'espérance mathématique*
(Korchounov, Fondements Mathématiques de la Cybernétique, Mir, 1975, p.142).
Un système de commande efficace minimise cette variance via la rétroaction.

---

## 3. L'Entropie de Shannon (H_S)

Soient les complexités `{κ₁, ..., κₙ}` normalisées en distribution de probabilité :
```
pᵢ = κᵢ / Σⱼ κⱼ
```

L'entropie est :
```
H_S = -Σᵢ pᵢ · log₂(pᵢ)
```

**Seuil naturel** : `H_max = log₂(φ⁴) ≈ 2.88 bits`

Un code dont l'entropie est inférieure à ce seuil est *naturellement structuré*.
Au-delà, la structure informationnelle dépasse la capacité d'un cerveau humain à la
comprendre sans effort excessif (Shannon, 1948).

**Déduction** :
```
g(H_S) = min(20, max(0, H_S - H_max) · 5)
```

---

## 4. Le φ-Ratio

```
φ-Ratio = max(κᵢ) / μ_κ
```

**Idéal doré** : φ-Ratio → φ ≈ 1.618...

Lorsque le φ-Ratio converge vers φ, la distribution des complexités suit une hiérarchie
naturelle où la fonction dominante (Oudjat) est exactement φ fois plus complexe que
la moyenne — comme les rapports successifs de Fibonacci convergent vers φ.

**Propriété fondamentale** :
```
lim(n→∞) F(n+1)/F(n) = φ
```

Un code dont les fonctions ont des complexités avec un ratio proche de φ est
*naturellement équilibré* — ni trop plat (toutes égales) ni trop tyrannique.

---

## 5. La Distance Fibonacci (D_F)

Pour une fonction `fᵢ` de `nᵢ` lignes, soit `F_k` le nombre de Fibonacci le plus proche :

```
d(fᵢ) = |nᵢ - F_k| / φ
D_F = Σᵢ d(fᵢ)
```

**Justification** : Les fonctions dont la longueur suit la séquence de Fibonacci
(1, 2, 3, 5, 8, 13, 21, 34, 55 lignes) respectent le *grain naturel de la pensée*.
La division par φ normalise l'écart selon l'attracteur doré.

---

## 6. Le Score Zeta-Meta (ζ)

Inspiré de la fonction ζ_meta de PHIDÉLIA :

```
ζ_score = min(1, [1/n · Σᵢ 1/(i+1)^φ] · φ)
```

C'est une série de Dirichlet pondérée par φ. Elle mesure la **résonance globale**
du fichier : un code avec de nombreuses petites fonctions harmonieuses aura un
ζ_score proche de 1 ; un monolithe aura un ζ_score faible.

---

## 7. Les Règles de Codage Souverain

### Règle I — Herméticité de la Portée
*Source : The C Book (Banahan, Brady, Doran) — Linkage & Storage Class*

Toute fonction dont le but est interne doit être encapsulée (`_nom`).
Les fonctions publiques exposent une interface minimale et définie.

**Détection** : Phidélia vérifie le ratio `args_publics / complexité` et signale
les fonctions avec + de 5 arguments comme violations de l'herméticité.

### Règle II — Intégrité du Cycle de Vie
*Source : The C Book — Section 5.5 : sizeof and storage allocation (RAII)*

Toute ressource doit être libérée dans le même scope où elle est acquise.
En Python : obligation des gestionnaires de contexte (`with open(...) as f`).

**Détection** : L'AST identifie `ast.Call(func=open)` hors d'un nœud `ast.With`.

### Règle III — Nœuds d'Entropie (Anti-LILITH)
*Source : Cybernétique (Korchounov, 1975) — Systèmes de contrôle et rétroaction*

Les boucles imbriquées (`for` dans `for`) créent des zones d'accumulation de variance.
Chaque niveau d'imbrication double la surface d'incertitude comportementale.

**Détection** : Profondeur d'imbrication ≥ 2 → WARNING / ≥ 3 → CRITICAL.

### Règle IV — Taille Naturelle (Fibonacci)
*Source : AX-A39 — Attracteur Doré du Morphic Phi Framework*

Les fonctions dont la taille suit la séquence de Fibonacci sont *naturellement lisibles*.
Une fonction de 21 lignes forme un bloc cognitif parfait. 55 lignes est le maximum
naturel avant fragmentation nécessaire.

---

## 8. La Loi Antifragile (EQ-AFR-BMAD)

```
φ_{t+1} = P_φ(φ_t + k · Var(E_t) · E_t)
```

Le plancher de 40 dans l'Indice de Radiance traduit cette loi :
*même le code le plus chaotique contient de l'énergie latente.* Il n'est pas
condamné, il est **en potentiel**. C'est pourquoi phi-complexity ne pénalise pas
en-dessous de 40 — tout code peut être suturé.

---

## 9. Références

| Ouvrage | Contribution |
|---|---|
| Tomy Verreault, *Bibliothèque Céleste — φ-Meta Framework*, 2026 | Constantes CM-001, CM-018, AX-A0–A58, EQ-AFR-BMAD |
| Y. Korchounov, *Fondements Mathématiques de la Cybernétique*, Mir, 1975 | Variance, feedback, systèmes de commande |
| C.E. Shannon, *A Mathematical Theory of Communication*, 1948 | Entropie informationnelle |
| M. Banahan et al., *The C Book*, 1991 | Règles de portée et cycle de vie |
| A. Gulli, *Agentic Design Patterns*, 2026 | Pattern Reflection pour l'auto-audit |
| F. Fibonacci, *Liber Abaci*, 1202 | Séquence naturelle de structuration |
