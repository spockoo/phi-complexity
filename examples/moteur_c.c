#include <stdio.h>

void transformer_donnees(int count) {
    if (count > 0) {
        for (int i = 0; i < count; i++) {
            printf("Traitement %d\n", i);
            if (i % 2 == 0) {
                // Simulation de complexité imbriquée
                for (int j = 0; j < 10; j++) {
                    printf("  - Sous-bloc %d\n", j);
                }
            }
        }
    }
}

int main() {
    printf("Initialisation du moteur C...\n");
    transformer_donnees(5);
    return 0;
}
