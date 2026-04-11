"""
tests/test_asm_backend.py — Tests du backend assembleur (Phase 15).
"""

import os
import tempfile

from phi_complexity.backends.asm_light import (
    AsmLightBackend,
    _detecter_architecture,
    _patterns_pour_arch,
)
from phi_complexity.analyseur import AnalyseurPhi

# ────────────────────────────────────────────────────────
# FIXTURES — Code assembleur de test
# ────────────────────────────────────────────────────────

CODE_X86_SIMPLE = """\
section .text
global _start

_start:
    mov eax, 1
    mov ebx, 0
    int 0x80

hello:
    push ebp
    mov ebp, esp
    mov eax, [ebp+8]
    add eax, [ebp+12]
    pop ebp
    ret
"""

CODE_X86_COMPLEXE = """\
section .text

sort_array:
    push ebp
    mov ebp, esp
    mov ecx, [ebp+8]
    mov edx, [ebp+12]
.outer_loop:
    cmp ecx, edx
    jge .done
    mov eax, [ecx]
    mov ebx, [ecx+4]
    cmp eax, ebx
    jle .no_swap
    mov [ecx], ebx
    mov [ecx+4], eax
.no_swap:
    add ecx, 4
    jmp .outer_loop
.done:
    pop ebp
    ret
"""

CODE_ARM_SIMPLE = """\
.text
.global main

main:
    stp x29, x30, [sp, #-16]!
    mov x0, #42
    ldp x29, x30, [sp], #16
    ret

add_func:
    add x0, x0, x1
    ret
"""

CODE_RISCV_SIMPLE = """\
.text
.globl _start

_start:
    addi a0, zero, 1
    addi a7, zero, 93
    ecall

fibonacci:
    addi sp, sp, -16
    beq a0, zero, .base
    addi a0, a0, -1
    jal ra, fibonacci
.base:
    addi sp, sp, 16
    jalr zero, ra, 0
"""

CODE_X86_PUSH_NO_POP = """\
section .text

leaky_func:
    push eax
    push ebx
    push ecx
    mov eax, 1
    mov ebx, 2
    add eax, ebx
    ret
"""

CODE_X86_MANY_BRANCHES = """\
section .text

dispatcher:
    cmp eax, 0
    je .case0
    cmp eax, 1
    je .case1
    cmp eax, 2
    je .case2
    cmp eax, 3
    je .case3
    cmp eax, 4
    je .case4
    cmp eax, 5
    je .case5
    cmp eax, 6
    je .case6
    cmp eax, 7
    je .case7
    cmp eax, 8
    je .case8
    cmp eax, 9
    je .case9
    cmp eax, 10
    je .case10
    cmp eax, 11
    je .case11
    cmp eax, 12
    je .case12
    cmp eax, 13
    je .case13
    jmp .default
.case0:
.case1:
.case2:
.case3:
.case4:
.case5:
.case6:
.case7:
.case8:
.case9:
.case10:
.case11:
.case12:
.case13:
.default:
    ret
"""


def _creer_fichier_asm(contenu: str, suffix: str = ".asm") -> str:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    f.write(contenu)
    f.close()
    return f.name


# ────────────────────────────────────────────────────────
# TESTS — Architecture Detection
# ────────────────────────────────────────────────────────


class TestArchitectureDetection:
    def test_detecte_x86(self):
        lignes = CODE_X86_SIMPLE.splitlines()
        assert _detecter_architecture(lignes) == "x86"

    def test_detecte_arm(self):
        lignes = CODE_ARM_SIMPLE.splitlines()
        assert _detecter_architecture(lignes) == "arm"

    def test_detecte_riscv(self):
        lignes = CODE_RISCV_SIMPLE.splitlines()
        assert _detecter_architecture(lignes) == "riscv"

    def test_detecte_defaut_x86(self):
        """Un fichier vide doit retourner x86 par défaut."""
        assert _detecter_architecture([]) == "x86"


# ────────────────────────────────────────────────────────
# TESTS — Backend x86
# ────────────────────────────────────────────────────────


class TestAsmLightBackendX86:
    def test_analyser_fichier_vide(self):
        chemin = _creer_fichier_asm("")
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            assert r.fichier == chemin
            assert len(r.fonctions) == 0
            assert r.oudjat is None
        finally:
            os.unlink(chemin)

    def test_analyser_detecte_routines(self):
        chemin = _creer_fichier_asm(CODE_X86_SIMPLE)
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            assert len(r.fonctions) >= 1
            noms = [f.nom for f in r.fonctions]
            assert "_start" in noms or "hello" in noms
        finally:
            os.unlink(chemin)

    def test_analyser_nb_lignes_total(self):
        chemin = _creer_fichier_asm(CODE_X86_SIMPLE)
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            assert r.nb_lignes_total == len(CODE_X86_SIMPLE.splitlines())
        finally:
            os.unlink(chemin)

    def test_analyser_oudjat_defini(self):
        chemin = _creer_fichier_asm(CODE_X86_COMPLEXE)
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            if r.fonctions:
                assert r.oudjat is not None
                assert r.oudjat == max(r.fonctions, key=lambda f: f.complexite)
        finally:
            os.unlink(chemin)

    def test_analyser_phi_ratio_calcule(self):
        chemin = _creer_fichier_asm(CODE_X86_SIMPLE)
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            for f in r.fonctions:
                assert f.phi_ratio >= 0.0
        finally:
            os.unlink(chemin)

    def test_extension_s_acceptee(self):
        """Les fichiers .s doivent être acceptés par le backend."""
        chemin = _creer_fichier_asm(CODE_X86_SIMPLE, suffix=".s")
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            assert isinstance(r.fonctions, list)
        finally:
            os.unlink(chemin)


