"""
phi_complexity/backends/elf_light.py — Backend souverain pour binaires natifs.

Analyse "Light" des formats ELF (Linux), PE (Windows) et Mach-O (macOS).
Extrait les métriques structurelles des sections pour l'analyse antivirale.
Zéro dépendances externes — Souveraineté totale.

Phase 16 du Morphic Phi Framework.
"""

from __future__ import annotations

import math
import os
import struct
from typing import Dict, List, Optional, Tuple

from ..analyseur import Annotation, MetriqueFonction, ResultatAnalyse
from ..core import distance_fibonacci
from .base import AnalyseurBackend

# ────────────────────────────────────────────────────────
# CONSTANTES MAGIQUES DES FORMATS BINAIRES
# ────────────────────────────────────────────────────────

_ELF_MAGIC = b"\x7fELF"
_PE_MZ_MAGIC = b"MZ"
_PE_SIGNATURE = b"PE\0\0"
_MACHO_MAGIC_32 = b"\xfe\xed\xfa\xce"
_MACHO_MAGIC_64 = b"\xcf\xfa\xed\xfe"
_MACHO_MAGIC_32_LE = b"\xce\xfa\xed\xfe"
_MACHO_MAGIC_64_BE = b"\xfe\xed\xfa\xcf"

# ────────────────────────────────────────────────────────
# SEUILS FIBONACCI POUR ANALYSE DE SECTIONS
# ────────────────────────────────────────────────────────

_SEUIL_ENTROPIE_CRITICAL = 7.0
_SEUIL_ENTROPIE_WARNING = 6.5
_SEUIL_SECTIONS_WARNING = 34   # Fibonacci(9)
_SEUIL_SECTIONS_CRITICAL = 55  # Fibonacci(10)
_SEUIL_SECTIONS_LILITH = 13   # Fibonacci(7)

# ────────────────────────────────────────────────────────
# SHELLCODE SIGNATURES
# ────────────────────────────────────────────────────────

_SHELLCODE_INT80 = b"\xcd\x80"
_SHELLCODE_SYSCALL = b"\x0f\x05"

# ────────────────────────────────────────────────────────
# DRAPEAUX DE SECTIONS ELF
# ────────────────────────────────────────────────────────

_SHF_WRITE = 0x1
_SHF_EXECINSTR = 0x4
_SHT_SYMTAB = 2
_SHT_DYNSYM = 11

# ────────────────────────────────────────────────────────
# DRAPEAUX PE
# ────────────────────────────────────────────────────────

_PE_SCN_MEM_EXECUTE = 0x20000000
_PE_SCN_MEM_WRITE = 0x80000000

# ────────────────────────────────────────────────────────
# TYPES DE SEGMENT MACH-O
# ────────────────────────────────────────────────────────

_LC_SEGMENT = 0x1
_LC_SEGMENT_64 = 0x19
_LC_SYMTAB = 0x2

# Protection flags Mach-O
_VM_PROT_WRITE = 0x02
_VM_PROT_EXECUTE = 0x04


# ────────────────────────────────────────────────────────
# STRUCTURES DE SECTIONS PARSÉES
# ────────────────────────────────────────────────────────


class _SectionInfo:
    """Informations extraites d'une section binaire."""

    __slots__ = (
        "nom",
        "offset",
        "taille",
        "donnees",
        "executable",
        "writable",
        "flags",
    )

    def __init__(
        self,
        nom: str,
        offset: int,
        taille: int,
        donnees: bytes,
        executable: bool = False,
        writable: bool = False,
        flags: int = 0,
    ) -> None:
        self.nom = nom
        self.offset = offset
        self.taille = taille
        self.donnees = donnees
        self.executable = executable
        self.writable = writable
        self.flags = flags


# ────────────────────────────────────────────────────────
# FONCTIONS UTILITAIRES
# ────────────────────────────────────────────────────────


def _calculer_entropie_shannon(donnees: bytes) -> float:
    """Calcule l'entropie de Shannon en bits par octet."""
    if not donnees:
        return 0.0
    longueur = len(donnees)
    compteurs: Dict[int, int] = {}
    for octet in donnees:
        compteurs[octet] = compteurs.get(octet, 0) + 1
    entropie = 0.0
    for compte in compteurs.values():
        probabilite = compte / longueur
        if probabilite > 0:
            entropie -= probabilite * math.log2(probabilite)
    return entropie


