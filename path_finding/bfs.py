from collections import deque


def bfs(maze, start, end,  return_trace=False):
    """
    Breadth-First Search pathfinding algorithm.
    
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
    import sys
    sys.stdout.flush()
    print(f"🔍 [BFS] Called with start={start}, end={end}, return_trace={return_trace}", flush=True)
    print(f"🔍 [BFS] Maze dimensions: {len(maze)}x{len(maze[0]) if maze else 0}", flush=True)
    
    try:
        rows, cols = len(maze), len(maze[0])
        visited = set()
        visited_order = []
        queue = deque([(tuple(start), [tuple(start)])])
        visited.add(tuple(start))
        
        print(f"🔍 [BFS] Starting BFS search...", flush=True)
    
        iterations = 0
        while queue:
            pos, path = queue.popleft()
            iterations += 1
            
            if pos == tuple(end):
                # Convert tuples to lists for JSON serialization
                path_list = [[p[0], p[1]] for p in path]
                visited_list = [[v[0], v[1]] for v in visited_order]
                print(f"🔍 [BFS] ✅ Path found! Length: {len(path_list)}, Iterations: {iterations}", flush=True)
                print(f"🔍 [BFS] Path: {path_list[:5]}{'...' if len(path_list) > 5 else ''}", flush=True)
                if return_trace:
                    return path_list, visited_list
                return path_list
            
            row, col = pos
            # Try all 4 directions
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                new_row, new_col = row + dr, col + dc
                new_pos = (new_row, new_col)
                
                # Check bounds and if not visited
                if (0 <= new_row < rows and 
                    0 <= new_col < cols and 
                    new_pos not in visited and 
                    maze[new_row][new_col] == 0):
                    
                    visited.add(new_pos)
                    visited_order.append(new_pos)
                    queue.append((new_pos, path + [new_pos]))
        
        # No path found - return empty lists
        print(f"🔍 [BFS] ❌ No path found after {iterations} iterations", flush=True)
        print(f"🔍 [BFS] Visited {len(visited)} cells", flush=True)
        if return_trace:
            return [], [[v[0], v[1]] for v in visited_order]
        return []
    except Exception as e:
        print(f"❌ [BFS] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise