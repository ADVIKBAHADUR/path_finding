from .bfs import bfs
from .dfs import dfs
from .Astar_h1 import astar_h1
from .Astar_h2 import astar_h2

# Alias for the default A* implementation (Manhattan heuristic)
astar = astar_h1

__all__ = ['bfs', 'dfs', 'astar', 'astar_h1', 'astar_h2']