"""
A* (A-Star) Algorithm

A* is an informed search algorithm that uses heuristics to find the
shortest path between nodes in a graph. It combines the benefits of
Dijkstra's algorithm and greedy best-first search.
"""

import heapq
from typing import Dict, List, Tuple, Any, Optional, Callable


def astar(
    graph: Dict[Any, List[Tuple[Any, float]]],
    start: Any,
    goal: Any,
    heuristic: Callable[[Any, Any], float]
) -> Optional[Tuple[List[Any], float]]:
    """
    Perform A* search on a weighted graph.
    
    Args:
        graph: A dictionary where keys are nodes and values are lists of
               (neighbor, cost) tuples
        start: The starting node
        goal: The goal/target node
        heuristic: A function that estimates the cost from a node to the goal
    
    Returns:
        A tuple of (path, cost) where path is the list of nodes from start to goal
        and cost is the total path cost, or None if no path exists
    
    Example:
        >>> graph = {
        ...     'A': [('B', 1), ('C', 4)],
        ...     'B': [('A', 1), ('D', 2), ('E', 5)],
        ...     'C': [('A', 4), ('F', 3)],
        ...     'D': [('B', 2)],
        ...     'E': [('B', 5), ('F', 1)],
        ...     'F': [('C', 3), ('E', 1)]
        ... }
        >>> def h(n, goal):
        ...     return 0  # Dijkstra-like behavior
        >>> path, cost = astar(graph, 'A', 'F', h)
        >>> path
        ['A', 'C', 'F']
    """
    if start == goal:
        return ([start], 0.0)
    
    if start not in graph or goal not in graph:
        return None
    
    # Priority queue: (f_score, g_score, node, path)
    open_set = [(heuristic(start, goal), 0.0, start, [start])]
    visited = set()
    
    while open_set:
        f_score, g_score, node, path = heapq.heappop(open_set)
        
        if node == goal:
            return (path, g_score)
        
        if node in visited:
            continue
        
        visited.add(node)
        
        for neighbor, cost in graph.get(node, []):
            if neighbor not in visited:
                new_g_score = g_score + cost
                new_f_score = new_g_score + heuristic(neighbor, goal)
                heapq.heappush(
                    open_set,
                    (new_f_score, new_g_score, neighbor, path + [neighbor])
                )
    
    return None


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    """
    Calculate Manhattan distance between two points.
    
    Args:
        pos1: First position as (x, y) tuple
        pos2: Second position as (x, y) tuple
    
    Returns:
        Manhattan distance between the points
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def euclidean_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        pos1: First position as (x, y) tuple
        pos2: Second position as (x, y) tuple
    
    Returns:
        Euclidean distance between the points
    """
    return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5


def astar_grid(
    grid: List[List[int]],
    start: Tuple[int, int],
    goal: Tuple[int, int],
    heuristic: Callable[[Tuple[int, int], Tuple[int, int]], float] = manhattan_distance
) -> Optional[Tuple[List[Tuple[int, int]], float]]:
    """
    Perform A* search on a 2D grid.
    
    Args:
        grid: 2D list where 0 represents walkable and 1 represents obstacles
        start: Starting position as (row, col) tuple
        goal: Goal position as (row, col) tuple
        heuristic: Heuristic function for distance estimation
    
    Returns:
        A tuple of (path, cost) or None if no path exists
    """
    if not grid or start == goal:
        return ([start], 0.0) if grid else None
    
    rows, cols = len(grid), len(grid[0])
    
    if (start[0] < 0 or start[0] >= rows or start[1] < 0 or start[1] >= cols or
        goal[0] < 0 or goal[0] >= rows or goal[1] < 0 or goal[1] >= cols):
        return None
    
    if grid[start[0]][start[1]] == 1 or grid[goal[0]][goal[1]] == 1:
        return None
    
    open_set = [(heuristic(start, goal), 0.0, start, [start])]
    visited = set()
    
    # 4-directional movement
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    while open_set:
        f_score, g_score, (row, col), path = heapq.heappop(open_set)
        
        if (row, col) == goal:
            return (path, g_score)
        
        if (row, col) in visited:
            continue
        
        visited.add((row, col))
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            if (0 <= new_row < rows and 0 <= new_col < cols and
                grid[new_row][new_col] == 0 and (new_row, new_col) not in visited):
                
                new_g_score = g_score + 1
                new_f_score = new_g_score + heuristic((new_row, new_col), goal)
                heapq.heappush(
                    open_set,
                    (new_f_score, new_g_score, (new_row, new_col), path + [(new_row, new_col)])
                )
    
    return None
