"""
Path Finding Algorithms Package

This package provides a template for implementing various path-finding and 
decision-making algorithms:
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- A* (A-Star)
- MDP (Markov Decision Process)

Note: This is a template package. Algorithm implementations are stubs that 
need to be completed.

Usage:
    from path_finding import bfs, dfs, astar
    from path_finding.mdp import MDP
"""

__version__ = "0.1.0"

# Import BFS functions
from .bfs import bfs, bfs_traverse

# Import DFS functions
from .dfs import dfs, dfs_iterative, dfs_traverse

# Import A* functions
from .astar import (
    astar,
    astar_grid,
    manhattan_distance,
    euclidean_distance,
)

# Import MDP classes and functions
from .mdp import (
    MDP,
    solve_mdp_value_iteration,
    solve_mdp_policy_iteration,
)

__all__ = [
    # BFS
    "bfs",
    "bfs_traverse",
    # DFS
    "dfs",
    "dfs_iterative",
    "dfs_traverse",
    # A*
    "astar",
    "astar_grid",
    "manhattan_distance",
    "euclidean_distance",
    # MDP
    "MDP",
    "solve_mdp_value_iteration",
    "solve_mdp_policy_iteration",
]
