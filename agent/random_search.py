# Lucien Random search

import heapq
import math
import random

import agent

agent.API = "http://127.0.0.1:8000"

W_MIN = 1
W_MAX = 5
N = 10


def h(case, cible):
    return math.sqrt((case[0] - cible[0]) ** 2 + (case[1] - cible[1]) ** 2)


def astar_pondere(depart, cible, w):
    couts = {depart: 0}
    file = [(0, depart)]
    explorees = 0
    while file:
        _, case = heapq.heappop(file)
        if case == cible:
            break
        explorees += 1
        for v in agent.get_neighbors(case):
            voisin = tuple(v["node"])
            cout = couts[case] + v["cost"]
            if voisin not in couts or cout < couts[voisin]:
                couts[voisin] = cout
                heapq.heappush(file, (cout + w * h(voisin, cible), voisin))
    return couts[cible], explorees


etat = agent.get_state()
depart = tuple(etat["mission"]["start"])
cible = tuple(etat["mission"]["target"])

meilleur_w = None
meilleur_cout = None
meilleur_explorees = None

for i in range(N):
    w = random.uniform(W_MIN, W_MAX)
    cout, explorees = astar_pondere(depart, cible, w)
    print("w =", round(w, 2), "cout =", cout, "explorees =", explorees)
    if meilleur_w is None or cout < meilleur_cout or (cout == meilleur_cout and explorees < meilleur_explorees):
        meilleur_w = w
        meilleur_cout = cout
        meilleur_explorees = explorees

print("meilleur w :", round(meilleur_w, 2), "cout :", meilleur_cout, "explorees :", meilleur_explorees)
