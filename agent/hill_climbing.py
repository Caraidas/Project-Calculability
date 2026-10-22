
import agent
from config_test import creer_test

POIDS_MIN = 1
POIDS_MAX = 5
PAS = 0.5
DEPART = 2


def evaluer(poids, cout_optimal):
    creer_test(8, 8)

    etat = agent.get_state()
    depart = tuple(etat["mission"]["start"])
    cible = tuple(etat["mission"]["target"])

    # Compter les cases explorees
    explores = set()
    ancien = agent.get_neighbors

    def compter(case):
        explores.add(case)
        return ancien(case)

    agent.get_neighbors = compter

    try:
        directions = agent.astar(depart, cible, "euclidean", poids)
    finally:
        agent.get_neighbors = ancien

    if directions is None:
        return 1000000, 0, 0

    # Transformer les directions en chemin
    chemin = [depart]

    for d in directions:
        dr, dc = agent.DIRECTIONS[d]
        r, c = chemin[-1]
        chemin.append((r + dr, c + dc))

    # Calculer le cout reel du chemin
    cout = 0

    for i in range(len(chemin) - 1):
        for voisin in agent.get_neighbors(chemin[i]):
            if tuple(voisin["node"]) == chemin[i + 1]:
                cout += voisin["cost"]
                break

    # Minimiser l'exploration, sans chemin trop cher
    score = len(explores)

    if cout > 1.25 * cout_optimal:
        score += 10000

    return score, len(explores), cout


def cout_dijkstra():
    creer_test(8, 8)

    etat = agent.get_state()
    depart = tuple(etat["mission"]["start"])
    cible = tuple(etat["mission"]["target"])

    parents, distances = agent.dijkstra(depart, cible)

    return distances[cible]


def hill_climbing():
    optimal = cout_dijkstra()

    poids = DEPART
    score, explores, cout = evaluer(poids, optimal)

    historique = [(poids, score, explores, cout)]

    print("Cout optimal :", optimal)
    print("Depart :", poids, "| score :", score)

    while True:
        meilleur_poids = poids
        meilleur_score = score
        meilleur_explores = explores
        meilleur_cout = cout

        # Les deux voisins du poids actuel
        voisins = [poids - PAS, poids + PAS]

        for candidat in voisins:
            if candidat < POIDS_MIN or candidat > POIDS_MAX:
                continue

            s, n, c = evaluer(candidat, optimal)
            historique.append((candidat, s, n, c))

            print(
                "Test w =", candidat,
                "| score =", s,
                "| explores =", n,
                "| cout =", round(c, 2)
            )

            if s < meilleur_score:
                meilleur_poids = candidat
                meilleur_score = s
                meilleur_explores = n
                meilleur_cout = c

        # Aucun voisin n'est meilleur : on s'arrete
        if meilleur_poids == poids:
            break

        poids = meilleur_poids
        score = meilleur_score
        explores = meilleur_explores
        cout = meilleur_cout

        print("Nouveau poids choisi :", poids)

    print("\nRESULTAT FINAL")
    print("Meilleur poids :", poids)
    print("Score :", score)
    print("Cases explorees :", explores)
    print("Cout du chemin :", round(cout, 2))

    return poids, historique


if __name__ == "__main__":
    hill_climbing()
