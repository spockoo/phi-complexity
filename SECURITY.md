# Politique de Sécurité - Phi-Complexity

Cette politique définit les protocoles de sécurité pour le projet `phi-complexity`, un système d'analyse statique et d'auto-évolution basé sur les invariants mathématiques du nombre d'or (φ).

## Versions Supportées

Compte tenu de la nature expérimentale et auto-évolutive du code, seule la branche principale la plus récente est activement maintenue pour les correctifs de sécurité.


| Version | Supportée           |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2.0 | :x:                |

## Signalement d'une Vulnérabilité

La sécurité de ce projet est critique car le moteur possède des permissions d'écriture automatique sur le dépôt via GitHub Actions.

**Ne publiez jamais de vulnérabilité publiquement dans une "Issue".**

Si vous découvrez une faille (injection AST, escalade de privilèges via le bot, etc.), veuillez suivre ces étapes :

1.  Envoyez un courriel détaillé à : **tiloup777@outlook.fr**
2.  Décrivez la nature de la faille et fournissez un exemple de code (PoC) si possible.
3.  Une réponse vous sera envoyée sous **48 heures** pour confirmer la réception du rapport.

## Processus de Correction

Une fois la faille confirmée :
- Un correctif sera développé en priorité absolue.
- Une nouvelle version sera déployée pour stabiliser le ratio $\phi$ et sécuriser les permissions du bot.
- Vous serez crédité pour la découverte (sauf si vous souhaitez rester anonyme).

## Gestion des Secrets

- Ne commitez jamais un token GitHub (ex: `ADMIN_TOKEN`) dans le dépôt.
- Utilisez des variables d'environnement ou GitHub Actions Secrets.
- Le fichier `.env.example` sert uniquement de modèle et ne doit contenir aucune valeur sensible.
- Si un token a fuité, révoquez-le immédiatement et régénérez-en un nouveau.

## Écosystème d'Audit Sécurité (Phase 22)

Le dépôt active désormais une chaîne d'audit sécurité unifiée :

- **Séparation démo vs production** : les exemples pédagogiques vulnérables (`examples/`) ne polluent plus le scan Flawfinder principal.
- **Pipeline unifié** : la commande `phi shield` fusionne :
  - annotations sécurité de `phi-complexity`,
  - résultats SARIF externes (ex: Flawfinder).
- **Score et gate CI** : un score de sécurité est calculé et le workflow échoue si :
  - le score est sous le seuil (`--min-security-score`),
  - ou s'il reste des findings bloquants sur la surface production.
- **Journal d'audit** : chaque exécution `shield` est tracée dans `.phi/audit_trail.jsonl`.

Exemple local :

```bash
phi shield ./phi_complexity \
  --sarif flawfinder_results.sarif \
  --output .phi/security_audit.json \
  --min-security-score 70
```

## CI Auto-Diagnostic — Mode observabilité vs blocage

Le workflow `ci-auto-diagnostic.yml` supporte maintenant deux modes :

- `PHI_CI_RESONANCE_MODE=observe` (défaut) : mesure + classification, sans blocage.
- `PHI_CI_RESONANCE_MODE=block` : blocage actif si la résonance passe sous le seuil dynamique.

Variables associées :

- `PHI_CI_RESONANCE_MIN` : plancher du seuil dynamique.
- `PHI_CI_RESONANCE_MAX` : plafond du seuil dynamique.
- `PHI_CI_RESONANCE_MARGIN` : marge retranchée à la baseline historique.
- `PHI_CI_RESONANCE_WINDOW` : taille de fenêtre historique utilisée.

Les faux positifs opérationnels (ex: auto-échec de gate en calibration) sont classés
`OPERATIONAL_FALSE_POSITIVE` et ne déclenchent pas de blocage en mode dynamique.

## Provenance, attestations et gouvernance

Le module `phi_complexity.securite` inclut maintenant :

- **journal chaîné** (`JournalAudit.prev_hash`) pour l'intégrité append-only ;
- **attestations signées** offline-first (`signer_attestation` / `verifier_attestation`) ;
- **rotation/révocation de clés** (`RegistreClesAttestation`) ;
- **score de risque global unifié** (`calculer_score_risque_global`) ;
- **politiques de gate** (`evaluer_politique_gouvernance`) avec profils `oss`, `strict`, `enterprise` ;
- **dossier de preuve** (`construire_dossier_preuve`) pour centraliser les artefacts d'audit.

## Chasse aux Menaces Éthique (Phase 22+)

Le projet intègre désormais des outils de chasse aux menaces (threat hunting) éthiques :

### Workflows de sécurité

| Workflow | Fichier | Description |
|---|---|---|
| Flawfinder | `flawfinder.yml` | Scan C/C++ (production uniquement, hors exemples) |
| Dependency Review | `security.yml` | Revue des dépendances sur les PR |
| Threat Hunter | `threat-hunter.yml` | Chasse automatisée (CWE + Sentinel + IoC) |
| Sentinel SARIF | `sentinel-sarif.yml` | Export findings vers GitHub Security tab |
| Commit Risk | `commit-risk.yml` | Analyse bayésienne du risque par commit |

### Modules de détection

- **phi_complexity/backends/c_rust_light.py** : Détection CWE-134 (format string) en C/C++/Rust.
- **phi_complexity/sentinel/** : Pipeline comportemental en 5 couches (host → telemetry → behavior → bayesian → response).
- **phi_complexity/securite.py** : Signatures SHA-256, journal d'audit immuable, SBOM.

### Philosophie

> L'intelligence artificielle doit être un bouclier, pas une épée.
> Toute détection est documentée, explicable et partageable (IoC OSS).
> Aucune donnée identifiante n'est collectée. Souveraineté totale.

Merci de nous aider à maintenir la souveraineté et l'intégrité mathématique de ce code.
