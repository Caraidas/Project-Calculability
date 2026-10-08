# Agent

Le robot cherche un chemin jusqu'à la cible avec BFS, DFS ou A*, puis se déplace
case par case en appelant l'API (il faut que le serveur tourne sur le port 8000).

```
python agent.py bfs
python agent.py dfs
python agent.py astar
```

La mission est remise à zéro à chaque lancement.
