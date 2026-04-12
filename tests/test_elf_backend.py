"""
tests/test_elf_backend.py — Tests pour le backend ELF/PE/Mach-O (Phase 24).

Couvre :
    - Détection de format binaire (ELF, PE, Mach-O, inconnu)
    - Parsing de sections ELF 32/64 bits
    - Parsing de sections PE
    - Parsing de sections Mach-O
    - Calcul d'entropie de Shannon
    - Détection de shellcode (int 0x80, syscall)
    - Détection de sections W+X
    - Détection de binaires strippés
    - Annotations Fibonacci sur le nombre de sections
    - Intégration avec AnalyseurPhi
"""

from __future__ import annotations

import os
import struct
import tempfile

import pytest

from phi_complexity.backends.elf_light import (
    ElfLightBackend,
    _calculer_entropie_shannon,
    _detecter_format,
    _detecter_shellcode,
    _SectionInfo,
    _parser_elf,
    _parser_pe,
    _parser_macho,
    _analyser_section,
    _SEUIL_ENTROPIE_CRITICAL,
    _SEUIL_ENTROPIE_WARNING,
)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────


def _creer_fichier_temp(donnees: bytes, suffix: str = ".bin") -> str:
    """Crée un fichier temporaire binaire."""
    fd, chemin = tempfile.mkstemp(suffix=suffix)
    os.write(fd, donnees)
    os.close(fd)
    return chemin


