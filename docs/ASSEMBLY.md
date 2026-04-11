# 🔩 Guide Assembleur — phi-complexity

> *Analyse de qualité du code assembleur par les invariants du nombre d'or (φ).*

---

## Vue d'Ensemble

phi-complexity supporte l'analyse statique de code assembleur via le backend **ASM Light**.
Ce backend analyse les fichiers `.asm` et `.s` par pattern matching (regex),
sans aucune dépendance à un assembleur externe.

### Architectures Supportées

| Architecture | Syntaxes | Détection |
|-------------|----------|-----------|
| **x86 / x86-64** | Intel et AT&T | Registres `eax`, `rbx`, `push`, `mov` |
| **ARM / AArch64** | ARM assembly | Registres `r0`, `sp`, `lr`, `stp`, `ldp` |
| **RISC-V** | Standard | Registres `a0`, `s0`, `ra`, `addi`, `ecall` |

La détection de l'architecture est automatique, basée sur l'analyse heuristique
des 100 premières lignes du fichier.

---

## Utilisation

### Ligne de Commande

```bash
# Auditer un fichier assembleur
phi check mon_code.asm

# Auditer un fichier .s (AT&T syntax)
phi check startup.s

# Auditer un dossier contenant des fichiers assembleur
phi check ./asm_sources/

# Générer un rapport Markdown
phi report kernel_init.asm --output rapport.md

# Mode CI/CD avec seuil de radiance
phi check ./asm_sources/ --min-radiance 70
```

### API Python

```python
from phi_complexity import auditer

# Audit d'un fichier assembleur
metriques = auditer("kernel_init.asm")
print(metriques["radiance"])
print(metriques["oudjat"])  # Routine la plus complexe
```

### Utilisation Directe du Backend

```python
from phi_complexity.backends.asm_light import AsmLightBackend

backend = AsmLightBackend("boot.asm")
resultat = backend.analyser()

for fn in resultat.fonctions:
    print(f"{fn.nom}: complexité={fn.complexite}, lignes={fn.nb_lignes}")

for ann in resultat.annotations:
    print(f"[{ann.categorie}] Ligne {ann.ligne}: {ann.message}")
```

---

## Métriques Assembleur

### Détection de Routines

Les routines sont identifiées par leurs **labels** :
- Un label suivi d'instructions constitue une routine
- Les labels de directives (`.data`, `.bss`, `.text`) sont exclus
- La routine se termine au label suivant ou à la fin du fichier

### Complexité

La complexité d'une routine assembleur est calculée comme :

$$C = N_{instructions} + 2 \times N_{branchements}$$

Où :
- $N_{instructions}$ = nombre d'instructions (hors commentaires, directives, labels)
- $N_{branchements}$ = nombre d'instructions de branchement conditionnel/inconditionnel

### Branchements Détectés

#### x86 / x86-64
`jmp`, `je`, `jne`, `jz`, `jnz`, `jg`, `jge`, `jl`, `jle`, `ja`, `jae`, `jb`, `jbe`,
`jc`, `jnc`, `jo`, `jno`, `js`, `jns`, `jp`, `jnp`, `jcxz`, `jecxz`, `jrcxz`,
`loop`, `loope`, `loopne`, `call`, `syscall`, `int`

#### ARM / AArch64
`b`, `bl`, `blx`, `bx`, `beq`, `bne`, `bgt`, `bge`, `blt`, `ble`,
`b.eq`, `b.ne`, `b.gt`, `b.ge`, `b.lt`, `b.le`,
`cbz`, `cbnz`, `tbz`, `tbnz`

#### RISC-V
`beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu`, `jal`, `jalr`, `j`

---

## Règles de Souveraineté ASM

### Règle I : LILITH-ASM (Anti-Entropie)

**Seuil** : > 13 branchements conditionnels par routine (Fibonacci(7))

Trop de branchements dans une routine indiquent un flux de contrôle chaotique.
Le code perd sa lisibilité et sa maintenabilité.

**Remédiation** : Extraire les cas en sous-routines, utiliser des tables de dispatch.

