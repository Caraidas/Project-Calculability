import json
import sys
import urllib.request
from collections import deque

API = "http://localhost:8000"

# Directions de l'API : (décalage ligne, décalage colonne). N = vers le haut.
DIRECTIONS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1),
              "NE": (-1, 1), "NW": (-1, -1), "SE": (1, 1), "SW": (1, -1)}


def appel(methode, chemin, corps=None):
    donnees = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(API + chemin, data=donnees, method=methode,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as rep:
        return json.loads(rep.read())


def voisins(case, taille, directions):
    for d in directions:
        r, c = case[0] + DIRECTIONS[d][0], case[1] + DIRECTIONS[d][1]
        if 0 <= r < taille and 0 <= c < taille:
            yield d, (r, c)


def bfs(depart, cible, taille, directions):
    parents = {depart: None}
    file = deque([depart])
    while file:
        case = file.popleft()
        if case == cible:
            break
        for d, v in voisins(case, taille, directions):
            if v not in parents:
                parents[v] = (case, d)
                file.append(v)
    return reconstruire(parents, cible)


def dfs(depart, cible, taille, directions):
    parents = {depart: None}
    pile, vues = [depart], set()
    while pile:
        case = pile.pop()
        if case in vues:
            continue
        vues.add(case)
        if case == cible:
            break
        for d, v in voisins(case, taille, directions):
            if v not in vues:
                parents[v] = (case, d)
                pile.append(v)
    return reconstruire(parents, cible)


def reconstruire(parents, cible):
    """Remonte de la cible au départ pour obtenir la liste des directions."""
    chemin, case = [], cible
    while parents[case] is not None:
        case, d = parents[case]
        chemin.append(d)
    return chemin[::-1]


if __name__ == "__main__":
    algo = sys.argv[1] if len(sys.argv) > 1 else "bfs"

    etat = appel("GET", "/state")
    m = etat["mission"]
    appel("POST", "/mission", {"start": m["start"], "target": m["target"],
                               "threshold": m["threshold"], "agent": m["agent"]})
    directions = list(DIRECTIONS) if etat["connectivity"] == 8 else ["N", "S", "E", "W"]

    chercher = bfs if algo == "bfs" else dfs
    chemin = chercher(tuple(m["start"]), tuple(m["target"]), etat["size"], directions)
    print(f"{algo.upper()} : {len(chemin)} déplacements -> {' '.join(chemin)}")

    for d in chemin:
        rep = appel("POST", f"/agents/{m['agent']}/move/{d}")
        print(f"{d:<2} -> {rep['pose']}  total {rep['total_weight']:g}")
        if rep["mission"]["status"] != "running":
            break

    print(appel("GET", "/mission")["message"])
