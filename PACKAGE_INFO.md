# Path Finding Package - Structure and Usage

## Package Structure

```
path_finding/
├── LICENSE                    # MIT License
├── README.md                  # Comprehensive documentation
├── examples.py                # Example usage of all algorithms
├── pyproject.toml            # Modern Python packaging config
├── setup.py                   # Classic setup file
└── src/
    └── path_finding/
        ├── __init__.py        # Package initialization and exports
        ├── astar.py          # A* algorithm implementation
        ├── bfs.py            # Breadth-First Search
        ├── dfs.py            # Depth-First Search
        └── mdp.py            # Markov Decision Process
```

## Installation

```bash
pip install -e .
```

## Quick Usage

```python
# Import algorithms
from path_finding import bfs, dfs, astar, MDP

# Use BFS
graph = {'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': []}
path = bfs(graph, 'A', 'D')

# Use A*
weighted_graph = {'A': [('B', 1)], 'B': [('C', 2)], 'C': []}
result = astar(weighted_graph, 'A', 'C', lambda n, g: 0)
```

## Algorithms Included

1. **BFS (bfs.py)**: Breadth-First Search for unweighted graphs
2. **DFS (dfs.py)**: Depth-First Search with recursive and iterative versions
3. **A* (astar.py)**: Optimal pathfinding with heuristics, supports graphs and grids
4. **MDP (mdp.py)**: Value iteration and policy iteration for decision-making

## Running Examples

```bash
python3 examples.py
```

This will demonstrate all algorithms with sample inputs and outputs.
