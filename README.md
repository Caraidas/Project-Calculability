# Project-Calculability

## Partie Paul :

Implementation : BFS & DFS 

5 fonctions : 
- appel : permet de faire les appels API.
- voisin : renvoie les directions possible pour une case.
- bfs : réalise l'algorithme bfs, retourne forcément le parcours avec le moins de pas possible sans prendre en compte le cout.
- dfs : réalise l'algorythme dfs, retourne forcément un chemin mais pas forcément le plus court.
- reconstruire : remonte la cible jusqu'au départ puis inverse la liste les directions.

## Lancer le programme

1/ ouvrir un terminale
cd exo-graph\graph-grid\grid_api
docker build -t grid-api-viz --build-arg WITH_VIZ=1 -f Containerfile .
docker run --rm --name grid-api -p 8000:8000 grid-api-viz

2/ dans un second terminal : 

python agent.py bfs
python agent.py dfs