"""
Depth-First Search (DFS) Algorithm

DFS is a graph traversal algorithm that explores as far as possible along
each branch before backtracking.
"""

from typing import Dict, List, Set, Any, Optional


def dfs(graph: Dict[Any, List[Any]], start: Any, goal: Any) -> Optional[List[Any]]:
    """
    Perform Depth-First Search on a graph.
    
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
        >>> dfs(graph, 'A', 'F')
        ['A', 'C', 'F']
    """
    if start == goal:
        return [start]
    
    if start not in graph or goal not in graph:
        return None
    
    visited: Set[Any] = set()
    
    def dfs_recursive(node: Any, path: List[Any]) -> Optional[List[Any]]:
        """Helper function for recursive DFS."""
        if node == goal:
            return path
        
        visited.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                result = dfs_recursive(neighbor, path + [neighbor])
                if result is not None:
                    return result
        
        return None
    
    return dfs_recursive(start, [start])


def dfs_iterative(graph: Dict[Any, List[Any]], start: Any, goal: Any) -> Optional[List[Any]]:
    """
    Perform iterative Depth-First Search on a graph using a stack.
    
    Args:
        graph: A dictionary representing the graph
        start: The starting node
        goal: The goal/target node
    
    Returns:
        A list representing the path from start to goal, or None if no path exists
    """
    if start == goal:
        return [start]
    
    if start not in graph or goal not in graph:
        return None
    
    stack = [(start, [start])]
    visited: Set[Any] = {start}
    
    while stack:
        node, path = stack.pop()
        
        for neighbor in graph.get(node, []):
            if neighbor == goal:
                return path + [neighbor]
            
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, path + [neighbor]))
    
    return None


def dfs_traverse(graph: Dict[Any, List[Any]], start: Any) -> List[Any]:
    """
    Traverse a graph using DFS and return all reachable nodes.
    
    Args:
        graph: A dictionary representing the graph
        start: The starting node
    
    Returns:
        A list of all nodes reachable from the start node in DFS order
    """
    if start not in graph:
        return []
    
    visited = []
    visited_set: Set[Any] = set()
    
    def dfs_helper(node: Any):
        """Helper function for DFS traversal."""
        visited_set.add(node)
        visited.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited_set:
                dfs_helper(neighbor)
    
    dfs_helper(start)
    return visited