def _detecter_format(donnees: bytes) -> str:
    """Détecte le format binaire à partir des octets magiques."""
    if len(donnees) < 4:
        return "inconnu"
    if donnees[:4] == _ELF_MAGIC:
        return "elf"
    if donnees[:2] == _PE_MZ_MAGIC:
        return "pe"
    if donnees[:4] in (
        _MACHO_MAGIC_32,
        _MACHO_MAGIC_64,
        _MACHO_MAGIC_32_LE,
        _MACHO_MAGIC_64_BE,
    ):
        return "macho"
    return "inconnu"


def _detecter_shellcode(donnees: bytes) -> List[int]:
    """Détecte les patterns de shellcode et retourne leurs offsets."""
    offsets: List[int] = []
    pos = 0
    while pos < len(donnees) - 1:
        if donnees[pos : pos + 2] in (_SHELLCODE_INT80, _SHELLCODE_SYSCALL):
            offsets.append(pos)
        pos += 1
    return offsets


# ────────────────────────────────────────────────────────
# PARSEURS DE FORMATS
# ────────────────────────────────────────────────────────


def _parser_elf(donnees: bytes) -> Tuple[List[_SectionInfo], bool]:
    """Parse un binaire ELF et retourne les sections + indicateur symboles."""
    sections: List[_SectionInfo] = []
    has_symtab = False

    if len(donnees) < 16:
        return sections, has_symtab

    ei_class = donnees[4]
    ei_data = donnees[5]
    is_64 = ei_class == 2
    endian = "<" if ei_data == 1 else ">"

    try:
        if is_64:
            if len(donnees) < 0x40:
                return sections, has_symtab
            e_shoff = struct.unpack_from(f"{endian}Q", donnees, 0x28)[0]
            e_shentsize = struct.unpack_from(
                f"{endian}H", donnees, 0x3A
            )[0]
            e_shnum = struct.unpack_from(f"{endian}H", donnees, 0x3C)[0]
            e_shstrndx = struct.unpack_from(
                f"{endian}H", donnees, 0x3E
            )[0]
        else:
            if len(donnees) < 0x34:
                return sections, has_symtab
            e_shoff = struct.unpack_from(f"{endian}I", donnees, 0x20)[0]
            e_shentsize = struct.unpack_from(
                f"{endian}H", donnees, 0x2E
            )[0]
            e_shnum = struct.unpack_from(f"{endian}H", donnees, 0x30)[0]
            e_shstrndx = struct.unpack_from(
                f"{endian}H", donnees, 0x32
            )[0]

        if e_shoff == 0 or e_shnum == 0 or e_shentsize == 0:
            return sections, has_symtab

        # Lire la table des chaînes de noms de sections
        strtab_data = b""
        if e_shstrndx < e_shnum:
            strtab_offset = e_shoff + e_shstrndx * e_shentsize
            if is_64:
                sh_offset = struct.unpack_from(
                    f"{endian}Q", donnees, strtab_offset + 24
                )[0]
                sh_size = struct.unpack_from(
                    f"{endian}Q", donnees, strtab_offset + 32
                )[0]
            else:
                sh_offset = struct.unpack_from(
                    f"{endian}I", donnees, strtab_offset + 16
                )[0]
                sh_size = struct.unpack_from(
                    f"{endian}I", donnees, strtab_offset + 20
                )[0]
            end = sh_offset + sh_size
            if end <= len(donnees):
                strtab_data = donnees[sh_offset:end]

        for i in range(e_shnum):
            offset_entree = e_shoff + i * e_shentsize
            if offset_entree + e_shentsize > len(donnees):
                break

            if is_64:
                sh_name_idx = struct.unpack_from(
                    f"{endian}I", donnees, offset_entree
                )[0]
                sh_type = struct.unpack_from(
                    f"{endian}I", donnees, offset_entree + 4
                )[0]
                sh_flags = struct.unpack_from(
                    f"{endian}Q", donnees, offset_entree + 8
                )[0]
                sh_offset = struct.unpack_from(
                    f"{endian}Q", donnees, offset_entree + 24
                )[0]
                sh_size = struct.unpack_from(
                    f"{endian}Q", donnees, offset_entree + 32
                )[0]
            else:
                sh_name_idx = struct.unpack_from(
                    f"{endian}I", donnees, offset_entree
                )[0]
                sh_type = struct.unpack_from(
                    f"{endian}I", donnees, offset_entree + 4
                )[0]
                sh_flags = struct.unpack_from(
                    f"{endian}I", donnees, offset_entree + 8
                )[0]
                sh_offset = struct.unpack_from(
                    f"{endian}I", donnees, offset_entree + 16
                )[0]
                sh_size = struct.unpack_from(
                    f"{endian}I", donnees, offset_entree + 20
                )[0]

            if sh_type in (_SHT_SYMTAB, _SHT_DYNSYM):
                has_symtab = True

            # Extraire le nom de la section
            nom = _extraire_nom_section(strtab_data, sh_name_idx)

            # Ignorer les sections vides
            if sh_size == 0:
                continue

            end = sh_offset + sh_size
            raw = donnees[sh_offset:end] if end <= len(donnees) else b""

            sections.append(
                _SectionInfo(
                    nom=nom,
                    offset=sh_offset,
                    taille=sh_size,
                    donnees=raw,
                    executable=bool(sh_flags & _SHF_EXECINSTR),
                    writable=bool(sh_flags & _SHF_WRITE),
                    flags=sh_flags,
                )
            )
    except (struct.error, IndexError):
        pass

    return sections, has_symtab


