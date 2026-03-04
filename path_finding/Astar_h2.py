import tracemalloc
from heapq import heappush, heappop

# Module-level stats written after every call — read by the server.
LAST_SEARCH_STATS: dict = {}

# ─────────────────────────────────────────────────────────────────────────────
# A* h₂  —  Deliberately Inadmissible "Weighted + Corridor" Heuristic
# ─────────────────────────────────────────────────────────────────────────────
#
# h(n)  =  W * manhattan(n, goal)  +  OPEN_BONUS * open_neighbours(n)
#
# Why this is inadmissible (and *interestingly* so):
#
#   1. Weight W > 1 guarantees overestimation proportional to distance.
#      The algorithm is now "WA*" (weighted A*): it expands the greedy
#      frontier aggressively and finds paths quickly but not optimally.
#
#   2. The OPEN_BONUS term adds *extra* cost to open junctions.
#      Counter-intuitive: it makes the heuristic *prefer* corridors
#      (narrow, single-option paths) because they get a lower h-value.
#      In practice this causes the search to thread through tight
#      corridors and miss shorter routes that go through open space.
#
# Combined effect on different maze types:
#   • Small mazes (7–15):   usually still finds optimal or near-optimal
#   • Medium mazes (20–50): frequently 10–40 % suboptimal
#   • Large mazes (75):     can be 20–80 % suboptimal; sometimes
#                           finds a wildly different path than h₁
#
# This gives *varied*, interpretable suboptimality that is great for
# academic comparison — not random noise, but a systematic bias.
# ─────────────────────────────────────────────────────────────────────────────

W          = 2.5    # inadmissibility weight  (>1 → overestimate)
OPEN_BONUS = 1.2    # extra cost per open neighbour (biases AWAY from open space)


def astar_h2(maze, start, end, return_trace=False):
    """
    A* with an inadmissible weighted heuristic.

    h(n) = W * manhattan(n, goal)  +  OPEN_BONUS * open_neighbours(n)

    Args:
        maze:         2D list where 0 = passable, 1 = wall
        start:        tuple (row, col)
        end:          tuple (row, col)
        return_trace: if True, return (path, visited_nodes), else path only

    Returns:
        (path, visited_nodes) or path — lists of [row, col] coordinates.
        Peak frontier and memory stats written to LAST_SEARCH_STATS.
    """
    global LAST_SEARCH_STATS

    rows, cols = len(maze), len(maze[0])
    start = tuple(start)
    end   = tuple(end)

    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def manhattan(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def open_neighbours(pos):
        r, c = pos
        return sum(
            1
            for dr, dc in DIRS
            if 0 <= r + dr < rows
            and 0 <= c + dc < cols
            and maze[r + dr][c + dc] == 0
        )

    def h(pos):
        return W * manhattan(pos, end) + OPEN_BONUS * open_neighbours(pos)

    tracemalloc.start()

    open_heap = []
    heappush(open_heap, (h(start), 0, start))

    came_from  = {}
    g_score    = {start: 0}
    closed_set = set()
    visited_order = []
    peak_frontier = 1

    while open_heap:
        peak_frontier = max(peak_frontier, len(open_heap))
        _, current_g, current = heappop(open_heap)

        if current in closed_set:
            continue
        closed_set.add(current)

        if current == end:
            path = [current]
            while path[-1] in came_from:
                path.append(came_from[path[-1]])
            path.reverse()

            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            LAST_SEARCH_STATS = {
                'peak_frontier':     peak_frontier,
                'peak_memory_bytes': peak_mem,
            }
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
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor]   = tentative_g
                f_score             = tentative_g + h(neighbor)
                heappush(open_heap, (f_score, tentative_g, neighbor))
                visited_order.append(neighbor)

    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    LAST_SEARCH_STATS = {
        'peak_frontier':     peak_frontier,
        'peak_memory_bytes': peak_mem,
    }
    visited_list = [[r, c] for r, c in visited_order]
    if return_trace:
        return [], visited_list
    return []