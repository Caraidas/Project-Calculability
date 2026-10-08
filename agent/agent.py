import heapq
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

def distance(case, cible, metrique):
    rep = appel("GET", f"/distance?r1={case[0]}&c1={case[1]}&r2={cible[0]}&c2={cible[1]}&metric={metrique}")
    return rep["distance"]

def get_state():
    return appel("GET", "/state")

def get_neighbors(case):
    """Voisins accessibles d'une case, avec le coût de déplacement, d'après l'API."""
    return appel("GET", f"/nodes/{case[0]}/{case[1]}/neighbors")

def direction(case, voisin):
    for d, (dr, dc) in DIRECTIONS.items():
        if (case[0] + dr, case[1] + dc) == voisin:
            return d


def astar(depart, cible, metrique):
    parents = {depart: None}
    couts = {depart: 0}
    file = [(0, depart)]
    while file:
        _, case = heapq.heappop(file)
        if case == cible:
            break
        for v in get_neighbors(case):
            voisin = tuple(v["node"])
            cout = couts[case] + v["cost"]
            if voisin not in couts or cout < couts[voisin]:
                couts[voisin] = cout
                parents[voisin] = (case, direction(case, voisin))
                heapq.heappush(file, (cout + distance(voisin, cible, metrique), voisin))
    return reconstruire(parents, cible)


def greedy(start, target, metric="euclidean"):
    frontier = []
    visited = set()
    parent = {
        start: None
    }
    h_start = distance(start, target, metric)
    heapq.heappush(
        frontier,
        (h_start, start)
    )
    while frontier:
        h, current = heapq.heappop(frontier)
        if current in visited:
            continue
        visited.add(current)
        print("Exploration :", current, "| h =", round(h, 2)
        )
        if current == target:
            print("Cible trouvée !")
            return parent
        neighbors = get_neighbors(current)
        for neighbor_data in neighbors:
            neighbor = tuple(neighbor_data["node"])
            if neighbor not in visited:
                h_neighbor = distance(
                    neighbor,
                    target,
                    metric
                )
                heapq.heappush(
                    frontier,
                    (h_neighbor, neighbor)
                )
                if neighbor not in parent:
                    parent[neighbor] = current
    return None

def reconstruct_path(parent, target):

    if parent is None:
        return None
    if target not in parent:
        return None
    path = []
    current = target
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path

def path_cost(path):

    total_cost = 0
    for i in range(len(path) - 1):
        current = path[i]
        next_node = path[i + 1]
        neighbors = get_neighbors(current)
        for neighbor_data in neighbors:
            neighbor = tuple(neighbor_data["node"])
            if neighbor == next_node:
                cost = neighbor_data["cost"]
                total_cost += cost
                print(current, "->", next_node,"| coût =", cost
                )
                break
    return total_cost

def dijkstra(start, target):
    distances = {start: 0}
    parents = {start: None}
    queue = [(0, start)]
    while queue:
        current_cost, current_node = heapq.heappop(queue)
        if current_node == target:
            break
        neighbors = get_neighbors(current_node)
        for neighbor in neighbors:
            next_node = tuple(neighbor["node"])
            move_cost = neighbor["cost"]
            new_cost = current_cost + move_cost
            if next_node not in distances or new_cost < distances[next_node]:
                distances[next_node] = new_cost
                parents[next_node] = current_node
                heapq.heappush(queue, (new_cost, next_node))
    return parents, distances

def reconstruire(parents, cible):
    """Remonte de la cible au départ pour obtenir la liste des directions."""
    chemin, case = [], cible
    while parents[case] is not None:
        case, d = parents[case]
        chemin.append(d)
    return chemin[::-1]


if __name__ == "__main__":
    algo = sys.argv[1] if len(sys.argv) > 1 else "bfs"
    if algo == "greedy":
        state = get_state()
        start = tuple(
            state["mission"]["start"]
        )
        target = tuple(
            state["mission"]["target"]
        )
        print("Départ :", start)
        print("Cible  :", target)
        print("\nRecherche")

        parent = greedy(
            start,
            target
        )
        path = reconstruct_path(
            parent,
            target
        )
        print("RÉSULTAT")
        if path is None:
            print("Aucun chemin trouvé.")

        else:
            print("Chemin trouvé :")
            for node in path:
                print(node)
            print(
                "\nNombre de déplacements :",
                len(path) - 1
            )
            print("\nCoûts")
            total_cost = path_cost(path)
            print(
                "\nPoids total du chemin :",
                total_cost
            )
            print(
                "\nNombre de déplacements :",
                len(path) - 1
            )
        sys.exit()

    etat = appel("GET", "/state")
    m = etat["mission"]
    appel("POST", "/mission", {"start": m["start"], "target": m["target"],
                               "threshold": m["threshold"], "agent": m["agent"]})
    directions = list(DIRECTIONS) if etat["connectivity"] == 8 else ["N", "S", "E", "W"]
    if algo == "astar":
        metrique = "euclidean" if etat["connectivity"] == 8 else "manhattan"
        chemin = astar(tuple(m["start"]), tuple(m["target"]), metrique)
    elif algo == "dijkstra":
        start, target = tuple(m["start"]), tuple(m["target"])
        print("Start:", start)
        print("Target:", target)
        parents, distances = dijkstra(start, target)
        path = reconstruct_path(parents, target)
        print("\nOptimal path:", path)
        print("Number of steps:", len(path) - 1)
        print("Total cost:", distances[target])
        # Conversion du chemin (liste de cases) en directions pour la boucle de déplacement commune
        chemin = [direction(path[i], path[i + 1]) for i in range(len(path) - 1)]
    else:
        chercher = bfs if algo == "bfs" else dfs
        chemin = chercher(tuple(m["start"]), tuple(m["target"]), etat["size"], directions)
    print(f"{algo.upper()} : {len(chemin)} déplacements -> {' '.join(chemin)}")

    for d in chemin:
        rep = appel("POST", f"/agents/{m['agent']}/move/{d}")
        print(f"{d:<2} -> {rep['pose']}  total {rep['total_weight']:g}")
        if rep["mission"]["status"] != "running":
            break

    print(appel("GET", "/mission")["message"])