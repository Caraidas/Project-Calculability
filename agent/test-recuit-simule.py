import heapq
import sys
import time
 
import agent
from recuit_simule import recuit_simule
 
# Fonction objectif : a + b + c = 1
POIDS_COUT = 0.5      # a
POIDS_TEMPS = 0.1     # b
POIDS_MEMOIRE = 0.4   # c
 
# Valeurs de w du balayage
W_DEBUT = 1.0
W_FIN = 5.0
PAS_BALAYAGE = 0.2
 
# Paramètres du recuit 
PAS_RECUIT = 0.2
TEMPERATURE_DEPART = 1.0
REFROIDISSEMENT = 0.95
NB_ITERATIONS = 100
 
 
def astar_pondere(depart, cible, metrique, w):
    parents = {depart: None}
    couts = {depart: 0}
    tas = [(0, depart)]
    taille_max_tas = 1
    while tas:
        _, case = heapq.heappop(tas)
        if case == cible:
            break
        for v in agent.get_neighbors(case):
            voisin = tuple(v["node"])
            cout = couts[case] + v["cost"]
            if voisin not in couts or cout < couts[voisin]:
                couts[voisin] = cout
                parents[voisin] = (case, agent.direction(case, voisin))
                heuristique = agent.distance(voisin, cible, metrique) if w > 0 else 0
                heapq.heappush(tas, (cout + w * heuristique, voisin))
                taille_max_tas = max(taille_max_tas, len(tas))
    chemin = agent.reconstruire(parents, cible)
    return chemin, couts[cible], taille_max_tas
 
 
def mesurer(depart, cible, metrique, w):
    debut = time.perf_counter()
    _, cout_chemin, taille_tas = astar_pondere(depart, cible, metrique, w)
    temps_ms = (time.perf_counter() - debut) * 1000
    return cout_chemin, temps_ms, taille_tas
 
 
def calculer_F(cout_chemin, temps_ms, taille_tas, references):
    """ F = a*C + b*T + c*M"""
    cout_ref, temps_ref, tas_ref = references
    return (POIDS_COUT * cout_chemin / cout_ref
            + POIDS_TEMPS * temps_ms / temps_ref
            + POIDS_MEMOIRE * taille_tas / tas_ref)
 
 
if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    connectivite = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    metrique = "euclidean" if connectivite == 8 else "manhattan"
    depart, cible = (0, 0), (n - 1, n - 1)
 
    agent.appel("POST", "/init", {"size": n, "connectivity": connectivite, "agents": ["robot"],
                                  "mission": {"start": list(depart), "target": list(cible),
                                              "threshold": 1000}})
    print("Grille", n, "x", n, "| connectivité", connectivite, "| distance", metrique, "|", depart, "->", cible)
    print("F =", POIDS_COUT, "·C +", POIDS_TEMPS, "·T +", POIDS_MEMOIRE, "·M (normalisés par A*)")
 
    # Références = A* classique (w = 1)
    references = mesurer(depart, cible, metrique, 1.0)
    print("Références (A*, w = 1) : C =", references[0],
          "| T =", round(references[1], 1), "ms | M =", references[2])
    print()
 
    # ---------- 1. Balayage de w ----------
    print("=== 1. Balayage ===")
    nb_valeurs = round((W_FIN - W_DEBUT) / PAS_BALAYAGE) + 1
    liste_w = [round(W_DEBUT + i * PAS_BALAYAGE, 2) for i in range(nb_valeurs)]
 
    meilleur_w_balayage, meilleur_F_balayage = None, float("inf")
    print("w", "Coût", "Temps (ms)", "Tas max", "F", sep="\t")
    for w in liste_w:
        cout_chemin, temps_ms, taille_tas = mesurer(depart, cible, metrique, w)
        valeur_F = calculer_F(cout_chemin, temps_ms, taille_tas, references)
        print(w, cout_chemin, round(temps_ms, 1), taille_tas, round(valeur_F, 3), sep="\t")
        if valeur_F < meilleur_F_balayage:
            meilleur_w_balayage, meilleur_F_balayage = w, valeur_F
 
    # ---------- 2. Recuit simulé ----------
    print("\n=== 2. Recuit simulé ===")
 
    def F_de_w(w):
        cout_chemin, temps_ms, taille_tas = mesurer(depart, cible, metrique, w)
        return calculer_F(cout_chemin, temps_ms, taille_tas, references)
 
    meilleur_w_recuit, meilleur_F_recuit, historique = recuit_simule(
        F_de_w, w_depart=meilleur_w_balayage, pas=PAS_RECUIT, temperature_depart=TEMPERATURE_DEPART,
        refroidissement=REFROIDISSEMENT, nb_iterations=NB_ITERATIONS)
 
    print("It.", "Temp.", "e", "Choix", "\tw", "F", sep="\t")
    for iteration, temperature, e, choix, w, valeur_F in historique:
        texte_e = "" if e is None else round(e, 2)
        print(iteration, round(temperature, 2), texte_e, choix.ljust(16), w, round(valeur_F, 3), sep="\t")
 
    # ---------- 3. Comparaison ----------
    print("\n=== 3. Comparaison ===")
    print("Balayage      : meilleur w =", meilleur_w_balayage,
          "| F =", round(meilleur_F_balayage, 3), "|", len(liste_w), "lancements d'A*")
    print("Recuit simulé : meilleur w =", meilleur_w_recuit, "| F =", round(meilleur_F_recuit, 3))