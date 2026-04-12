#include <stdio.h>
#include <string.h>

/*
 * moteur_c.c — Exemple de moteur C pour phi-complexity.
 *
 * Ce fichier illustre la détection ET la correction de CWE-134
 * (Format String Vulnerability) par le backend C de phi-complexity.
 *
 * CWE-134: Utilisation d'une chaîne de format contrôlée de l'extérieur.
 * Risque : lecture/écriture arbitraire en mémoire via %n, %x, etc.
 *
 * Toutes les fonctions ci-dessous utilisent des formats LITTÉRAUX.
 * Les versions vulnérables sont documentées en commentaire uniquement.
 *
 * Références :
 *   https://cwe.mitre.org/data/definitions/134.html
 *   https://owasp.org/www-community/attacks/Format_string_attack
 */

/* ── FONCTIONS SÛRES ─────────────────────────────────── */

void transformer_donnees(int count) {
    if (count > 0) {
        for (int i = 0; i < count; i++) {
            printf("Traitement %d\n", i);   /* OK : format littéral */
            if (i % 2 == 0) {
                for (int j = 0; j < 10; j++) {
                    printf("  - Sous-bloc %d\n", j);  /* OK */
                }
            }
        }
    }
}

void afficher_message_ok(const char *msg) {
    printf("%s\n", msg);       /* OK : format littéral, msg est un argument */
    fprintf(stderr, "%s", msg); /* OK */
}

/* ── FONCTIONS CORRIGÉES (ex-CWE-134) ───────────────── */

void journaliser_evenement(const char *message) {
    /*
     * Avant (VULNÉRABLE — CWE-134) :
     *     printf(message);
     * Un attaquant pouvait injecter %x, %n, etc. pour lire/écrire la pile.
     *
     * Correction : toujours utiliser un format littéral.
     */
    printf("%s", message);              /* CORRIGÉ — format littéral */
}

void log_erreur(const char *buffer) {
    /*
     * Avant (VULNÉRABLE — CWE-134) :
     *     fprintf(stderr, buffer);
     *     sprintf(buffer, buffer);
     *
     * Correction : format littéral pour fprintf.
     * L'appel sprintf(buffer, buffer) a été supprimé car il constituait
     * un double risque (CWE-134 + écrasement du buffer source).
     */
    fprintf(stderr, "%s", buffer);      /* CORRIGÉ — format littéral */
}

/* ── POINT D'ENTRÉE ──────────────────────────────────── */

int main(void) {
    printf("Initialisation du moteur C...\n");
    transformer_donnees(5);

    char buf[256];
    snprintf(buf, sizeof(buf), "test %d", 42);   /* OK : format littéral */
    afficher_message_ok(buf);

    /* Démonstration de la correction */
    journaliser_evenement("Ceci est un test\n");
    log_erreur("Erreur de test\n");
    return 0;
}
