from heapq import heappush, heappop


# Penalty added per blocked cardinal neighbour.
# A dead-end (1 open neighbour) adds 3 × CORRIDOR_PENALTY to h.
# Keep it < 1 to limit overestimation; the heuristic is intentionally
# inadmissible – that's the point of this variant for benchmarking.
CORRIDOR_PENALTY = 0.5


def astar_h2(maze, start, end, return_trace=False):
    """
    A* pathfinding algorithm with a corridor-aware heuristic.

    h(n) = manhattan(n, end) + CORRIDOR_PENALTY * (4 - open_neighbours(n))

    Nodes inside dead-ends or tight corridors receive a higher estimate,
    so the search biases toward open space.  The heuristic is deliberately
    *inadmissible* (it can overestimate), which means the found path may
    be suboptimal – making it an interesting contrast to h1 in benchmarks.

    Args:
        maze: 2D list where 0 = empty, 1 = wall
        start: tuple (row, col)
        end: tuple (row, col)
        return_trace: if True, return (path, visited_nodes), else just path

    Returns:
        If return_trace is True: tuple of (path, visited_nodes)
        If return_trace is False: path only
        where path is a list of [row, col] coordinates
    """
    rows, cols = len(maze), len(maze[0])
    start = tuple(start)
    end   = tuple(end)

    DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def open_neighbour_count(pos):
        """How many of the 4 cardinal neighbours are passable."""
        r, c = pos
        count = 0
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0:
                count += 1
        return count

    def h(pos):
        """Corridor-aware heuristic: manhattan + penalty for tight spaces."""
        return manhattan(pos, end) + CORRIDOR_PENALTY * (4 - open_neighbour_count(pos))

    # Min-heap entries: (f_score, g_score, position)
    open_heap = []
    heappush(open_heap, (h(start), 0, start))

    came_from  = {}
    g_score    = {start: 0}
    closed_set = set()
    visited_order = []

    while open_heap:
        _, current_g, current = heappop(open_heap)

        if current in closed_set:
            continue

        closed_set.add(current)

        # Goal reached: reconstruct path via parent pointers
        if current == end:
            path = [current]
            while path[-1] in came_from:
                path.append(came_from[path[-1]])
            path.reverse()

            path_list    = [[r, c] for r, c in path]
            visited_list = [[r, c] for r, c in visited_order]
            if return_trace:
                return path_list, visited_list
            return path_list

        row, col = current
        for dr, dc in DIRS:
            nr, nc   = row + dr, col + dc
            neighbor = (nr, nc)

            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if maze[nr][nc] != 0:
                continue
            if neighbor in closed_set:
                continue

            tentative_g = current_g + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor]   = tentative_g
                f_score             = tentative_g + h(neighbor)
                heappush(open_heap, (f_score, tentative_g, neighbor))
                visited_order.append(neighbor)

    # No path found
    visited_list = [[r, c] for r, c in visited_order]
    if return_trace:
        return [], visited_list
    return []