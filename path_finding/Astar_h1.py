from heapq import heappush, heappop


def astar_h1(maze, start, end, return_trace=False):
    """
    A* pathfinding algorithm with Manhattan distance heuristic.

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
    end = tuple(end)

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # Min-heap entries: (f_score, g_score, position)
    open_heap = []
    heappush(open_heap, (manhattan(start, end), 0, start))

    came_from = {}
    g_score = {start: 0}
    closed_set = set()
    visited_order = []

    while open_heap:
        _, current_g, current = heappop(open_heap)

        if current in closed_set:
            continue

        closed_set.add(current)

        # Goal reached: rebuild path by following parent pointers.
        if current == end:
            path = [current]
            while path[-1] in came_from:
                path.append(came_from[path[-1]])
            path.reverse()

            path_list = [[r, c] for r, c in path]
            visited_list = [[r, c] for r, c in visited_order]
            if return_trace:
                return path_list, visited_list
            return path_list

        row, col = current
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nr, nc = row + dr, col + dc
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
                g_score[neighbor] = tentative_g
                f_score = tentative_g + manhattan(neighbor, end)
                heappush(open_heap, (f_score, tentative_g, neighbor))
                visited_order.append(neighbor)

    # No path found
    visited_list = [[r, c] for r, c in visited_order]
    if return_trace:
        return [], visited_list
    return []