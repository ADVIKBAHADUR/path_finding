def dfs(maze, start, end, return_trace=False):
    """
    Depth-First Search pathfinding algorithm.

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

    # Stack stores: (current_position, path_to_current)
    stack = [(start, [start])]
    visited = {start}
    visited_order = []

    while stack:
        pos, path = stack.pop()

        # Goal reached
        if pos == end:
            path_list = [[r, c] for r, c in path]
            visited_list = [[r, c] for r, c in visited_order]
            if return_trace:
                return path_list, visited_list
            return path_list

        row, col = pos

        # Explore in 4 directions
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_row, new_col = row + dr, col + dc
            new_pos = (new_row, new_col)

            if (
                0 <= new_row < rows
                and 0 <= new_col < cols
                and new_pos not in visited
                and maze[new_row][new_col] == 0
            ):
                visited.add(new_pos)
                visited_order.append(new_pos)
                stack.append((new_pos, path + [new_pos]))

    # No path found
    visited_list = [[r, c] for r, c in visited_order]
    if return_trace:
        return [], visited_list
    return []