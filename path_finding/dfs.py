import tracemalloc

# Module-level stats written after every call — read by the server.
LAST_SEARCH_STATS: dict = {}


def dfs(maze, start, end, return_trace=False):
    """
    Depth-First Search pathfinding algorithm.

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

    rows, cols = len(maze), len(maze[0])
    start = tuple(start)
    end   = tuple(end)

    tracemalloc.start()

    # Stack stores: (current_position, path_to_current)
    stack = [(start, [start])]
    visited = {start}
    visited_order = []
    peak_frontier = 1  # track max simultaneous stack depth

    while stack:
        peak_frontier = max(peak_frontier, len(stack))
        pos, path = stack.pop()

        if pos == end:
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            LAST_SEARCH_STATS = {
                'peak_frontier':    peak_frontier,
                'peak_memory_bytes': peak_mem,
            }
            path_list    = [[r, c] for r, c in path]
            visited_list = [[r, c] for r, c in visited_order]
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
                stack.append((new_pos, path + [new_pos]))

    # No path found
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    LAST_SEARCH_STATS = {
        'peak_frontier':    peak_frontier,
        'peak_memory_bytes': peak_mem,
    }
    visited_list = [[r, c] for r, c in visited_order]
    if return_trace:
        return [], visited_list
    return []