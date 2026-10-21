import csv
import time
import agent
from config_test import creer_test


def convertir(depart, directions):
    if directions is None:
        return None
    chemin = [depart]
    for d in directions:
        dr, dc = agent.DIRECTIONS[d]
        r, c = chemin[-1]
        chemin.append((r + dr, c + dc))
    return chemin


def tester(nom, metrique):
    etat = agent.get_state()
    depart = tuple(etat["mission"]["start"])
    cible = tuple(etat["mission"]["target"])
    taille = etat["size"]
    directions = list(agent.DIRECTIONS) if etat["connectivity"] == 8 else ["N", "S", "E", "W"]

    explores = set()
    ancien_voisins = agent.voisins
    ancien_neighbors = agent.get_neighbors

    def compter_voisins(case, taille, directions):
        explores.add(case)
        yield from ancien_voisins(case, taille, directions)

    def compter_neighbors(case):
        explores.add(case)
        return ancien_neighbors(case)

    agent.voisins = compter_voisins
    agent.get_neighbors = compter_neighbors
    debut = time.perf_counter()
    try:
        if nom == "bfs":
            chemin = convertir(depart, agent.bfs(depart, cible, taille, directions))
        elif nom == "dfs":
            chemin = convertir(depart, agent.dfs(depart, cible, taille, directions))
        elif nom == "greedy":
            parents = agent.greedy(depart, cible, metrique)
            chemin = agent.reconstruct_path(parents, cible)
        elif nom == "dijkstra":
            parents, distances = agent.dijkstra(depart, cible)
            chemin = agent.reconstruct_path(parents, cible)
        elif nom == "astar":
            chemin = convertir(depart, agent.astar(depart, cible, metrique))
        else:
            raise ValueError("Algorithme inconnu")
    finally:
        temps = time.perf_counter() - debut
        agent.voisins = ancien_voisins
        agent.get_neighbors = ancien_neighbors

    cout = 0
    if chemin is not None:
        for i in range(len(chemin) - 1):
            for voisin in agent.get_neighbors(chemin[i]):
                if tuple(voisin["node"]) == chemin[i + 1]:
                    cout += voisin["cost"]
                    break

    resultat = {
        "algo": nom,
        "distance": metrique if nom in ("greedy", "astar") else "-",
        "temps_s": round(temps, 4),
        "steps": len(chemin) - 1 if chemin is not None else "echec",
        "explores": len(explores),
        "cout": round(cout, 2) if chemin is not None else "echec"
    }
    print(f"{nom:9} {resultat['distance']:10} | {resultat['temps_s']:7} s | "
          f"{str(resultat['steps']):>5} steps | {len(explores):>4} explores | cout {resultat['cout']}")
    return resultat


def comparer(taille, connectivite, forme="vide", epaisseur=1):
    print(f"\n=== {taille}x{taille}, voisins {connectivite}, {forme}, epaisseur {epaisseur} ===")
    lignes = []
    for nom in ["bfs", "dfs", "greedy", "dijkstra", "astar"]:
        creer_test(taille, connectivite, forme, epaisseur)
        metrique = "manhattan" if connectivite == 4 else "euclidean"
        r = tester(nom, metrique)
        r.update({"taille": taille, "connectivite": connectivite,
                  "obstacle": forme, "epaisseur": epaisseur})
        lignes.append(r)
    return lignes


if __name__ == "__main__":
    resultats = []

    resultats += comparer(12, 4)
    resultats += comparer(12, 8)

    resultats += comparer(8, 4)
    resultats += comparer(20, 4)

    resultats += comparer(12, 4, "u")
    resultats += comparer(12, 8, "u")

    for epaisseur in [1, 2, 3]:
        resultats += comparer(12, 4, "ligne", epaisseur)
        resultats += comparer(12, 8, "ligne", epaisseur)

    print("\n=== Comparaison des distances ===")
    for connectivite in [4, 8]:
        for metrique in ["manhattan", "euclidean", "chebyshev"]:
            for nom in ["greedy", "astar"]:
                creer_test(12, connectivite, "u")
                r = tester(nom, metrique)
                r.update({"taille": 12, "connectivite": connectivite,
                          "obstacle": "u", "epaisseur": 1})
                resultats.append(r)

    with open("resultats.csv", "w", newline="", encoding="utf-8") as fichier:
        colonnes = ["taille", "connectivite", "obstacle", "epaisseur",
                    "algo", "distance", "temps_s", "steps", "explores", "cout"]
        ecrivain = csv.DictWriter(fichier, fieldnames=colonnes)
        ecrivain.writeheader()
        ecrivain.writerows(resultats)
    print("\nResultats enregistres dans resultats.csv")
