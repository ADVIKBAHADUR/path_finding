"""
Example usage of the path_finding package.

This script demonstrates how to use the different algorithms
included in the package.
"""

from path_finding import bfs, dfs, astar, astar_grid, MDP


def example_bfs():
    """Demonstrate Breadth-First Search."""
    print("=" * 50)
    print("BFS Example")
    print("=" * 50)
    
    graph = {
        'A': ['B', 'C'],
        'B': ['A', 'D', 'E'],
        'C': ['A', 'F'],
        'D': ['B'],
        'E': ['B', 'F'],
        'F': ['C', 'E']
    }
    
    path = bfs(graph, 'A', 'F')
    print(f"Graph: {graph}")
    print(f"Path from A to F: {path}")
    print()


def example_dfs():
    """Demonstrate Depth-First Search."""
    print("=" * 50)
    print("DFS Example")
    print("=" * 50)
    
    graph = {
        'A': ['B', 'C'],
        'B': ['A', 'D', 'E'],
        'C': ['A', 'F'],
        'D': ['B'],
        'E': ['B', 'F'],
        'F': ['C', 'E']
    }
    
    path = dfs(graph, 'A', 'F')
    print(f"Graph: {graph}")
    print(f"Path from A to F: {path}")
    print()


def example_astar():
    """Demonstrate A* algorithm."""
    print("=" * 50)
    print("A* Example")
    print("=" * 50)
    
    # Weighted graph
    graph = {
        'A': [('B', 1), ('C', 4)],
        'B': [('A', 1), ('D', 2), ('E', 5)],
        'C': [('A', 4), ('F', 3)],
        'D': [('B', 2)],
        'E': [('B', 5), ('F', 1)],
        'F': [('C', 3), ('E', 1)]
    }
    
    def heuristic(node, goal):
        # Simple heuristic (could be improved based on actual distances)
        return 0
    
    result = astar(graph, 'A', 'F', heuristic)
    if result:
        path, cost = result
        print(f"Weighted graph: {graph}")
        print(f"Path from A to F: {path}")
        print(f"Total cost: {cost}")
    print()


def example_astar_grid():
    """Demonstrate A* on a 2D grid."""
    print("=" * 50)
    print("A* Grid Example")
    print("=" * 50)
    
    # Grid where 0 = walkable, 1 = obstacle
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 1, 1, 0],
        [0, 0, 0, 0, 0]
    ]
    
    print("Grid (0 = walkable, 1 = obstacle):")
    for row in grid:
        print(row)
    
    result = astar_grid(grid, (0, 0), (4, 4))
    if result:
        path, cost = result
        print(f"\nPath from (0,0) to (4,4): {path}")
        print(f"Total cost: {cost}")
    print()


def example_mdp():
    """Demonstrate MDP value iteration."""
    print("=" * 50)
    print("MDP Example")
    print("=" * 50)
    
    # Simple MDP: two states, one action
    states = ['s1', 's2', 's3']
    actions = ['a1', 'a2']
    
    def transition_prob(state, action, next_state):
        """Define transition probabilities."""
        transitions = {
            ('s1', 'a1', 's2'): 0.8,
            ('s1', 'a1', 's1'): 0.2,
            ('s1', 'a2', 's3'): 0.6,
            ('s1', 'a2', 's1'): 0.4,
            ('s2', 'a1', 's3'): 1.0,
            ('s2', 'a2', 's2'): 1.0,
            ('s3', 'a1', 's3'): 1.0,
            ('s3', 'a2', 's3'): 1.0,
        }
        return transitions.get((state, action, next_state), 0.0)
    
    def reward(state, action, next_state):
        """Define rewards."""
        if next_state == 's3':
            return 10.0
        return -1.0
    
    mdp = MDP(states, actions, transition_prob, reward, gamma=0.9)
    values = mdp.value_iteration()
    policy = mdp.extract_policy(values)
    
    print(f"States: {states}")
    print(f"Actions: {actions}")
    print(f"\nOptimal values: {values}")
    print(f"Optimal policy: {policy}")
    print()


if __name__ == "__main__":
    example_bfs()
    example_dfs()
    example_astar()
    example_astar_grid()
    example_mdp()
    
    print("=" * 50)
    print("All examples completed successfully!")
    print("=" * 50)
