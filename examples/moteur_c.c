#include <stdio.h>
#include <string.h>

/*
 * moteur_c.c — Exemple de moteur C pour phi-complexity.
 *
 * Ce fichier illustre la détection de CWE-134 (Format String Vulnerability)
 * par le backend C de phi-complexity.
 *
 * CWE-134: Utilisation d'une chaîne de format contrôlée de l'extérieur.
 * Risque : lecture/écriture arbitraire en mémoire via %n, %x, etc.
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

/* ── FONCTIONS VULNÉRABLES (CWE-134) ────────────────── */

void journaliser_evenement(char *message) {
    /* CWE-134 : 'message' est utilisé directement comme format string.
     * Un attaquant peut injecter %x, %n, etc. pour lire/écrire la pile.
     * Correction : printf("%s", message);
     */
    printf(message);                /* VULNÉRABLE — CWE-134 */
}

void log_erreur(char *buffer) {
    fprintf(stderr, buffer);        /* VULNÉRABLE — CWE-134 */
    sprintf(buffer, buffer);        /* VULNÉRABLE — CWE-134 (double) */
}

/* ── POINT D'ENTRÉE ──────────────────────────────────── */

int main() {
    printf("Initialisation du moteur C...\n");
    transformer_donnees(5);

    char buf[256];
    snprintf(buf, sizeof(buf), "test %d", 42);   /* OK : format littéral */
    afficher_message_ok(buf);

    /* Démonstration de la vulnérabilité */
    journaliser_evenement("Ceci est un test\n");  /* Sûr à l'appel, mais la fonction est vulnérable */
    return 0;
}