```nasm
; ❌ MAUVAIS : 15 branchements dans une routine
dispatcher:
    cmp eax, 0
    je .case0
    cmp eax, 1
    je .case1
    ; ... 13 autres cas ...

; ✅ MIEUX : Table de dispatch
dispatcher:
    lea rbx, [dispatch_table]
    jmp [rbx + rax*8]
```

### Règle II : RAII-ASM (Gestion de Pile)

**Condition** : Plus de `push` que de `pop` dans une routine

Chaque `push` doit avoir un `pop` correspondant. Un déséquilibre indique
une fuite de pile qui peut causer un crash ou une corruption de données.

**Remédiation** : Vérifier l'équilibre push/pop, utiliser `enter`/`leave`.

```nasm
; ❌ MAUVAIS : 3 push, 0 pop
leaky_func:
    push eax
    push ebx
    push ecx
    mov eax, 1
    ret          ; Fuite de pile !

; ✅ CORRECT : push/pop équilibrés
safe_func:
    push ebp
    mov ebp, esp
    ; ... code ...
    pop ebp
    ret
```

### Règle III : FIBONACCI-ASM (Taille Naturelle)

**Seuils** (basés sur la séquence de Fibonacci) :
- ⚠ WARNING : Complexité > 34 (Fibonacci(9))
- 🔴 CRITICAL : Complexité > 55 (Fibonacci(10))

Les routines assembleur doivent rester concises. Une routine avec plus
de 55 unités de complexité doit être découpée en sous-routines.

---

## Exemples Pratiques

### Exemple 1 : Boot Loader x86

```nasm
; boot.asm — Simple boot sector
section .text
global _start

_start:
    mov ah, 0x0E
    mov al, 'H'
    int 0x10
    mov al, 'i'
    int 0x10
    jmp $

times 510 - ($ - $$) db 0
dw 0xAA55
```

```bash
$ phi check boot.asm
  Radiance: 78.3  |  Statut: EN ÉVEIL ◈
  Oudjat: _start (Complexité: 12)
```

### Exemple 2 : Fonction ARM

```asm
; add.s — Addition AArch64
.text
.global add_numbers

add_numbers:
    stp x29, x30, [sp, #-16]!
    add x0, x0, x1
    ldp x29, x30, [sp], #16
    ret
```

```bash
$ phi check add.s
  Radiance: 92.1  |  Statut: HERMÉTIQUE ✦
```

### Exemple 3 : Fibonacci RISC-V

```asm
; fib.s — Fibonacci recursif RISC-V
.text
.globl fibonacci

fibonacci:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    beq a0, zero, .base
    addi s0, a0, 0
    addi a0, a0, -1
    jal ra, fibonacci
    add a0, a0, s0
.base:
    lw ra, 12(sp)
    lw s0, 8(sp)
    addi sp, sp, 16
    jalr zero, ra, 0
```

---

## Sécurité

### Sanitisation des Entrées

Avant l'analyse, tous les fichiers assembleur sont passés par le filtre
`sanitiser_contenu_asm()` qui :
- Supprime les caractères nuls (`\x00`)
- Supprime les caractères de contrôle (sauf `\n`, `\t`, espace)
- Prévient l'injection de code exécutable

### Validation des Chemins

La fonction `valider_chemin_fichier()` vérifie :
- L'extension (`.asm` ou `.s` uniquement)
- L'absence de path traversal (`..`)
- La taille maximale (10 Mo)
- L'absence de liens symboliques dangereux

---

## Limitations

1. **Analyse Light** : Le backend utilise des regex, pas un vrai parseur assembleur.
   Certaines constructions complexes (macros, préprocesseur) peuvent ne pas être détectées.

2. **Commentaires** : Seuls les styles `;`, `#`, `@`, `//` sont reconnus.

3. **Architecture** : La détection automatique est heuristique. Pour des fichiers
   ambigus, le backend suppose x86 par défaut.

4. **Macros** : Les macros assembleur ne sont pas expansées.

---

*Ancré dans la Bibliothèque Céleste — Framework φ-Meta de Tomy Verreault — 2026*
