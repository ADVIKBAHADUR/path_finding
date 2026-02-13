"""
Breadth-First Search (BFS) Algorithm

BFS is a graph traversal algorithm that explores vertices in layers,
visiting all neighbors at the present depth before moving to vertices
at the next depth level.
"""

from collections import deque
from typing import Dict, List, Set, Any, Optional


def bfs(graph: Dict[Any, List[Any]], start: Any, goal: Any) -> Optional[List[Any]]:
    """
    Perform Breadth-First Search on a graph.
    
    Args:
        graph: A dictionary representing the graph where keys are nodes
               and values are lists of neighboring nodes
        start: The starting node
        goal: The goal/target node
    
    Returns:
        A list representing the path from start to goal, or None if no path exists
    
    Example:
        >>> graph = {
        ...     'A': ['B', 'C'],
        ...     'B': ['A', 'D', 'E'],
        ...     'C': ['A', 'F'],
        ...     'D': ['B'],
        ...     'E': ['B', 'F'],
        ...     'F': ['C', 'E']
        ... }
        >>> bfs(graph, 'A', 'F')
        ['A', 'C', 'F']
    """
    if start == goal:
        return [start]
    
    if start not in graph or goal not in graph:
        return None
    
    queue = deque([(start, [start])])
    visited: Set[Any] = {start}
    
    while queue:
        node, path = queue.popleft()
        
        for neighbor in graph.get(node, []):
            if neighbor == goal:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None


def bfs_traverse(graph: Dict[Any, List[Any]], start: Any) -> List[Any]:
    """
    Traverse a graph using BFS and return all reachable nodes.
    
    Args:
        graph: A dictionary representing the graph
        start: The starting node
    
    Returns:
        A list of all nodes reachable from the start node in BFS order
    """
    if start not in graph:
        return []
    
    visited = []
    queue = deque([start])
    visited_set: Set[Any] = {start}
    
    while queue:
        node = queue.popleft()
        visited.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited_set:
                visited_set.add(neighbor)
                queue.append(neighbor)
    
    return visited
