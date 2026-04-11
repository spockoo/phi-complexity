"""
phi_complexity/backends/asm_light.py — Backend souverain pour langages assembleurs.

Analyse "Light" basée sur regex pour x86/x86-64, ARM (AArch64) et RISC-V.
Zéro dépendances externes — Souveraineté totale.

Phase 15 du Morphic Phi Framework.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from ..analyseur import ResultatAnalyse, MetriqueFonction, Annotation
from ..core import distance_fibonacci
from .base import AnalyseurBackend

# ────────────────────────────────────────────────────────
# PATTERNS DE BRANCHEMENTS PAR ARCHITECTURE
# ────────────────────────────────────────────────────────

# x86 / x86-64 (Intel & AT&T syntax)
_X86_BRANCHES = re.compile(
    r"^\s*(jmp|je|jne|jz|jnz|jg|jge|jl|jle|ja|jae|jb|jbe|jc|jnc|jo|jno|js|jns|"
    r"jp|jnp|jcxz|jecxz|jrcxz|loop|loope|loopne|loopz|loopnz)\b",
    re.IGNORECASE,
)
_X86_CALL = re.compile(r"^\s*(call|syscall|int)\b", re.IGNORECASE)
_X86_RET = re.compile(r"^\s*(ret|retn|retf|iret|iretd|iretq)\b", re.IGNORECASE)
_X86_PUSH = re.compile(r"^\s*(push|pushf|pushfd|pushfq|pusha|pushad)\b", re.IGNORECASE)
_X86_POP = re.compile(r"^\s*(pop|popf|popfd|popfq|popa|popad)\b", re.IGNORECASE)

# ARM / AArch64
_ARM_BRANCHES = re.compile(
    r"^\s*(b|bl|blx|bx|beq|bne|bgt|bge|blt|ble|bhi|bls|bcc|bcs|"
    r"b\.eq|b\.ne|b\.gt|b\.ge|b\.lt|b\.le|b\.hi|b\.ls|b\.cc|b\.cs|"
    r"cbz|cbnz|tbz|tbnz)\b",
    re.IGNORECASE,
)
_ARM_RET = re.compile(r"^\s*(bx\s+lr|ret)\b", re.IGNORECASE)
_ARM_PUSH = re.compile(r"^\s*(push|stmfd|stp)\b", re.IGNORECASE)
_ARM_POP = re.compile(r"^\s*(pop|ldmfd|ldp)\b", re.IGNORECASE)

# RISC-V
_RISCV_BRANCHES = re.compile(
    r"^\s*(beq|bne|blt|bge|bltu|bgeu|jal|jalr|j)\b",
    re.IGNORECASE,
)
_RISCV_RET = re.compile(r"^\s*(ret|jalr\s+zero)\b", re.IGNORECASE)

# Labels (global pour toutes architectures)
_LABEL = re.compile(r"^([a-zA-Z_][\w.]*)\s*:")
_DIRECTIVE = re.compile(r"^\s*\.", re.IGNORECASE)
_COMMENT_LINE = re.compile(r"^\s*([;#@]|//|/\*)")

# Poids des branchements dans le calcul de complexité ASM
# Les branchements sont pondérés ×2 car ils créent des chemins d'exécution
# alternatifs, doublant l'effort cognitif de compréhension.
_POIDS_BRANCHEMENT = 2
_SEUIL_COMPLEXITE_WARNING = 34  # Fibonacci(9)
_SEUIL_COMPLEXITE_CRITICAL = 55  # Fibonacci(10)
_SEUIL_BRANCHES_LILITH = 13  # Fibonacci(7) — trop de branchements


def _detecter_architecture(lignes: List[str]) -> str:
    """Détecte l'architecture du fichier assembleur par heuristique."""
    score_x86 = 0
    score_arm = 0
    score_riscv = 0

    for ligne in lignes[:100]:  # Analyse des 100 premières lignes
        stripped = ligne.strip().lower()
        if any(
            kw in stripped
            for kw in ("eax", "ebx", "rax", "rbx", "rsp", "rbp", "mov", "push", "pop")
        ):
            score_x86 += 1
        if any(kw in stripped for kw in ("r0", "r1", "sp", "lr", "stp", "ldp", "adr")):
            score_arm += 1
        if any(
            kw in stripped for kw in ("a0", "a1", "s0", "s1", "ra", "addi", "ecall")
        ):
            score_riscv += 1

    if score_riscv > score_x86 and score_riscv > score_arm:
        return "riscv"
    if score_arm > score_x86:
        return "arm"
    return "x86"