def _safe_unlink(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _creer_elf_minimal_64() -> bytes:
    """Crée un binaire ELF 64-bit minimal avec une section .text."""
    # ELF Header (64 bytes)
    e_ident = b"\x7fELF"  # magic
    e_ident += b"\x02"  # 64-bit
    e_ident += b"\x01"  # little-endian
    e_ident += b"\x01"  # ELF version
    e_ident += b"\x00" * 9  # padding
    header = e_ident
    header += struct.pack("<H", 2)  # e_type = ET_EXEC
    header += struct.pack("<H", 0x3E)  # e_machine = x86-64
    header += struct.pack("<I", 1)  # e_version
    header += struct.pack("<Q", 0)  # e_entry
    header += struct.pack("<Q", 0)  # e_phoff
    header += struct.pack("<Q", 64)  # e_shoff = right after header
    header += struct.pack("<I", 0)  # e_flags
    header += struct.pack("<H", 64)  # e_ehsize
    header += struct.pack("<H", 0)  # e_phentsize
    header += struct.pack("<H", 0)  # e_phnum
    header += struct.pack("<H", 64)  # e_shentsize
    header += struct.pack("<H", 3)  # e_shnum = 3 (null + .text + .shstrtab)
    header += struct.pack("<H", 2)  # e_shstrndx = 2

    # String table for section names
    shstrtab = b"\x00.text\x00.shstrtab\x00"

    # Section data for .text (some NOP sled + ret)
    text_data = b"\x90" * 32 + b"\xc3"

    # Calculate offsets
    sh_offset = 64  # section header table starts after ELF header
    shdr_size = 64 * 3  # 3 section headers, each 64 bytes
    text_offset = sh_offset + shdr_size
    strtab_offset = text_offset + len(text_data)

    # Section Header 0 (SHT_NULL)
    sh0 = b"\x00" * 64

    # Section Header 1 (.text)
    sh1 = struct.pack("<I", 1)  # sh_name (.text at idx 1)
    sh1 += struct.pack("<I", 1)  # sh_type = SHT_PROGBITS
    sh1 += struct.pack("<Q", 0x6)  # sh_flags = SHF_ALLOC | SHF_EXECINSTR
    sh1 += struct.pack("<Q", 0)  # sh_addr
    sh1 += struct.pack("<Q", text_offset)  # sh_offset
    sh1 += struct.pack("<Q", len(text_data))  # sh_size
    sh1 += struct.pack("<I", 0)  # sh_link
    sh1 += struct.pack("<I", 0)  # sh_info
    sh1 += struct.pack("<Q", 16)  # sh_addralign
    sh1 += struct.pack("<Q", 0)  # sh_entsize

    # Section Header 2 (.shstrtab)
    sh2 = struct.pack("<I", 7)  # sh_name (.shstrtab at idx 7)
    sh2 += struct.pack("<I", 3)  # sh_type = SHT_STRTAB
    sh2 += struct.pack("<Q", 0)  # sh_flags
    sh2 += struct.pack("<Q", 0)  # sh_addr
    sh2 += struct.pack("<Q", strtab_offset)  # sh_offset
    sh2 += struct.pack("<Q", len(shstrtab))  # sh_size
    sh2 += struct.pack("<I", 0)  # sh_link
    sh2 += struct.pack("<I", 0)  # sh_info
    sh2 += struct.pack("<Q", 1)  # sh_addralign
    sh2 += struct.pack("<Q", 0)  # sh_entsize

    return header + sh0 + sh1 + sh2 + text_data + shstrtab


def _creer_pe_minimal() -> bytes:
    """Crée un fichier PE minimal avec une section .text."""
    # DOS Header (MZ stub)
    dos = b"MZ" + b"\x00" * 58
    pe_offset = 64
    dos += struct.pack("<I", pe_offset)  # e_lfanew at 0x3C

    # PE Signature
    pe_sig = b"PE\x00\x00"

    # COFF Header (20 bytes)
    coff = struct.pack("<H", 0x14C)  # Machine = i386
    coff += struct.pack("<H", 1)  # NumberOfSections
    coff += struct.pack("<I", 0)  # TimeDateStamp
    coff += struct.pack("<I", 0)  # PointerToSymbolTable
    coff += struct.pack("<I", 0)  # NumberOfSymbols
    coff += struct.pack("<H", 0)  # SizeOfOptionalHeader
    coff += struct.pack("<H", 0)  # Characteristics

    # Section Header (.text)
    section = b".text\x00\x00\x00"  # Name (8 bytes)
    section += struct.pack("<I", 32)  # VirtualSize
    section += struct.pack("<I", 0x1000)  # VirtualAddress
    section += struct.pack("<I", 32)  # SizeOfRawData
    text_offset = len(dos) + len(pe_sig) + len(coff) + 40  # after section header
    section += struct.pack("<I", text_offset)  # PointerToRawData
    section += struct.pack("<I", 0)  # PointerToRelocations
    section += struct.pack("<I", 0)  # PointerToLinenumbers
    section += struct.pack("<H", 0)  # NumberOfRelocations
    section += struct.pack("<H", 0)  # NumberOfLinenumbers
    section += struct.pack("<I", 0x60000020)  # Characteristics: EXEC|READ|CODE

    # .text data
    text_data = b"\xCC" * 32  # INT3 breakpoints

    return dos + pe_sig + coff + section + text_data


def _creer_macho_minimal_64() -> bytes:
    """Crée un binaire Mach-O 64-bit minimal."""
    # Mach-O header (little-endian, 64-bit) = 32 bytes
    magic = b"\xcf\xfa\xed\xfe"  # MH_MAGIC_64 (little-endian)

    # Section data
    text_data = b"\x90" * 64  # NOP sled

    # section_64 header = 80 bytes
    # sectname (16 bytes) + segname (16 bytes) + addr(8) + size(8)
    # + offset(4) + align(4) + reloff(4) + nreloc(4)
    # + flags(4) + reserved1(4) + reserved2(4) + reserved3(4) = 80

    # segment_command_64 = 72 bytes + nsects * 80
    seg_cmd_size = 72 + 80  # 1 section

    # Data offset: after header (32) + segment command (152)
    data_offset = 32 + seg_cmd_size

    # Build segment_command_64
    seg_cmd = struct.pack("<I", 0x19)  # cmd = LC_SEGMENT_64
    seg_cmd += struct.pack("<I", seg_cmd_size)  # cmdsize
    seg_cmd += b"__TEXT".ljust(16, b"\x00")  # segname (16 bytes)
    seg_cmd += struct.pack("<Q", 0)  # vmaddr
    seg_cmd += struct.pack("<Q", len(text_data))  # vmsize
    seg_cmd += struct.pack("<Q", data_offset)  # fileoff
    seg_cmd += struct.pack("<Q", len(text_data))  # filesize
    seg_cmd += struct.pack("<I", 5)  # maxprot = VM_PROT_READ | VM_PROT_EXECUTE
    seg_cmd += struct.pack("<I", 5)  # initprot
    seg_cmd += struct.pack("<I", 1)  # nsects = 1
    seg_cmd += struct.pack("<I", 0)  # flags

    # Build section_64
    sect = b"__text".ljust(16, b"\x00")  # sectname (16 bytes)
    sect += b"__TEXT".ljust(16, b"\x00")  # segname (16 bytes)
    sect += struct.pack("<Q", 0)  # addr
    sect += struct.pack("<Q", len(text_data))  # size
    sect += struct.pack("<I", data_offset)  # offset
    sect += struct.pack("<I", 0)  # align
    sect += struct.pack("<I", 0)  # reloff
    sect += struct.pack("<I", 0)  # nreloc
    sect += struct.pack("<I", 0)  # flags
    sect += struct.pack("<I", 0)  # reserved1
    sect += struct.pack("<I", 0)  # reserved2
    sect += struct.pack("<I", 0)  # reserved3

    # Build header
    header = magic
    header += struct.pack("<I", 0x01000007)  # cputype = CPU_TYPE_X86_64
    header += struct.pack("<I", 3)  # cpusubtype
    header += struct.pack("<I", 2)  # filetype = MH_EXECUTE
    header += struct.pack("<I", 1)  # ncmds = 1
    header += struct.pack("<I", seg_cmd_size)  # sizeofcmds
    header += struct.pack("<I", 0)  # flags
    header += struct.pack("<I", 0)  # reserved

    assert len(header) == 32
    assert len(seg_cmd) == 72
    assert len(sect) == 80

    return header + seg_cmd + sect + text_data


# ──────────────────────────────────────────────
# TESTS DES UTILITAIRES
# ──────────────────────────────────────────────


class TestEntropieShannon:
    def test_entropie_vide(self):
        assert _calculer_entropie_shannon(b"") == 0.0

    def test_entropie_uniforme(self):
        """256 octets distincts → entropie maximale ≈ 8.0 bits."""
        donnees = bytes(range(256))
        entropie = _calculer_entropie_shannon(donnees)
        assert abs(entropie - 8.0) < 0.01

    def test_entropie_constante(self):
        """Données constantes → entropie = 0."""
        donnees = b"\x00" * 100
        entropie = _calculer_entropie_shannon(donnees)
        assert entropie == 0.0

    def test_entropie_intermediaire(self):
        """Données avec 2 valeurs équiprobables → entropie = 1.0 bit."""
        donnees = b"\x00\x01" * 50
        entropie = _calculer_entropie_shannon(donnees)
        assert abs(entropie - 1.0) < 0.01


class TestDetecterFormat:
    def test_elf(self):
        assert _detecter_format(b"\x7fELF" + b"\x00" * 60) == "elf"

    def test_pe(self):
        assert _detecter_format(b"MZ" + b"\x00" * 60) == "pe"

    def test_macho_64_le(self):
        assert _detecter_format(b"\xcf\xfa\xed\xfe" + b"\x00" * 60) == "macho"

    def test_macho_32_le(self):
        assert _detecter_format(b"\xce\xfa\xed\xfe" + b"\x00" * 60) == "macho"

    def test_macho_32_be(self):
        assert _detecter_format(b"\xfe\xed\xfa\xce" + b"\x00" * 60) == "macho"

    def test_macho_64_be(self):
        assert _detecter_format(b"\xfe\xed\xfa\xcf" + b"\x00" * 60) == "macho"

    def test_inconnu(self):
        assert _detecter_format(b"\x00\x00\x00\x00") == "inconnu"

    def test_trop_court(self):
        assert _detecter_format(b"\x7f") == "inconnu"


class TestDetecterShellcode:
    def test_int80(self):
        donnees = b"\x90\x90\xcd\x80\x90"
        offsets = _detecter_shellcode(donnees)
        assert 2 in offsets

    def test_syscall(self):
        donnees = b"\x90\x0f\x05\x90"
        offsets = _detecter_shellcode(donnees)
        assert 1 in offsets

    def test_pas_de_shellcode(self):
        donnees = b"\x90" * 100
        offsets = _detecter_shellcode(donnees)
        assert offsets == []

    def test_multiple_patterns(self):
        donnees = b"\xcd\x80\x90\x0f\x05"
        offsets = _detecter_shellcode(donnees)
        assert len(offsets) == 2


# ──────────────────────────────────────────────
# TESTS DE PARSING ELF
# ──────────────────────────────────────────────


class TestParserELF:
    def test_elf_minimal_64(self):
        donnees = _creer_elf_minimal_64()
        sections, has_symtab = _parser_elf(donnees)
        # Should find at least the .text section (shstrtab may also appear)
        noms = [s.nom for s in sections]
        assert ".text" in noms
        assert not has_symtab  # No symbol table in minimal ELF

    def test_elf_tronque(self):
        sections, has_symtab = _parser_elf(b"\x7fELF\x02\x01")
        assert sections == []

    def test_elf_vide(self):
        sections, has_symtab = _parser_elf(b"")
        assert sections == []


class TestParserPE:
    def test_pe_minimal(self):
        donnees = _creer_pe_minimal()
        sections, has_symtab = _parser_pe(donnees)
        assert len(sections) == 1
        assert sections[0].nom == ".text"
        assert not has_symtab

    def test_pe_tronque(self):
        sections, has_symtab = _parser_pe(b"MZ" + b"\x00" * 10)
        assert sections == []


class TestParserMachO:
    def test_macho_minimal_64(self):
        donnees = _creer_macho_minimal_64()
        sections, has_symtab = _parser_macho(donnees)
        # Should find the __text section
        noms = [s.nom for s in sections]
        assert "__text" in noms
        assert not has_symtab

    def test_macho_tronque(self):
        sections, has_symtab = _parser_macho(b"\xcf\xfa\xed\xfe" + b"\x00" * 10)
        assert sections == []


# ──────────────────────────────────────────────
# TESTS DU BACKEND COMPLET
# ──────────────────────────────────────────────


class TestElfLightBackend:
    def test_analyser_elf_minimal(self):
        donnees = _creer_elf_minimal_64()
        chemin = _creer_fichier_temp(donnees, suffix=".elf")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            assert resultat.fichier == chemin
            assert len(resultat.fonctions) > 0
            # The .text section should appear
            noms = [f.nom for f in resultat.fonctions]
            assert ".text" in noms
        finally:
            _safe_unlink(chemin)

    def test_analyser_pe_minimal(self):
        donnees = _creer_pe_minimal()
        chemin = _creer_fichier_temp(donnees, suffix=".exe")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            assert len(resultat.fonctions) == 1
            assert resultat.fonctions[0].nom == ".text"
        finally:
            _safe_unlink(chemin)

    def test_analyser_macho_minimal(self):
        donnees = _creer_macho_minimal_64()
        chemin = _creer_fichier_temp(donnees, suffix=".dylib")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            noms = [f.nom for f in resultat.fonctions]
            assert "__text" in noms
        finally:
            _safe_unlink(chemin)

    def test_analyser_format_inconnu(self):
        chemin = _creer_fichier_temp(b"\x00\x01\x02\x03", suffix=".bin")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            assert any(
                "non reconnu" in a.message for a in resultat.annotations
            )
        finally:
            _safe_unlink(chemin)

    def test_analyser_fichier_inexistant(self):
        backend = ElfLightBackend("/tmp/phi_inexistant_12345.elf")
        resultat = backend.analyser()
        assert resultat.fonctions == []

    def test_detection_binaire_strippe(self):
        """Un ELF sans table de symboles génère une annotation INFO."""
        donnees = _creer_elf_minimal_64()
        chemin = _creer_fichier_temp(donnees, suffix=".elf")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            stripped_annotations = [
                a for a in resultat.annotations if "strippé" in a.message
            ]
            assert len(stripped_annotations) == 1
            assert stripped_annotations[0].niveau == "INFO"
        finally:
            _safe_unlink(chemin)

    def test_detection_shellcode_dans_text(self):
        """Shellcode dans .text génère une annotation CRITICAL."""
        # Create an ELF with shellcode directly embedded in .text section
        # We build a new ELF with shellcode in the text data
        shellcode = b"\x90" * 10 + b"\xcd\x80" + b"\x0f\x05" + b"\xc3"
        # Replace the text_data in the ELF creation
        import struct as _s

        elf = _creer_elf_minimal_64()
        # The .text data in _creer_elf_minimal_64 is b"\x90"*32 + b"\xc3"
        # Find the NOP sled in the binary and replace it
        nop_sled = b"\x90" * 32 + b"\xc3"
        idx = elf.find(nop_sled)
        if idx >= 0:
            pad_len = max(0, 33 - len(shellcode))
            elf = elf[:idx] + shellcode + b"\x90" * pad_len + elf[idx + 33 :]

        chemin = _creer_fichier_temp(elf, suffix=".elf")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            shellcode_annotations = [
                a for a in resultat.annotations if "SHELLCODE" in a.message
            ]
            assert len(shellcode_annotations) >= 1
            assert shellcode_annotations[0].niveau == "CRITICAL"
        finally:
            _safe_unlink(chemin)

    def test_oudjat_est_section_plus_complexe(self):
        """L'oudjat est la section avec la complexité la plus élevée."""
        donnees = _creer_elf_minimal_64()
        chemin = _creer_fichier_temp(donnees, suffix=".elf")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            if resultat.fonctions:
                max_c = max(f.complexite for f in resultat.fonctions)
                assert resultat.oudjat is not None
                assert resultat.oudjat.complexite == max_c
        finally:
            _safe_unlink(chemin)

    def test_entropie_moyenne_calculee(self):
        """L'entropie Shannon est calculée pour le binaire."""
        donnees = _creer_elf_minimal_64()
        chemin = _creer_fichier_temp(donnees, suffix=".elf")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            assert resultat.shannon_entropy >= 0.0
        finally:
            _safe_unlink(chemin)

    def test_phi_ratio_calcule(self):
        """Le phi_ratio est calculé à partir des tailles de sections."""
        donnees = _creer_elf_minimal_64()
        chemin = _creer_fichier_temp(donnees, suffix=".elf")
        try:
            backend = ElfLightBackend(chemin)
            resultat = backend.analyser()
            assert resultat.phi_ratio >= 0.0
        finally:
            _safe_unlink(chemin)


class TestAnalyserSection:
    def test_section_normale(self):
        section = _SectionInfo(
            nom=".data",
            offset=0x1000,
            taille=100,
            donnees=b"\x00" * 100,
            executable=False,
            writable=True,
            flags=0x3,
        )
        metrique, annotations = _analyser_section(section)
        assert metrique.nom == ".data"
        assert metrique.nb_lignes == 100
        assert len(annotations) == 0  # Low entropy, not exec, not W+X

    def test_section_haute_entropie(self):
        """Section avec entropie > seuil critique génère une annotation."""
        donnees = bytes(range(256)) * 4  # entropie ≈ 8.0 bits
        section = _SectionInfo(
            nom=".packed",
            offset=0,
            taille=len(donnees),
            donnees=donnees,
            executable=False,
            writable=False,
            flags=0,
        )
        metrique, annotations = _analyser_section(section)
        entropy_annots = [a for a in annotations if "ENTROPY" in a.message]
        assert len(entropy_annots) >= 1
        assert entropy_annots[0].niveau == "CRITICAL"

    def test_section_wx(self):
        """Section W+X génère une annotation WARNING."""
        section = _SectionInfo(
            nom=".jit",
            offset=0,
            taille=64,
            donnees=b"\x90" * 64,
            executable=True,
            writable=True,
            flags=0,
        )
        _, annotations = _analyser_section(section)
        wx_annots = [a for a in annotations if "W+X" in a.message]
        assert len(wx_annots) == 1
        assert wx_annots[0].niveau == "WARNING"


# ──────────────────────────────────────────────
# TEST D'INTÉGRATION : AnalyseurPhi route vers ELF
# ──────────────────────────────────────────────


class TestAnalyseurPhiELF:
    def test_analyseur_route_vers_elf_backend(self):
        """AnalyseurPhi sélectionne ElfLightBackend pour les fichiers .elf."""
        from phi_complexity.analyseur import AnalyseurPhi
        from phi_complexity.backends.elf_light import ElfLightBackend

        donnees = _creer_elf_minimal_64()
        chemin = _creer_fichier_temp(donnees, suffix=".elf")
        try:
            analyseur = AnalyseurPhi(chemin)
            assert isinstance(analyseur.backend, ElfLightBackend)
        finally:
            _safe_unlink(chemin)

    def test_analyseur_route_exe(self):
        """AnalyseurPhi sélectionne ElfLightBackend pour les fichiers .exe."""
        from phi_complexity.analyseur import AnalyseurPhi
        from phi_complexity.backends.elf_light import ElfLightBackend

        donnees = _creer_pe_minimal()
        chemin = _creer_fichier_temp(donnees, suffix=".exe")
        try:
            analyseur = AnalyseurPhi(chemin)
            assert isinstance(analyseur.backend, ElfLightBackend)
        finally:
            _safe_unlink(chemin)

    def test_analyseur_route_so(self):
        """AnalyseurPhi sélectionne ElfLightBackend pour les fichiers .so."""
        from phi_complexity.analyseur import AnalyseurPhi
        from phi_complexity.backends.elf_light import ElfLightBackend

        donnees = _creer_elf_minimal_64()
        chemin = _creer_fichier_temp(donnees, suffix=".so")
        try:
            analyseur = AnalyseurPhi(chemin)
            assert isinstance(analyseur.backend, ElfLightBackend)
        finally:
            _safe_unlink(chemin)
