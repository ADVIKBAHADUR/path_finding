"""
MDP (Markov Decision Process) pathfinding solver.

=======================================================================
OVERVIEW
=======================================================================
Unlike BFS / DFS / A*, an MDP does NOT search from start to goal.
Instead it computes a VALUE for every free cell in the maze and derives
a POLICY (best action at every cell).  The path is then extracted by
following the greedy policy from start until the goal is reached.

This lets us:
  - Handle stochastic transitions (e.g. 80% chance you move where you
    intended, 10% you slip sideways each way)
  - Tune risk-aversion vs speed via the discount factor γ
  - Compare planning time vs search-based algorithms in benchmarks

=======================================================================
CORE CONCEPTS YOU NEED TO IMPLEMENT
=======================================================================

1. STATE SPACE  ─────────────────────────────────────────────────────
   Every passable cell (maze[r][c] == 0) is a state.
   Wall cells are NOT states – they are obstacles.
   The goal cell is a TERMINAL state (no further transitions).

   State representation: tuple (row, col)
   Full state space: {(r, c) for r in range(rows)
                              for c in range(cols)
                              if maze[r][c] == 0}

2. ACTIONS  ──────────────────────────────────────────────────────────
   Four cardinal moves: UP, DOWN, LEFT, RIGHT
   Represented as (Δrow, Δcol) offsets, e.g. UP = (-1, 0)

   ACTIONS = {
       'UP':    (-1,  0),
       'DOWN':  ( 1,  0),
       'LEFT':  ( 0, -1),
       'RIGHT': ( 0,  1),
   }

   An action is INVALID at a state if the resulting cell is a wall or
   out of bounds → the agent stays in place (or you can simply exclude
   invalid moves).

3. TRANSITION MODEL  ────────────────────────────────────────────────
   Deterministic version (simple):
     T(s, a, s') = 1.0  if s' is the cell reached by taking a from s
                   0.0  otherwise

   Stochastic version (more interesting / realistic):
     When the agent intends to move in direction a, there is noise:
       - With probability p_intended  → move in direction a
       - With probability p_sideways  → slip 90° left of a  (each)
       - With probability p_back      → slip backward

     Example (classic gridworld):  p_intended=0.8, p_sideways=0.1 each
     These must sum to 1.0.

   Signature you need to implement:
     def get_transitions(state, action, maze):
         \"\"\"
         Returns a list of (probability, next_state) pairs.

         Parameters
         ----------
         state  : tuple (row, col)  – current cell
         action : tuple (dr, dc)    – intended move direction
         maze   : 2D list           – 0=free, 1=wall

         Returns
         -------
         list of (float, tuple)     – [(prob, next_state), ...]
                                      probabilities must sum to 1.0
                                      next_state == state if move hits wall
         \"\"\"
         # TODO

4. REWARD FUNCTION  ─────────────────────────────────────────────────
   R(s, a, s') → scalar reward received after taking action a in state s
   and landing in s'.

   Design choices (you pick the values):
     - GOAL_REWARD   : large positive number, e.g. +100.0
     - STEP_COST     : small negative number, e.g. -1.0
                       (penalises long paths, encourages efficiency)
     - WALL_PENALTY  : negative reward when intended move hits a wall
                       (only relevant if you count hitting a wall as a step)

   Signature you need to implement:
     def reward(state, action, next_state, goal,
                goal_reward=100.0, step_cost=-1.0):
         \"\"\"
         Parameters
         ----------
         state      : tuple (row, col)
         action     : tuple (dr, dc)
         next_state : tuple (row, col)
         goal       : tuple (row, col)

         Returns
         -------
         float – scalar reward
         \"\"\"
         # TODO

5. VALUE ITERATION  ─────────────────────────────────────────────────
   Iteratively refines V(s) (expected discounted return from state s)
   using the Bellman optimality equation:

     V_{k+1}(s) = max_a  Σ_{s'} T(s,a,s') · [R(s,a,s') + γ · V_k(s')]

   Key data structures:
     V        : dict  {state → float}     – value table, init 0.0 everywhere
     policy   : dict  {state → action}    – best action table
     delta    : float                     – max change this iteration
     GAMMA    : float  (0 < γ ≤ 1)        – discount factor
                 γ close to 1 → patient, long-horizon planning
                 γ close to 0 → myopic, prefers immediate rewards
     EPSILON  : float                     – convergence threshold (e.g. 1e-4)

   Convergence: stop when delta < EPSILON (or after MAX_ITERS iterations)

   Signature you need to implement:
     def value_iteration(maze, goal,
                         gamma=0.99,
                         epsilon=1e-4,
                         max_iters=10_000,
                         p_intended=1.0,
                         p_sideways=0.0):
         \"\"\"
         Parameters
         ----------
         maze        : 2D list of int     – 0=free, 1=wall
         goal        : tuple (row, col)   – terminal/target state
         gamma       : float              – discount factor
         epsilon     : float              – convergence delta threshold
         max_iters   : int                – hard iteration cap
         p_intended  : float              – prob of moving intended direction
         p_sideways  : float              – prob of slipping sideways (each side)
                                           p_back = 1 - p_intended - 2*p_sideways

         Returns
         -------
         V           : dict {state → float}   – converged value table
         policy      : dict {state → action}  – greedy policy (dr, dc)
         iters       : int                    – iterations until convergence
         residuals   : list of float          – delta per iteration (for plotting)
         \"\"\"
         # TODO

6. POLICY EXTRACTION  ───────────────────────────────────────────────
   After value iteration converges, extract the path from start → goal
   by following policy[state] greedily.

   Edge cases to handle:
     - The policy leads into a cycle (shouldn't happen if γ < 1,
       but detect with a visited-set anyway)
     - The start state has no value (unreachable from goal side)

   Signature you need to implement:
     def extract_path(start, goal, policy, maze, max_steps=None):
         \"\"\"
         Parameters
         ----------
         start    : tuple (row, col)
         goal     : tuple (row, col)
         policy   : dict {state → action}  – output of value_iteration
         maze     : 2D list
         max_steps: int | None  – safety cap (default: rows*cols)

         Returns
         -------
         path         : list of [row, col]   – same format as BFS/DFS/A*
         visited_order: list of [row, col]   – every state touched during
                                               policy rollout (for animation)
         \"\"\"
         # TODO

7. TOP-LEVEL SOLVER (benchmark entry point)  ─────────────────────────
   This is what server.py / benchmark_browser.py will call.
   Mirror the interface of bfs / dfs / astar_h1 exactly.

   def mdp_solver(maze, start, end, return_trace=False,
                  gamma=0.99, epsilon=1e-4,
                  p_intended=1.0, p_sideways=0.0):
       \"\"\"
       Parameters
       ----------
       maze         : 2D list                – 0=free, 1=wall
       start        : tuple/list (row, col)
       end          : tuple/list (row, col)
       return_trace : bool
       gamma        : float
       epsilon      : float
       p_intended   : float
       p_sideways   : float

       Returns
       -------
       If return_trace is True:
           (path, visited_order)
           path         : list of [row, col]  – solution path
           visited_order: list of [row, col]  – policy rollout trace
       If return_trace is False:
           path only
       \"\"\"
       # TODO: call value_iteration → extract_path → return

=======================================================================
BENCHMARK-SPECIFIC METRICS (unique to MDP; add to compute_metrics later)
=======================================================================

These are things you can cheaply capture inside value_iteration and
return to the benchmark harness:

  planning_iters   : int    – number of Bellman sweeps until convergence
  residuals        : list   – delta per iteration (plot convergence curve)
  planning_time    : float  – wall-clock time for value_iteration alone
  extraction_time  : float  – wall-clock time for extract_path alone
  total_time       : float  – planning_time + extraction_time
  cumulative_reward: float  – sum of R(s,a,s') along extracted path
  discounted_return: float  – Σ γ^t · R_t along extracted path
  states_valued    : int    – len(V)  (cells that received a finite value)
  policy_path_len  : int    – len(path)

=======================================================================
INTEGRATION CHECKLIST (things to wire up once implemented)
=======================================================================

[ ] Add mdp_solver import to path_finding/__init__.py
[ ] Add 'mdp' route to backend/server.py  (/solve endpoint)
[ ] Add <option value="10"> to index.html dropdown
[ ] Add python_mdp() and value "10" case to maze_solvers.js
[ ] Add {'name': 'MDP', 'value': '10'} to algorithms list in benchmark_browser.py
[ ] Extend compute_metrics() in benchmark_browser.py with MDP-specific columns
[ ] Add MDP columns to CSV_COLUMNS header in benchmark_browser.py

=======================================================================
SUGGESTED FILE LAYOUT WHEN COMPLETE
=======================================================================

mdp.py
├── ACTIONS          (module-level constant dict)
├── get_transitions  (stochastic/deterministic transition model)
├── reward           (reward function)
├── value_iteration  (core Bellman loop → V, policy, iters, residuals)
├── extract_path     (greedy rollout → path, visited_order)
└── mdp_solver       (top-level entry point matching BFS/DFS/A* API)
"""


# -----------------------------------------------------------------------
# Constants – define these first, then implement the functions above
# -----------------------------------------------------------------------

ACTIONS = {
    'UP':    (-1,  0),
    'DOWN':  ( 1,  0),
    'LEFT':  ( 0, -1),
    'RIGHT': ( 0,  1),
}

# Default hyperparameters
DEFAULT_GAMMA    = 0.99
DEFAULT_EPSILON  = 1e-4
DEFAULT_MAX_ITER = 10_000

# Reward constants – tweak these to change path behaviour
GOAL_REWARD  =  100.0
STEP_COST    =   -1.0
WALL_PENALTY =   -1.0   # optional; only applies if you penalise wall bumps


# -----------------------------------------------------------------------
# TODO: implement get_transitions(state, action, maze)
# TODO: implement reward(state, action, next_state, goal, ...)
# TODO: implement value_iteration(maze, goal, gamma, epsilon, ...)
# TODO: implement extract_path(start, goal, policy, maze, ...)
# TODO: implement mdp_solver(maze, start, end, return_trace, ...)
# -----------------------------------------------------------------------
