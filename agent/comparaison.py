# Lucien

import contextlib
import io
import time

import agent


def grilles(k):
    ligne = [[r, 5 * k] for r in range(k, 9 * k)]
    u = ([[3 * k, c] for c in range(3 * k, 6 * k + 1)]
         + [[7 * k, c] for c in range(3 * k, 6 * k + 1)]
         + [[r, 6 * k] for r in range(3 * k + 1, 7 * k)])
    return [
        ("aucun", 4, []),
        ("aucun", 8, []),
        ("ligne", 4, ligne),
        ("ligne", 8, ligne),
        ("U", 4, u),
        ("U", 8, u),
    ]


TESTS = [
    ("greedy", "manhattan"),
    ("greedy", "euclidean"),
    ("astar", "manhattan"),
    ("astar", "euclidean"),
    ("dijkstra", None),
]

depart = (5, 0)
cible = (5, 9)
explorees = 0
get_neighbors = agent.get_neighbors


def get_neighbors_compte(case):
    global explorees
    explorees += 1
    return get_neighbors(case)


agent.get_neighbors = get_neighbors_compte


def chercher(algo, metrique):
    if algo == "astar":
        return agent.astar(depart, cible, metrique)
    if algo == "greedy":
        cases = agent.reconstruct_path(agent.greedy(depart, cible, metrique), cible)
    else:
        parents, _ = agent.dijkstra(depart, cible)
        cases = agent.reconstruct_path(parents, cible)
    return [agent.direction(cases[i], cases[i + 1]) for i in range(len(cases) - 1)]


def lancer(taille, connectivite, obstacles, algo, metrique):
    global explorees
    agent.appel("POST", "/init", {
        "size": taille, "connectivity": connectivite, "agents": ["robot"],
        "obstacles": [{"node": n, "weight": 20} for n in obstacles],
        "mission": {"start": list(depart), "target": list(cible), "threshold": 1000},
    })
    explorees = 0
    t = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):
        chemin = chercher(algo, metrique)
    t = (time.perf_counter() - t) * 1000

    for d in chemin:
        agent.appel("POST", f"/agents/robot/move/{d}")
    m = agent.appel("GET", "/mission")
    return m["steps"], m["total_weight"], explorees, t


for k in [1, 3]:
    taille = 10 * k
    depart = (5 * k, 0)
    cible = (5 * k, taille - 1)
    for nom, connectivite, obstacles in grilles(k):
        print(f"\n{taille}x{taille} - {nom} - connectivite {connectivite}")
        print(f"{'algo':<9} {'dist':<10} {'pas':>3} {'cout':>6} {'explorees':>11} {'temps(ms)':>11}")
        for algo, metrique in TESTS:
            pas, cout, nb, t = lancer(taille, connectivite, obstacles, algo, metrique)
            print(f"{algo:<9} {metrique or '-':<10} {pas:>3} {cout:>6g} {nb:>11} {t:>11.0f}")
