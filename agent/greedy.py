import requests
import heapq

BASE_URL = "http://localhost:8000"


def get_state():
    response = requests.get(f"{BASE_URL}/state")
    response.raise_for_status()

    return response.json()


def get_neighbors(node):
    r, c = node

    response = requests.get(
        f"{BASE_URL}/nodes/{r}/{c}/neighbors"
    )

    response.raise_for_status()

    return response.json()


def distance(node, target, metric="euclidean"):
    r1, c1 = node
    r2, c2 = target

    response = requests.get(
        f"{BASE_URL}/distance",
        params={
            "r1": r1,
            "c1": c1,
            "r2": r2,
            "c2": c2,
            "metric": metric
        }
    )

    response.raise_for_status()

    data = response.json()

    return data["distance"]


def greedy(start, target):

    frontier = []

    visited = set()

    parent = {
        start: None
    }

    h_start = distance(start, target)
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
                    target
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
    start,
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