def _extraire_nom_section(strtab: bytes, index: int) -> str:
    """Extrait un nom depuis la table des chaînes."""
    if not strtab or index >= len(strtab):
        return "<inconnu>"
    fin = strtab.find(b"\x00", index)
    if fin == -1:
        fin = len(strtab)
    nom = strtab[index:fin]
    try:
        return nom.decode("ascii", errors="replace")
    except (UnicodeDecodeError, ValueError):
        return "<inconnu>"


def _parser_pe(donnees: bytes) -> Tuple[List[_SectionInfo], bool]:
    """Parse un binaire PE (Portable Executable) et retourne les sections."""
    sections: List[_SectionInfo] = []
    has_symtab = False

    try:
        if len(donnees) < 0x40:
            return sections, has_symtab

        pe_offset = struct.unpack_from("<I", donnees, 0x3C)[0]

        if pe_offset + 4 > len(donnees):
            return sections, has_symtab
        if donnees[pe_offset : pe_offset + 4] != _PE_SIGNATURE:
            return sections, has_symtab

        # COFF Header suit la signature PE
        coff_offset = pe_offset + 4
        if coff_offset + 20 > len(donnees):
            return sections, has_symtab

        nb_sections = struct.unpack_from("<H", donnees, coff_offset + 2)[0]
        ptr_symtab = struct.unpack_from("<I", donnees, coff_offset + 8)[0]
        nb_symbols = struct.unpack_from("<I", donnees, coff_offset + 12)[0]
        optional_hdr_size = struct.unpack_from(
            "<H", donnees, coff_offset + 16
        )[0]

        if ptr_symtab != 0 and nb_symbols != 0:
            has_symtab = True

        # Table des sections
        section_table_offset = coff_offset + 20 + optional_hdr_size
        _PE_SECTION_ENTRY_SIZE = 40

        for i in range(nb_sections):
            entry = section_table_offset + i * _PE_SECTION_ENTRY_SIZE
            if entry + _PE_SECTION_ENTRY_SIZE > len(donnees):
                break

            nom_raw = donnees[entry : entry + 8]
            nom = nom_raw.split(b"\x00", 1)[0].decode(
                "ascii", errors="replace"
            )

            taille_raw = struct.unpack_from("<I", donnees, entry + 16)[0]
            offset_raw = struct.unpack_from("<I", donnees, entry + 20)[0]
            characteristics = struct.unpack_from(
                "<I", donnees, entry + 36
            )[0]

            taille = taille_raw if taille_raw > 0 else 0
            end = offset_raw + taille
            raw = (
                donnees[offset_raw:end]
                if taille > 0 and end <= len(donnees)
                else b""
            )

            sections.append(
                _SectionInfo(
                    nom=nom,
                    offset=offset_raw,
                    taille=taille,
                    donnees=raw,
                    executable=bool(
                        characteristics & _PE_SCN_MEM_EXECUTE
                    ),
                    writable=bool(characteristics & _PE_SCN_MEM_WRITE),
                    flags=characteristics,
                )
            )
    except (struct.error, IndexError):
        pass

    return sections, has_symtab


