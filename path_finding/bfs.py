import tracemalloc
from collections import deque

# Module-level stats written after every call — read by the server.
LAST_SEARCH_STATS: dict = {}


def bfs(maze, start, end, return_trace=False):
    """
    Breadth-First Search pathfinding algorithm.

    Args:
        maze: 2D list where 0 = empty, 1 = wall
        start: tuple (row, col)
        end: tuple (row, col)
        return_trace: if True, return (path, visited_nodes), else just path

    Returns:
        (path, visited_nodes) or path — lists of [row, col] coordinates.
        Peak frontier and memory stats are written to LAST_SEARCH_STATS.
    """
    global LAST_SEARCH_STATS
    import sys

    rows, cols = len(maze), len(maze[0])

    tracemalloc.start()

    visited = {tuple(start)}
    visited_order = []
    queue = deque([(tuple(start), [tuple(start)])])
    peak_frontier = 1

    while queue:
        peak_frontier = max(peak_frontier, len(queue))
        pos, path = queue.popleft()

        if pos == tuple(end):
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            LAST_SEARCH_STATS = {
                'peak_frontier':     peak_frontier,
                'peak_memory_bytes': peak_mem,
            }
            path_list    = [[p[0], p[1]] for p in path]
            visited_list = [[v[0], v[1]] for v in visited_order]
            if return_trace:
                return path_list, visited_list
            return path_list

        row, col = pos
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_row, new_col = row + dr, col + dc
            new_pos = (new_row, new_col)
            if (0 <= new_row < rows
                    and 0 <= new_col < cols
                    and new_pos not in visited
                    and maze[new_row][new_col] == 0):
                visited.add(new_pos)
                visited_order.append(new_pos)
                queue.append((new_pos, path + [new_pos]))

    # No path found
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    LAST_SEARCH_STATS = {
        'peak_frontier':     peak_frontier,
        'peak_memory_bytes': peak_mem,
    }
    if return_trace:
        return [], [[v[0], v[1]] for v in visited_order]
    return []