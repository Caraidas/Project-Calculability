import time
import agent

W_VALUES = [1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2]


def grid_search():
    etat = agent.get_state()
    depart = tuple(etat["mission"]["start"])
    cible = tuple(etat["mission"]["target"])

    resultats = []

    for w in W_VALUES:
        explorees = set()
        get_neighbors_original = agent.get_neighbors
        def compter(case):
            explorees.add(case)
            return get_neighbors_original(case)

        agent.get_neighbors = compter

        debut = time.perf_counter()

        try:
            chemin = agent.astar(depart, cible, "euclidean", w)
        finally:
            agent.get_neighbors = get_neighbors_original

        temps = time.perf_counter() - debut

        if chemin is None:
            continue

        cout = 0
        position = depart

        for d in chemin:
            dr, dc = agent.DIRECTIONS[d]
            suivante = (position[0] + dr, position[1] + dc)

            for voisin in agent.get_neighbors(position):
                if tuple(voisin["node"]) == suivante:
                    cout += voisin["cost"]
                    break

            position = suivante

        resultats.append({
            "w": w,
            "cout": cout,
            "temps": temps,
            "explorees": len(explorees)
        })

    print("\nRESULTATS GRID SEARCH")

    for r in resultats:
        print(
            "w =", r["w"],
            "| cout =", round(r["cout"], 2),
            "| temps =", round(r["temps"], 4),
            "| explorees =", r["explorees"]
        )

    return resultats


if __name__ == "__main__":
    grid_search()