# ────────────────────────────────────────────────────────
# TESTS — Annotations ASM
# ────────────────────────────────────────────────────────


class TestAsmAnnotations:
    def test_annotation_raii_push_sans_pop(self):
        """push sans pop correspondant doit générer une annotation SUTURE."""
        chemin = _creer_fichier_asm(CODE_X86_PUSH_NO_POP)
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            suture_annots = [a for a in r.annotations if a.categorie == "SUTURE"]
            assert len(suture_annots) >= 1
            assert (
                "push" in suture_annots[0].message.lower()
                or "pop" in suture_annots[0].message.lower()
            )
        finally:
            os.unlink(chemin)

    def test_annotation_lilith_trop_de_branches(self):
        """Trop de branchements doit générer une annotation LILITH."""
        chemin = _creer_fichier_asm(CODE_X86_MANY_BRANCHES)
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            lilith_annots = [a for a in r.annotations if a.categorie == "LILITH"]
            assert len(lilith_annots) >= 1
        finally:
            os.unlink(chemin)


# ────────────────────────────────────────────────────────
# TESTS — Backend ARM
# ────────────────────────────────────────────────────────


class TestAsmLightBackendARM:
    def test_analyser_arm_detecte_routines(self):
        chemin = _creer_fichier_asm(CODE_ARM_SIMPLE)
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            assert len(r.fonctions) >= 1
        finally:
            os.unlink(chemin)


# ────────────────────────────────────────────────────────
# TESTS — Backend RISC-V
# ────────────────────────────────────────────────────────


class TestAsmLightBackendRISCV:
    def test_analyser_riscv_detecte_routines(self):
        chemin = _creer_fichier_asm(CODE_RISCV_SIMPLE)
        try:
            backend = AsmLightBackend(chemin)
            r = backend.analyser()
            assert len(r.fonctions) >= 1
        finally:
            os.unlink(chemin)


# ────────────────────────────────────────────────────────
# TESTS — Intégration avec AnalyseurPhi (Factory)
# ────────────────────────────────────────────────────────


class TestAnalyseurPhiASM:
    def test_factory_selectionne_asm_pour_asm(self):
        chemin = _creer_fichier_asm(CODE_X86_SIMPLE, suffix=".asm")
        try:
            analyseur = AnalyseurPhi(chemin)
            assert isinstance(analyseur.backend, AsmLightBackend)
        finally:
            os.unlink(chemin)

    def test_factory_selectionne_asm_pour_s(self):
        chemin = _creer_fichier_asm(CODE_X86_SIMPLE, suffix=".s")
        try:
            analyseur = AnalyseurPhi(chemin)
            assert isinstance(analyseur.backend, AsmLightBackend)
        finally:
            os.unlink(chemin)

    def test_audit_complet_asm(self):
        """Un audit complet via AnalyseurPhi doit fonctionner."""
        chemin = _creer_fichier_asm(CODE_X86_SIMPLE, suffix=".asm")
        try:
            analyseur = AnalyseurPhi(chemin)
            resultat = analyseur.analyser()
            assert resultat.fichier == chemin
            assert resultat.nb_lignes_total > 0
        finally:
            os.unlink(chemin)


# ────────────────────────────────────────────────────────
# TESTS — Patterns per architecture
# ────────────────────────────────────────────────────────


class TestPatternsParArch:
    def test_patterns_x86(self):
        pat_branch, pat_ret, pat_push, pat_pop = _patterns_pour_arch("x86")
        assert pat_branch.match("  jmp .label")
        assert pat_ret.match("  ret")
        assert pat_push.match("  push eax")
        assert pat_pop.match("  pop eax")

    def test_patterns_arm(self):
        pat_branch, pat_ret, pat_push, pat_pop = _patterns_pour_arch("arm")
        assert pat_branch.match("  beq .label")
        assert pat_ret.match("  bx lr")

    def test_patterns_riscv(self):
        pat_branch, pat_ret, _, _ = _patterns_pour_arch("riscv")
        assert pat_branch.match("  beq a0, zero, .label")
        assert pat_ret.match("  ret")
