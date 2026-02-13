# Path Finding Algorithms

A Python package implementing various path-finding and decision-making algorithms including BFS, DFS, A*, and MDP.

## Overview

This package provides implementations of fundamental pathfinding and graph traversal algorithms, designed for educational purposes and practical applications in robotics, game development, and AI research.

## Features

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

# Install the package
pip install -e .
```

### Using pip (after publishing to PyPI)

```bash
pip install path_finding
```

## Quick Start

### BFS Example

```python
from path_finding import bfs

# Define a graph
graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E']
}

# Find path from A to F
path = bfs(graph, 'A', 'F')
print(f"Path: {path}")  # Output: Path: ['A', 'C', 'F']
```

### DFS Example

```python
from path_finding import dfs

# Find path using DFS
path = dfs(graph, 'A', 'F')
print(f"Path: {path}")
```

### A* Example

```python
from path_finding import astar

# Define a weighted graph
graph = {
    'A': [('B', 1), ('C', 4)],
    'B': [('A', 1), ('D', 2), ('E', 5)],
    'C': [('A', 4), ('F', 3)],
    'D': [('B', 2)],
    'E': [('B', 5), ('F', 1)],
    'F': [('C', 3), ('E', 1)]
}

# Define heuristic function
def heuristic(node, goal):
    return 0  # Simplified for this example

# Find optimal path
result = astar(graph, 'A', 'F', heuristic)
if result:
    path, cost = result
    print(f"Path: {path}, Cost: {cost}")
```

### A* Grid Example

```python
from path_finding import astar_grid

# Define a grid (0 = walkable, 1 = obstacle)
grid = [
    [0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 1, 1, 0],
    [0, 0, 0, 0, 0]
]

# Find path from (0,0) to (4,4)
result = astar_grid(grid, (0, 0), (4, 4))
if result:
    path, cost = result
    print(f"Path: {path}")
    print(f"Cost: {cost}")
```

### MDP Example

```python
from path_finding import MDP

# Define states and actions
states = ['s1', 's2', 's3']
actions = ['a1', 'a2']

# Define transition probabilities
def transition_prob(state, action, next_state):
    # Define your transition probabilities here
    if state == 's1' and action == 'a1' and next_state == 's2':
        return 0.8
    # ... more transitions
    return 0.0

# Define rewards
def reward(state, action, next_state):
    if next_state == 's3':
        return 10.0
    return -1.0

# Create and solve MDP
mdp = MDP(states, actions, transition_prob, reward, gamma=0.9)
values = mdp.value_iteration()
policy = mdp.extract_policy(values)

print(f"Optimal values: {values}")
print(f"Optimal policy: {policy}")
```

## Algorithms

### BFS (Breadth-First Search)
- **Time Complexity**: O(V + E)
- **Space Complexity**: O(V)
- **Use Case**: Unweighted graphs, shortest path in terms of edges

### DFS (Depth-First Search)
- **Time Complexity**: O(V + E)
- **Space Complexity**: O(V)
- **Use Case**: Graph traversal, cycle detection, topological sorting

### A* (A-Star)
- **Time Complexity**: O(E) in worst case
- **Space Complexity**: O(V)
- **Use Case**: Weighted graphs, optimal pathfinding with heuristics

### MDP (Markov Decision Process)
- **Algorithms**: Value Iteration, Policy Iteration
- **Use Case**: Decision-making under uncertainty, reinforcement learning

## API Reference

### BFS
- `bfs(graph, start, goal)`: Find shortest path
- `bfs_traverse(graph, start)`: Traverse all reachable nodes

### DFS
- `dfs(graph, start, goal)`: Find path using DFS (recursive)
- `dfs_iterative(graph, start, goal)`: Find path using DFS (iterative)
- `dfs_traverse(graph, start)`: Traverse all reachable nodes

### A*
- `astar(graph, start, goal, heuristic)`: Find optimal path in weighted graph
- `astar_grid(grid, start, goal, heuristic)`: Find path in 2D grid
- `manhattan_distance(pos1, pos2)`: Manhattan distance heuristic
- `euclidean_distance(pos1, pos2)`: Euclidean distance heuristic

### MDP
- `MDP(states, actions, transition_prob, reward, gamma)`: Create MDP instance
- `value_iteration(epsilon, max_iterations)`: Solve using value iteration
- `policy_iteration(max_iterations)`: Solve using policy iteration
- `solve_mdp_value_iteration(...)`: Convenience function for value iteration
- `solve_mdp_policy_iteration(...)`: Convenience function for policy iteration

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- ADVIKBAHADUR

## Acknowledgments

This package implements classical algorithms from computer science and artificial intelligence literature.