class AsmLightBackend(AnalyseurBackend):
    """
    Backend souverain pour les langages assembleurs.
    Analyse "Light" basée sur le comptage de branchements et la détection
    de routines par labels. Supporte x86/x86-64, ARM/AArch64, RISC-V.
    Zéro dépendances.
    """

    def analyser(self) -> ResultatAnalyse:
        with open(self.fichier, "r", encoding="utf-8") as handle:
            lignes = handle.readlines()

        resultat = ResultatAnalyse(fichier=self.fichier)
        resultat.nb_lignes_total = len(lignes)

        arch = _detecter_architecture(lignes)

        # Sélection des patterns selon l'architecture
        pat_branch, pat_ret, pat_push, pat_pop = _patterns_pour_arch(arch)

        # Comptage global
        nb_commentaires = 0
        routines = _extraire_routines(lignes, pat_ret)

        for ligne in lignes:
            stripped = ligne.strip()
            if _COMMENT_LINE.match(stripped) or not stripped:
                if stripped:
                    nb_commentaires += 1

        resultat.nb_commentaires = nb_commentaires

        # Analyse de chaque routine
        for nom, debut, fin in routines:
            bloc = lignes[debut:fin]
            metrique, annotations = _analyser_routine(
                nom, debut + 1, bloc, pat_branch, pat_push, pat_pop, arch
            )
            resultat.fonctions.append(metrique)
            resultat.annotations.extend(annotations)

        # Calcul des phi_ratio et identification de l'oudjat
        if resultat.fonctions:
            resultat.oudjat = max(resultat.fonctions, key=lambda f: f.complexite)
            moyenne = sum(f.complexite for f in resultat.fonctions) / len(
                resultat.fonctions
            )
            if moyenne > 0:
                for f in resultat.fonctions:
                    f.phi_ratio = f.complexite / moyenne

        return resultat


def _patterns_pour_arch(
    arch: str,
) -> Tuple[re.Pattern[str], re.Pattern[str], re.Pattern[str], re.Pattern[str]]:
    """Retourne les patterns regex appropriés pour l'architecture détectée."""
    if arch == "arm":
        return _ARM_BRANCHES, _ARM_RET, _ARM_PUSH, _ARM_POP
    if arch == "riscv":
        return _RISCV_BRANCHES, _RISCV_RET, _X86_PUSH, _X86_POP  # RISC-V n'a pas push/pop natif
    return _X86_BRANCHES, _X86_RET, _X86_PUSH, _X86_POP


def _extraire_routines(
    lignes: List[str], pat_ret: re.Pattern[str]
) -> List[Tuple[str, int, int]]:
    """
    Extrait les routines du fichier assembleur.
    Une routine = un label suivi éventuellement d'un ret/leave/bx lr.
    """
    routines: List[Tuple[str, int, int]] = []
    labels: List[Tuple[str, int]] = []

    for i, ligne in enumerate(lignes):
        stripped = ligne.strip()
        if _DIRECTIVE.match(stripped):
            continue
        match = _LABEL.match(stripped)
        if match:
            labels.append((match.group(1), i))

    # Délimiter les routines entre deux labels successifs
    for idx, (nom, debut) in enumerate(labels):
        if idx + 1 < len(labels):
            fin = labels[idx + 1][1]
        else:
            fin = len(lignes)

        # Vérifier qu'il y a des instructions (pas juste un label de données)
        bloc = lignes[debut:fin]
        has_instructions = any(
            l.strip()
            and not _COMMENT_LINE.match(l.strip())
            and not _DIRECTIVE.match(l.strip())
            and not _LABEL.match(l.strip())
            for l in bloc
        )
        if has_instructions:
            routines.append((nom, debut, fin))

    return routines


