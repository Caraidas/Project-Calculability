from agent import appel


def creer_test(taille=12, connectivite=4, forme="vide", epaisseur=1):
    obstacles = []

    if forme == "u":
        gauche = taille // 4
        droite = taille - gauche - 1
        haut = taille // 4
        bas = taille - 3
        for r in range(haut, bas + 1):
            obstacles.append({"node": [r, gauche], "weight": 50})
            obstacles.append({"node": [r, droite], "weight": 50})
        for c in range(gauche + 1, droite):
            obstacles.append({"node": [bas, c], "weight": 50})
        depart = [taille // 2, taille // 2]
        cible = [taille - 1, taille // 2]

    elif forme == "ligne":
        milieu = taille // 2
        if epaisseur < 1 or milieu + epaisseur >= taille - 2:
            raise ValueError("Epaisseur trop grande pour cette grille")
        for r in range(1, taille - 1):
            for c in range(milieu, milieu + epaisseur):
                obstacles.append({"node": [r, c], "weight": 50})
        depart = [taille // 2, 1]
        cible = [taille // 2, taille - 2]

    elif forme == "vide":
        depart = [0, 0]
        cible = [taille - 1, taille - 1]
    else:
        raise ValueError("Forme inconnue")

    config = {
        "size": taille,
        "connectivity": connectivite,
        "agents": ["robot"],
        "obstacles": obstacles,
        "mission": {
            "start": depart,
            "target": cible,
            "threshold": 100000,
            "agent": "robot"
        }
    }
    appel("POST", "/init", config)
    return config


if __name__ == "__main__":
    creer_test(12, 4, "u")
    print("Grille en U initialisee")