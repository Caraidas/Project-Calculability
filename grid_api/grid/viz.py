"""Two views of the grid: viz_grid (text, as a grid) and viz_graph (PNG, as a graph)."""


def viz_grid(grid) -> str:
    """Text drawing of the last state. @ mission agent, o other agent, S start, T target,
    a number = obstacle weight, . = free node."""
    obstacles = {v: d["obstacle_value"] for v, d in grid.G.nodes(data=True)
                 if d["obstacle_value"] > 1}
    m = grid.mission
    agent_at: dict = {}
    for a in grid.agents.values():
        sym = "@" if (m is not None and a.name == m.agent) else "o"
        if agent_at.get(a.pose) != "@":
            agent_at[a.pose] = sym
    w = max([3] + [len(str(v)) + 2 for v in obstacles.values()])
    lab = len(str(grid.n - 1))

    def symbol(node) -> str:
        if node in agent_at:
            return agent_at[node]
        if m is not None and node == m.target:
            return "T"
        if m is not None and node == m.start:
            return "S"
        return str(obstacles[node]) if node in obstacles else "."

    lines = [grid.mission_message(), ""]
    lines.append(" " * (lab + 1) + "".join(str(c).center(w) for c in range(grid.n)))
    for r in range(grid.n):
        lines.append(str(r).rjust(lab) + " " + "".join(symbol((r, c)).center(w) for c in range(grid.n)))
    lines += ["", "@ mission agent   o other agent   S start   T target   number = obstacle weight   . free"]
    return "\n".join(lines)


def viz_graph(grid, out) -> None:
    """Draw the grid as a graph into `out` (a path or a binary file object), as a PNG.
    Needs matplotlib (optional dependency)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx

    n = grid.n
    pos = {(r, c): (c, -r) for r, c in grid.G.nodes}
    nodes = list(grid.G.nodes)
    values = [grid.obstacle_value(v) for v in nodes]
    side = max(4, min(14, n * 0.7))
    fig, ax = plt.subplots(figsize=(side, side))
    nx.draw_networkx_edges(grid.G, pos, ax=ax, edge_color="#cccccc", width=0.8)
    nx.draw_networkx_nodes(grid.G, pos, nodelist=nodes, ax=ax, node_color=values, cmap="Reds",
                           vmin=1, vmax=max(values + [2]), edgecolors="#555555",
                           node_size=max(30, 2500 // n))
    if n <= 12:
        nx.draw_networkx_labels(grid.G, pos, ax=ax, font_size=8,
                                labels={v: str(w) for v, w in zip(nodes, values) if w > 1})
    m = grid.mission
    if m is not None:
        ax.scatter(*zip(*[pos[m.target]]), marker="*", s=350, c="green", zorder=5)
        ax.scatter(*zip(*[pos[m.start]]), marker="s", s=140, facecolors="none",
                   edgecolors="blue", linewidths=2, zorder=5)
    for a in grid.agents.values():
        ax.scatter(*zip(*[pos[a.pose]]), marker="o", s=200, c="blue", zorder=6)
    ax.set_title(grid.mission_message(), fontsize=9)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(out, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)