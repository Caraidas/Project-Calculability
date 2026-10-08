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