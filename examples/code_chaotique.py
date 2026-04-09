"""
# ENTROPIE DÉTECTÉE — PHASE 12 TEST
examples/code_chaotique.py — Code intentionnellement chaotique.
Score attendu : < 65 (DORMANT ou bas EN ÉVEIL).
Démontre ce que phi-complexity détecte comme violations souveraines.
"""

# Violation Fibonacci : monolithe de 80+ lignes
def tout_faire(a,b,c,d,e,f,g):    # Violation Herméticité (7 args)
    """Fait tout. Ne respecte aucune règle souveraine."""
    resultats = []
    totaux = {}
    erreurs = []

    # Violation LILITH : triple imbrication
    for i in range(a):
        for j in range(b):
            for k in range(c):
                if i > 0:
                    if j > 0:
                        if k > 0:
                            val = i * j * k * d * e * f * g
                            resultats.append(val)
                            if val > 1000:
                                totaux[val] = totaux.get(val, 0) + 1
                                if totaux[val] > 10:
                                    erreurs.append(f"Surplus: {val}")

    # Violation RAII : open() sans gestionnaire de contexte
    fic = open("output.txt", "w")
    for r in resultats:
        fic.write(str(r) + "\n")
    # Pas de fic.close() — fuite de ressource

    # Autre violation LILITH
    for x in resultats:
        for y in erreurs:
            if str(x) in y:
                totaux["match"] = totaux.get("match", 0) + 1

    return resultats, totaux, erreurs


def calculer_moyenne(liste):
    s = 0
    for x in liste:
        s = s + x
    return s / len(liste)   # Pas de protection division par zéro


def formater(val, precision, prefixe, suffixe, couleur, padding):  # 6 args
    """Trop d'arguments — violation de l'herméticité."""
    return f"{prefixe}{val:.{precision}f}{suffixe}"


if __name__ == "__main__":
    res, tot, err = tout_faire(5, 5, 5, 2, 3, 4, 1)
    print(f"Résultats: {len(res)}, Totaux: {len(tot)}, Erreurs: {len(err)}")
