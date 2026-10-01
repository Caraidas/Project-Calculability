import requests
import heapq

API = "http://localhost:8000"
directions = requests.get(f"{API}/directions").json()["directions"]
state = requests.get(f"{API}/state").json()

start = tuple(state["mission"]["start"])
target = tuple(state["mission"]["target"])
print("Start:", start)
print("Target:", target)


distances = {start: 0}
parents = {start: None}
queue = [(0, start)]

while queue:

    current_cost, current_node = heapq.heappop(queue)
    print("current node:", current_node)
    print("current cost:", current_cost)

    if current_node == target:
        print("Target reached")
        break
    r, c = current_node

    neighbors = requests.get(f"{API}/nodes/{r}/{c}/neighbors").json()

    for neighbor in neighbors:
        next_node = tuple(neighbor["node"])
        move_cost = neighbor["cost"]
        new_cost = current_cost + move_cost
        if next_node not in distances or new_cost < distances[next_node]:

            distances[next_node] = new_cost
            parents[next_node] = current_node

            heapq.heappush(queue, (new_cost, next_node))

path = []
current = target

while current is not None:
    path.append(current)
    current = parents[current]

path.reverse()

print("\nOptimal path:", path)
print("Number of steps:", len(path) - 1)
print("Total cost:", distances[target])

for i in range(len(path) - 1):
    current = path[i]
    next_node = path[i + 1]
    delta = [
        next_node[0] - current[0],
        next_node[1] - current[1]
    ]
    for direction, value in directions.items():
        if value == delta:requests.post(f"{API}/agents/robot/move/{direction}")
    break

