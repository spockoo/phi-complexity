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

Merci de nous aider à maintenir la souveraineté et l'intégrité mathématique de ce code.