def _parser_macho(donnees: bytes) -> Tuple[List[_SectionInfo], bool]:
    """Parse un binaire Mach-O et retourne les sections."""
    sections: List[_SectionInfo] = []
    has_symtab = False

    try:
        if len(donnees) < 28:
            return sections, has_symtab

        magic = donnees[:4]
        if magic in (_MACHO_MAGIC_64, _MACHO_MAGIC_64_BE):
            is_64 = True
        elif magic in (_MACHO_MAGIC_32, _MACHO_MAGIC_32_LE):
            is_64 = False
        else:
            return sections, has_symtab

        # Déterminer l'endianness
        if magic in (_MACHO_MAGIC_32, _MACHO_MAGIC_64_BE):
            endian = ">"
        else:
            endian = "<"

        ncmds = struct.unpack_from(f"{endian}I", donnees, 16)[0]
        header_size = 32 if is_64 else 28
        pos = header_size

        for _ in range(ncmds):
            if pos + 8 > len(donnees):
                break

            cmd = struct.unpack_from(f"{endian}I", donnees, pos)[0]
            cmdsize = struct.unpack_from(
                f"{endian}I", donnees, pos + 4
            )[0]

            if cmdsize < 8:
                break

            if cmd == _LC_SYMTAB:
                has_symtab = True

            if cmd in (_LC_SEGMENT, _LC_SEGMENT_64):
                sections.extend(
                    _parser_macho_segment(
                        donnees, pos, endian, is_64
                    )
                )

            pos += cmdsize
    except (struct.error, IndexError):
        pass

    return sections, has_symtab


def _parser_macho_segment(
    donnees: bytes,
    pos: int,
    endian: str,
    is_64: bool,
) -> List[_SectionInfo]:
    """Parse un load command LC_SEGMENT/LC_SEGMENT_64."""
    sections: List[_SectionInfo] = []

    try:
        if is_64:
            nsects = struct.unpack_from(
                f"{endian}I", donnees, pos + 64
            )[0]
            sect_start = pos + 72
            sect_size = 80
        else:
            nsects = struct.unpack_from(
                f"{endian}I", donnees, pos + 48
            )[0]
            sect_start = pos + 56
            sect_size = 68

        for i in range(nsects):
            sect_pos = sect_start + i * sect_size
            if sect_pos + sect_size > len(donnees):
                break

            nom_raw = donnees[sect_pos : sect_pos + 16]
            nom = nom_raw.split(b"\x00", 1)[0].decode(
                "ascii", errors="replace"
            )

            if is_64:
                offset = struct.unpack_from(
                    f"{endian}I", donnees, sect_pos + 48
                )[0]
                taille = struct.unpack_from(
                    f"{endian}Q", donnees, sect_pos + 40
                )[0]
                flags = struct.unpack_from(
                    f"{endian}I", donnees, sect_pos + 76
                )[0]
            else:
                offset = struct.unpack_from(
                    f"{endian}I", donnees, sect_pos + 40
                )[0]
                taille = struct.unpack_from(
                    f"{endian}I", donnees, sect_pos + 32
                )[0]
                flags = struct.unpack_from(
                    f"{endian}I", donnees, sect_pos + 64
                )[0]

            # Protection: lire du segment parent
            if is_64:
                initprot = struct.unpack_from(
                    f"{endian}I", donnees, pos + 52
                )[0]
                maxprot = struct.unpack_from(
                    f"{endian}I", donnees, pos + 48
                )[0]
            else:
                initprot = struct.unpack_from(
                    f"{endian}I", donnees, pos + 40
                )[0]
                maxprot = struct.unpack_from(
                    f"{endian}I", donnees, pos + 36
                )[0]

            prot = initprot | maxprot
            executable = bool(prot & _VM_PROT_EXECUTE)
            writable = bool(prot & _VM_PROT_WRITE)

            if taille == 0:
                continue

            end = offset + taille
            raw = donnees[offset:end] if end <= len(donnees) else b""

            sections.append(
                _SectionInfo(
                    nom=nom,
                    offset=offset,
                    taille=taille,
                    donnees=raw,
                    executable=executable,
                    writable=writable,
                    flags=flags,
                )
            )
    except (struct.error, IndexError):
        pass

    return sections


