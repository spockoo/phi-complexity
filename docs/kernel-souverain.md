# Noyau Souverain — Guide Arch Linux 🐧

Guide de construction d'un noyau Linux "souverain" sur Arch Linux : optimisation native, durcissement sécuritaire, chiffrement intégral et minimalisme des dépendances.

---

## 1. Base — `linux-cachyos` comme point de départ

`linux-cachyos` (disponible sur l'AUR) est le point de départ recommandé car il intègre déjà :

- **BORE scheduler** (Burst-Oriented Response Enhancer) — réactivité accrue sous charge intermittente
- **BBRv3** — algorithme de contrôle de congestion TCP
- **Compression zstd** pour les modules et l'initramfs
- Patchs de performance `sched_ext`, `per-VMA locks`, `LRNG`

```bash
# Installer les outils AUR
sudo pacman -S base-devel git

# Cloner le PKGBUILD CachyOS
git clone https://aur.archlinux.org/linux-cachyos.git
cd linux-cachyos
```

---

## 2. Compilation Native (`-march=native`)

Exploiter les jeux d'instructions spécifiques au processeur local (AVX2, AVX-512, etc.) via le système de construction Arch (ABS).

### Activation dans le `.config`

```bash
make menuconfig
# Processor type and features → Processor family → Native optimizations (MNATIVE_INTEL / MNATIVE_AMD)
```

Équivalent en mode non-interactif :

```bash
# Pour Intel
scripts/config --enable CONFIG_MNATIVE_INTEL

# Pour AMD
scripts/config --enable CONFIG_MNATIVE_AMD
```

### Flags de compilation dans le PKGBUILD

Éditer le fichier `PKGBUILD`, dans la fonction `build()` :

```bash
export CFLAGS="$CFLAGS -march=native -O2 -pipe"
export CXXFLAGS="$CXXFLAGS -march=native -O2 -pipe"
```

> **Note** : `-march=native` détecte automatiquement les capacités du CPU à la compilation. Le binaire résultant **ne sera pas portable** vers d'autres machines — c'est précisément l'objectif souverain.

---

## 3. Durcissement Sécuritaire

Fusionner les configurations de `linux-hardened` pour réduire la surface d'attaque.

### Options clés à activer

```bash
# Lockdown LSM — restreint l'accès root au noyau en mode EFI Secure Boot
scripts/config --enable CONFIG_SECURITY_LOCKDOWN_LSM
scripts/config --set-val CONFIG_SECURITY_LOCKDOWN_LSM_EARLY y

# Initialisation sécurisée de la mémoire allouée
scripts/config --enable CONFIG_INIT_ON_ALLOC_DEFAULT_ON
scripts/config --enable CONFIG_INIT_ON_FREE_DEFAULT_ON

# Randomisation de l'offset de pile noyau
scripts/config --enable CONFIG_RANDOMIZE_KSTACK_OFFSET_DEFAULT

# Forcer la signature des modules (aucun module non signé chargé)
scripts/config --enable CONFIG_MODULE_SIG_FORCE

# Désactiver le chargement de modules tiers non signés
scripts/config --disable CONFIG_MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS
```

### Audit des modules non utilisés

```bash
# Identifier les modules chargés sur votre système actuel
lsmod | awk '{print $1}' | sort > /tmp/modules_actifs.txt

# Dans le menuconfig, désactiver tout ce qui n'est pas dans cette liste
# Processor type → [désactiver les architectures inutiles]
# Device Drivers → [désactiver les pilotes matériels absents]
```

---

## 4. LUKS + Démarrage Sécurisé

### Partitionnement avec chiffrement LUKS2

```bash
# Créer une partition chiffrée
cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 --key-size 512 \
  --hash sha512 --pbkdf argon2id /dev/sdXY

# Ouvrir le volume
cryptsetup open /dev/sdXY cryptroot

# Créer les volumes LVM sur le volume chiffré
pvcreate /dev/mapper/cryptroot
vgcreate vg0 /dev/mapper/cryptroot
lvcreate -L 16G vg0 -n swap
lvcreate -l 100%FREE vg0 -n root
```

### Configuration `mkinitcpio.conf`

Fichier : `/etc/mkinitcpio.conf`

```bash
HOOKS=(base systemd autodetect modconf block keyboard encrypt lvm2 filesystems fsck)
COMPRESSION="zstd"
COMPRESSION_OPTIONS=(-19 --threads=0)
```

> Utiliser le hook `systemd` plutôt que `udev` pour une intégration native avec `systemd-cryptsetup`.

Regénérer l'initramfs :

```bash
mkinitcpio -P
```

### Configuration `systemd-boot`

Fichier : `/boot/loader/entries/arch-souverain.conf`

```ini
title   Arch Linux Souverain
linux   /vmlinuz-linux-cachyos
initrd  /amd-ucode.img
initrd  /initramfs-linux-cachyos.img
options rd.luks.name=<UUID-partition>=cryptroot rd.luks.options=discard \
        root=/dev/vg0/root rw \
        resume=UUID=<UUID-swap> \
        lsm=landlock,lockdown,yama,integrity,apparmor,bpf \
        quiet splash
```

Remplacer `<UUID-partition>` et `<UUID-swap>` par les UUID réels (`blkid`).

---

## 5. Gestion Mémoire — `zram`

Compression RAM en temps réel via `zram` : réduit l'usure des SSD, améliore la réactivité sous forte charge mémoire.

### Installation et configuration

```bash
sudo pacman -S zram-generator
```

Fichier : `/etc/systemd/zram-generator.conf`

```ini
[zram0]
zram-size = min(ram / 2, 8192)
compression-algorithm = zstd
swap-priority = 100
fs-type = swap
```

Activer :

```bash
systemctl daemon-reload
systemctl start systemd-zram-setup@zram0.service
systemctl enable systemd-zram-setup@zram0.service

# Vérifier
zramctl
swapon --show
```

> `zstd` offre un meilleur ratio compression/vitesse que `lz4` sur les workloads bureautiques modernes.

---

## 6. Réduction des Dépendances

### Audit du PKGBUILD avec `namcap`

```bash
sudo pacman -S namcap
namcap PKGBUILD
namcap linux-cachyos-*.pkg.tar.zst
```

`namcap` signale les dépendances manquantes, superflues ou les permissions incorrectes.

### Supprimer les `makedepends` inutiles

Inspecter le PKGBUILD et retirer les outils de compilation non utilisés :

```bash
# Vérifier chaque makedepend déclaré
grep makedepends PKGBUILD
# Retirer ceux dont aucun script build() ne fait usage
```

### Vérifier l'absence de blobs binaires

```bash
# Rechercher les références à des firmwares propriétaires dans la config
grep -r "firmware" .config | grep -v "^#"

# Lister les firmwares embarqués
grep "CONFIG_EXTRA_FIRMWARE=" .config

# Désactiver l'intégration de firmwares propriétaires dans le noyau
scripts/config --set-val CONFIG_EXTRA_FIRMWARE ""
```

Pour un système entièrement libre, désactiver :

```bash
scripts/config --disable CONFIG_FIRMWARE_IN_KERNEL
scripts/config --disable CONFIG_EXTRA_FIRMWARE
```

---

## 7. Analyse du Démarrage

Identifier les goulots d'étranglement avec `systemd-analyze` :

```bash
# Temps total de démarrage
systemd-analyze

# Cascade des services
systemd-analyze blame

# Graphe SVG du démarrage
systemd-analyze plot > boot.svg

# Vérifier les dépendances critiques
systemd-analyze critical-chain
```

---

## 8. Construction et Installation

```bash
# Dans le répertoire du PKGBUILD
makepkg -s --skippgpcheck

# Installer le noyau et les headers
sudo pacman -U linux-cachyos-*.pkg.tar.zst linux-cachyos-headers-*.pkg.tar.zst

# Mettre à jour le bootloader
bootctl update
```

---

## Récapitulatif des fichiers de configuration

| Fichier | Rôle |
|---|---|
| `PKGBUILD` | Flags de compilation natifs (`-march=native`) |
| `/boot/loader/entries/arch-souverain.conf` | Paramètres noyau, LUKS, hibernation |
| `/etc/mkinitcpio.conf` | Hooks initramfs (encrypt, lvm2, systemd) |
| `/etc/systemd/zram-generator.conf` | Swap compressé en RAM |
| `.config` (noyau) | Options de durcissement et de minimalisme |

---

## Commandes Essentielles

```bash
# Installer le noyau de base
sudo pacman -S linux-cachyos linux-cachyos-headers

# Installer les outils de chiffrement
sudo pacman -S cryptsetup lvm2

# Installer le gestionnaire de boot
sudo pacman -S systemd-boot

# Installer le générateur zram
sudo pacman -S zram-generator

# Audit du paquet
sudo pacman -S namcap
```
