# Path Finding Algorithms - Template Package

A Python package template for implementing various path-finding and decision-making algorithms including BFS, DFS, A*, and MDP.

## Overview

This package provides a structured template for implementing fundamental pathfinding and graph traversal algorithms. The structure is ready for you to add your own algorithm implementations.

## Features

Template stubs provided for:
- **Breadth-First Search (BFS)**: Explore graphs layer by layer
- **Depth-First Search (DFS)**: Explore graphs by going as deep as possible
- **A* (A-Star)**: Optimal pathfinding using heuristics
- **Markov Decision Process (MDP)**: Decision-making in stochastic environments

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/ADVIKBAHADUR/path_finding.git
cd path_finding

# Install the package in editable mode
pip install -e .
```

## Package Structure

```
path_finding/
├── src/
│   └── path_finding/
│       ├── __init__.py          # Package exports
│       ├── bfs.py               # BFS algorithm template
│       ├── dfs.py               # DFS algorithm template
│       ├── astar.py             # A* algorithm template
│       └── mdp.py               # MDP algorithm template
├── setup.py                      # Package setup
├── pyproject.toml               # Modern Python packaging
└── README.md                    # This file
```

## Implementation Guide

Each algorithm file contains:
- Function signatures with type hints
- Comprehensive docstrings
- TODO comments marking where to implement logic

### Example: Implementing BFS

Edit `src/path_finding/bfs.py`:

```python
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
    """
    # TODO: Implement BFS algorithm
    # Add your implementation here
    from collections import deque
    
    if start == goal:
        return [start]
    
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        node, path = queue.popleft()
        for neighbor in graph.get(node, []):
            if neighbor == goal:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None
```

## Usage

After implementing the algorithms, you can use them as follows:

```python
from path_finding import bfs, dfs, astar, MDP

# Example graph
graph = {
    'A': ['B', 'C'],
    'B': ['D'],
    'C': ['D'],
    'D': []
}

# Use your implemented algorithms
path = bfs(graph, 'A', 'D')
```

## Algorithms to Implement

### BFS (src/path_finding/bfs.py)
- `bfs(graph, start, goal)`: Find shortest path
- `bfs_traverse(graph, start)`: Traverse all reachable nodes

### DFS (src/path_finding/dfs.py)
- `dfs(graph, start, goal)`: Find path using DFS (recursive)
- `dfs_iterative(graph, start, goal)`: Find path using DFS (iterative)
- `dfs_traverse(graph, start)`: Traverse all reachable nodes

### A* (src/path_finding/astar.py)
- `astar(graph, start, goal, heuristic)`: Find optimal path in weighted graph
- `astar_grid(grid, start, goal, heuristic)`: Find path in 2D grid
- `manhattan_distance(pos1, pos2)`: Manhattan distance heuristic
- `euclidean_distance(pos1, pos2)`: Euclidean distance heuristic

### MDP (src/path_finding/mdp.py)
- `MDP` class with methods:
  - `value_iteration(epsilon, max_iterations)`: Solve using value iteration
  - `policy_iteration(max_iterations)`: Solve using policy iteration
  - `extract_policy(V)`: Extract policy from value function
- `solve_mdp_value_iteration(...)`: Convenience function for value iteration
- `solve_mdp_policy_iteration(...)`: Convenience function for policy iteration

## Testing Your Implementation

Create test files to verify your implementations:

```python
# test_bfs.py
from path_finding import bfs

def test_bfs_simple_path():
    graph = {'A': ['B'], 'B': ['C'], 'C': []}
    assert bfs(graph, 'A', 'C') == ['A', 'B', 'C']

def test_bfs_no_path():
    graph = {'A': ['B'], 'B': [], 'C': []}
    assert bfs(graph, 'A', 'C') is None
```

## Contributing

Feel free to add tests, documentation, or improve the template structure.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- ADVIKBAHADUR

## Notes

- This is a template package with stub implementations
- All functions are marked with `# TODO:` comments
- Implement the algorithms yourself to learn the concepts
- The package structure allows for easy testing and distribution once implemented
