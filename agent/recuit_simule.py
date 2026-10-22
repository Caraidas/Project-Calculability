import random


def voisins_du_poids(w, pas, w_min):
    liste_voisins = []
    for w_voisin in (w - pas, w + pas):
        w_voisin = round(w_voisin, 2)  # évite les 2.6000000000000005
        if w_voisin >= w_min:
            liste_voisins.append(w_voisin)
    return liste_voisins


def recuit_simule(fonction_F, w_depart=2.4, pas=0.2, w_min=0.0,
                  temperature_depart=1.0, refroidissement=0.85, nb_iterations=100):
    # On garde en mémoire les w déjà évalués pour ne pas relancer A* à chaque fois
    deja_evalues = {}

    def evaluer(w):
        if w not in deja_evalues:
            deja_evalues[w] = fonction_F(w)
        return deja_evalues[w]

    w_courant = w_depart
    F_courant = evaluer(w_courant)
    meilleur_w, meilleur_F = w_courant, F_courant
    temperature = temperature_depart
    historique = [(0, temperature, None, "départ", w_courant, F_courant)]

    for iteration in range(1, nb_iterations + 1):
        e = random.random()  # tirage aléatoire dans [0, 1]
        voisins = voisins_du_poids(w_courant, pas, w_min)

        if e <= temperature:
            # Exploration
            w_courant = random.choice(voisins)
            F_courant = evaluer(w_courant)
            choix = "voisin au hasard"
        else:
            # Hill climbing
            meilleur_voisin = min(voisins, key=evaluer)
            if evaluer(meilleur_voisin) < F_courant:
                w_courant = meilleur_voisin
                F_courant = evaluer(w_courant)
                choix = "hill climbing"
            else:
                choix = "optimum local"

        # On retient la meilleure solution rencontrée depuis le début
        if F_courant < meilleur_F:
            meilleur_w, meilleur_F = w_courant, F_courant

        historique.append((iteration, temperature, e, choix, w_courant, F_courant))
        temperature = temperature * refroidissement  # refroidissement

    return meilleur_w, meilleur_F, historique