def _analyser_routine(
    nom: str,
    ligne_debut: int,
    bloc: List[str],
    pat_branch: re.Pattern[str],
    pat_push: re.Pattern[str],
    pat_pop: re.Pattern[str],
    arch: str,
) -> Tuple[MetriqueFonction, List[Annotation]]:
    """Analyse une routine assembleur et retourne ses métriques + annotations."""
    annotations: List[Annotation] = []
    nb_instructions = 0
    nb_branches = 0
    nb_push = 0
    nb_pop = 0
    profondeur_max = 0
    profondeur_courante = 0

    for ligne in bloc:
        stripped = ligne.strip()
        if not stripped or _COMMENT_LINE.match(stripped) or _DIRECTIVE.match(stripped):
            continue
        if _LABEL.match(stripped):
            continue

        nb_instructions += 1

        if pat_branch.match(stripped):
            nb_branches += 1
            profondeur_courante += 1
            profondeur_max = max(profondeur_max, profondeur_courante)
        elif pat_push.match(stripped):
            nb_push += 1
        elif pat_pop.match(stripped):
            nb_pop += 1
            if profondeur_courante > 0:
                profondeur_courante -= 1

    # Complexité = instructions + branches pondérés
    complexite = nb_instructions + nb_branches * _POIDS_BRANCHEMENT

    nb_lignes = len([l for l in bloc if l.strip()])

    metrique = MetriqueFonction(
        nom=nom,
        ligne=ligne_debut,
        complexite=complexite,
        nb_args=0,
        nb_lignes=nb_lignes,
        profondeur_max=profondeur_max,
        distance_fib=distance_fibonacci(nb_lignes),
        phi_ratio=1.0,
    )

    # ── Règle LILITH-ASM : trop de branchements conditionnels ──
    if nb_branches > _SEUIL_BRANCHES_LILITH:
        extrait = bloc[0].strip() if bloc else nom
        annotations.append(
            Annotation(
                ligne=ligne_debut,
                message=(
                    f"LILITH-ASM : Routine '{nom}' contient {nb_branches} branchements "
                    f"(seuil Fibonacci: {_SEUIL_BRANCHES_LILITH}). "
                    f"Simplifier le flux de contrôle."
                ),
                niveau="WARNING",
                extrait=extrait,
                categorie="LILITH",
            )
        )

    # ── Règle RAII-ASM : push sans pop correspondant (fuite de pile) ──
    if nb_push > nb_pop:
        extrait = bloc[0].strip() if bloc else nom
        annotations.append(
            Annotation(
                ligne=ligne_debut,
                message=(
                    f"RAII-ASM : Routine '{nom}' a {nb_push} push mais seulement "
                    f"{nb_pop} pop. Fuite de pile possible."
                ),
                niveau="WARNING",
                extrait=extrait,
                categorie="SUTURE",
            )
        )

    # ── Règle FIBONACCI-ASM : taille de routine ──
    if complexite > _SEUIL_COMPLEXITE_CRITICAL:
        extrait = bloc[0].strip() if bloc else nom
        annotations.append(
            Annotation(
                ligne=ligne_debut,
                message=(
                    f"FIBONACCI-ASM : Routine '{nom}' a une complexité de {complexite} "
                    f"(seuil critique: {_SEUIL_COMPLEXITE_CRITICAL}). "
                    f"Découper en sous-routines."
                ),
                niveau="CRITICAL",
                extrait=extrait,
                categorie="FIBONACCI",
            )
        )
    elif complexite > _SEUIL_COMPLEXITE_WARNING:
        extrait = bloc[0].strip() if bloc else nom
        annotations.append(
            Annotation(
                ligne=ligne_debut,
                message=(
                    f"FIBONACCI-ASM : Routine '{nom}' a une complexité de {complexite} "
                    f"(seuil: {_SEUIL_COMPLEXITE_WARNING}). Surveiller la croissance."
                ),
                niveau="WARNING",
                extrait=extrait,
                categorie="FIBONACCI",
            )
        )

    return metrique, annotations