# ────────────────────────────────────────────────────────
# BACKEND PRINCIPAL
# ────────────────────────────────────────────────────────


class ElfLightBackend(AnalyseurBackend):
    """
    Backend souverain pour les binaires natifs (ELF, PE, Mach-O).
    Analyse "Light" basée sur le parsing des en-têtes et sections.
    Extrait les métriques structurelles pour détection de patterns
    suspects (packing, shellcode, sections W+X).
    Zéro dépendances.
    """

    def analyser(self) -> ResultatAnalyse:
        """Exécute l'analyse structurelle du binaire."""
        resultat = ResultatAnalyse(fichier=self.fichier)

        try:
            taille_fichier = os.path.getsize(self.fichier)
            with open(self.fichier, "rb") as handle:
                donnees = handle.read()
        except (OSError, IOError):
            return resultat

        resultat.nb_lignes_total = taille_fichier
        fmt = _detecter_format(donnees)

        if fmt == "inconnu":
            resultat.annotations.append(
                Annotation(
                    ligne=0,
                    message="Format binaire non reconnu.",
                    niveau="INFO",
                    extrait=donnees[:16].hex(),
                    categorie="SOUVERAINETE",
                )
            )
            return resultat

        # Parser selon le format détecté
        sections, has_symtab = _parser_par_format(donnees, fmt)

        # Binaire strippé (pas de table de symboles)
        if not has_symtab:
            resultat.annotations.append(
                Annotation(
                    ligne=0,
                    message=(
                        f"Binaire {fmt.upper()} strippé : aucune table "
                        f"de symboles détectée."
                    ),
                    niveau="INFO",
                    extrait=f"format={fmt}",
                    categorie="SOUVERAINETE",
                )
            )

        # Nombre excessif de sections
        nb_sections = len(sections)
        if nb_sections > _SEUIL_SECTIONS_CRITICAL:
            resultat.annotations.append(
                Annotation(
                    ligne=0,
                    message=(
                        f"FIBONACCI-BIN : {nb_sections} sections "
                        f"(seuil critique: {_SEUIL_SECTIONS_CRITICAL}). "
                        f"Structure anormalement fragmentée."
                    ),
                    niveau="CRITICAL",
                    extrait=f"nb_sections={nb_sections}",
                    categorie="FIBONACCI",
                )
            )
        elif nb_sections > _SEUIL_SECTIONS_WARNING:
            resultat.annotations.append(
                Annotation(
                    ligne=0,
                    message=(
                        f"FIBONACCI-BIN : {nb_sections} sections "
                        f"(seuil: {_SEUIL_SECTIONS_WARNING}). "
                        f"Surveiller la fragmentation."
                    ),
                    niveau="WARNING",
                    extrait=f"nb_sections={nb_sections}",
                    categorie="FIBONACCI",
                )
            )
        elif nb_sections > _SEUIL_SECTIONS_LILITH:
            resultat.annotations.append(
                Annotation(
                    ligne=0,
                    message=(
                        f"LILITH-BIN : {nb_sections} sections "
                        f"(seuil Fibonacci: {_SEUIL_SECTIONS_LILITH}). "
                        f"Structure dense à surveiller."
                    ),
                    niveau="INFO",
                    extrait=f"nb_sections={nb_sections}",
                    categorie="LILITH",
                )
            )

        # Analyser chaque section
        entropies: List[float] = []
        for section in sections:
            metrique, annotations = _analyser_section(section)
            resultat.fonctions.append(metrique)
            resultat.annotations.extend(annotations)
            entropies.append(
                _calculer_entropie_shannon(section.donnees)
            )

        # Entropie globale du fichier
        if entropies:
            resultat.shannon_entropy = sum(entropies) / len(entropies)

        # Phi ratio et oudjat
        if resultat.fonctions:
            tailles = [f.nb_lignes for f in resultat.fonctions]
            taille_max = max(tailles)
            moyenne = sum(tailles) / len(tailles)
            resultat.phi_ratio = (
                taille_max / moyenne if moyenne > 0 else 0.0
            )

            for f in resultat.fonctions:
                f.phi_ratio = (
                    f.nb_lignes / moyenne if moyenne > 0 else 1.0
                )

            resultat.oudjat = max(
                resultat.fonctions, key=lambda f: f.complexite
            )

        return resultat


