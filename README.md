# Project-Calculability

## Comment executer : 

cd exo-graph\graph-grid\grid_api
docker build -t grid-api-viz --build-arg WITH_VIZ=1 -f Containerfile .
docker run --rm --name grid-api -p 8000:8000 grid-api-viz

# DFS & BFS

python agent.py bfs
python agent.py dfs
python agent.py astar
python agent.py greedy
python agent.py dijkstra

# Utilisation de la config de test

appeler la fonction creer_test depuis config_tests.py
Le premier paramètre correspond à la taille de la grid, le deuxième à la connectivité, le troisième à la forme et le quatrième à l'épaisseur qui est 1.
les formes: mettre "u" pour un obstacle en u, "ligne" pour l'obstacle en forme de ligne et ne pas mettre de paramètre dans le cas de vide.