def _parser_par_format(
    donnees: bytes, fmt: str
) -> Tuple[List[_SectionInfo], bool]:
    """Dispatch le parsing selon le format détecté."""
    if fmt == "elf":
        return _parser_elf(donnees)
    if fmt == "pe":
        return _parser_pe(donnees)
    if fmt == "macho":
        return _parser_macho(donnees)
    return [], False


def _analyser_section(
    section: _SectionInfo,
) -> Tuple[MetriqueFonction, List[Annotation]]:
    """Analyse une section binaire et retourne métriques + annotations."""
    annotations: List[Annotation] = []

    entropie = _calculer_entropie_shannon(section.donnees)
    taille = section.taille

    # Complexité = entropie normalisée × log2(taille + 1).
    # Le +1 évite log2(0) et assure la continuité pour les petites sections.
    complexite = int(
        entropie * math.log2(taille + 1)
    ) if taille > 0 else 0

    metrique = MetriqueFonction(
        nom=section.nom or "<sans-nom>",
        ligne=section.offset,
        complexite=complexite,
        nb_args=0,
        nb_lignes=taille,
        profondeur_max=int(entropie),
        distance_fib=distance_fibonacci(taille),
        phi_ratio=1.0,
    )

    # ── Entropie suspecte : section probablement packée/chiffrée ──
    if entropie > _SEUIL_ENTROPIE_CRITICAL:
        annotations.append(
            Annotation(
                ligne=section.offset,
                message=(
                    f"ENTROPY-SUSPECTE : Section '{section.nom}' "
                    f"entropie={entropie:.2f} bits "
                    f"(seuil: {_SEUIL_ENTROPIE_CRITICAL}). "
                    f"Contenu probablement packé ou chiffré."
                ),
                niveau="CRITICAL",
                extrait=f"{section.nom} offset=0x{section.offset:x}",
                categorie="LILITH",
            )
        )
    elif entropie > _SEUIL_ENTROPIE_WARNING:
        annotations.append(
            Annotation(
                ligne=section.offset,
                message=(
                    f"ENTROPY-SUSPECTE : Section '{section.nom}' "
                    f"entropie={entropie:.2f} bits "
                    f"(seuil: {_SEUIL_ENTROPIE_WARNING}). "
                    f"Contenu dense à surveiller."
                ),
                niveau="WARNING",
                extrait=f"{section.nom} offset=0x{section.offset:x}",
                categorie="LILITH",
            )
        )

    # ── Shellcode dans section exécutable ──
    if section.executable and section.donnees:
        offsets_shellcode = _detecter_shellcode(section.donnees)
        if offsets_shellcode:
            annotations.append(
                Annotation(
                    ligne=section.offset,
                    message=(
                        f"SHELLCODE : Section '{section.nom}' "
                        f"contient {len(offsets_shellcode)} pattern(s) "
                        f"de syscall direct (int 0x80 / syscall). "
                        f"Indicateur d'injection potentielle."
                    ),
                    niveau="CRITICAL",
                    extrait=(
                        f"{section.nom} "
                        f"offsets={offsets_shellcode[:5]}"
                    ),
                    categorie="SUTURE",
                )
            )

    # ── Section W+X : écriture + exécution simultanées ──
    if section.writable and section.executable:
        annotations.append(
            Annotation(
                ligne=section.offset,
                message=(
                    f"W+X-SECTION : Section '{section.nom}' est à la "
                    f"fois inscriptible et exécutable. "
                    f"Indicateur de code auto-modifiant "
                    f"ou de protection mémoire insuffisante."
                ),
                niveau="WARNING",
                extrait=f"{section.nom} flags=0x{section.flags:x}",
                categorie="SUTURE",
            )
        )

    return metrique, annotations
