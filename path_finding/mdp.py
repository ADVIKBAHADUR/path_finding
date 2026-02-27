"""
MDP (Markov Decision Process) pathfinding solver.
Provides two algorithms that share the same external API as BFS/DFS/A*:

  mdp_value_iteration(maze, start, end, return_trace, ...)
  mdp_policy_iteration(maze, start, end, return_trace, ...)

Both return (path, visited_order) or path depending on return_trace.
They also attach extra planning statistics to the LAST_MDP_STATS dict
so the benchmark harness / server can retrieve them after the call.
"""

import time
import math

# ───────────────────────────────────────────────────────────────────────────
# Constants
# ───────────────────────────────────────────────────────────────────────────

ACTIONS = {
    'UP':    (-1,  0),
    'DOWN':  ( 1,  0),
    'LEFT':  ( 0, -1),
    'RIGHT': ( 0,  1),
}

# Perpendicular slip pairs for each intended direction.
# If the agent intends (dr, dc) it may slip 90° either side.
_PERP = {
    (-1,  0): [( 0, -1), ( 0,  1)],   # UP  → slip LEFT or RIGHT
    ( 1,  0): [( 0, -1), ( 0,  1)],   # DOWN → slip LEFT or RIGHT
    ( 0, -1): [(-1,  0), ( 1,  0)],   # LEFT → slip UP or DOWN
    ( 0,  1): [(-1,  0), ( 1,  0)],   # RIGHT → slip UP or DOWN
}

DEFAULT_GAMMA       = 0.99
DEFAULT_EPSILON     = 1e-4
DEFAULT_MAX_ITER    = 10_000

GOAL_REWARD  =  100.0
STEP_COST    =   -1.0

# Module-level dict written by every top-level solver call.
# Keys: planning_iters, planning_time, extraction_time,
#       cumulative_reward, discounted_return, states_valued, residuals
LAST_MDP_STATS: dict = {}


# ───────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────

def _free_states(maze):
    """Return the set of all passable (row, col) tuples."""
    rows, cols = len(maze), len(maze[0])
    return {(r, c) for r in range(rows) for c in range(cols) if maze[r][c] == 0}


def _step(maze, state, direction):
    """
    Apply a direction to a state.  Returns the resulting state (stays put
    if the move would leave the grid or enter a wall).
    """
    rows, cols = len(maze), len(maze[0])
    r, c = state
    dr, dc = direction
    nr, nc = r + dr, c + dc
    if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0:
        return (nr, nc)
    return state   # bounce back


def _get_transitions(state, action, maze, p_intended, p_sideways):
    """
    Stochastic transition model.

    With probability p_intended the agent moves in direction `action`.
    With probability p_sideways it slips 90° left, and p_sideways right.
    Remaining probability (p_back = 1 - p_intended - 2*p_sideways) it
    moves backward (opposite of intended).

    All wall bumps keep the agent in place.

    Returns list of (probability, next_state) — probabilities sum to 1.
    """
    perp = _PERP[action]
    back = (-action[0], -action[1])
    p_back = max(0.0, 1.0 - p_intended - 2 * p_sideways)

    outcomes = [
        (p_intended,  _step(maze, state, action)),
        (p_sideways,  _step(maze, state, perp[0])),
        (p_sideways,  _step(maze, state, perp[1])),
        (p_back,      _step(maze, state, back)),
    ]

    # Merge duplicate next-states (can happen when several moves bounce to same cell)
    merged = {}
    for prob, ns in outcomes:
        if prob > 0:
            merged[ns] = merged.get(ns, 0.0) + prob
    return [(prob, ns) for ns, prob in merged.items()]


def _reward(next_state, goal):
    """R(s, a, s') — step cost unless we reached the goal."""
    if next_state == goal:
        return GOAL_REWARD
    return STEP_COST


def _extract_path(start, goal, policy, maze):
    """
    Follow the greedy policy from start until goal or until a cycle is detected.

    Returns
    -------
    path         : list of [r, c]   – complete path including start and goal
    visited_order: list of [r, c]   – same as path (every state stepped through)
    cumulative_reward : float
    discounted_return : float  (using gamma from calling scope — passed in)
    """
    max_steps = len(maze) * len(maze[0]) * 2
    path = [list(start)]
    visited_set = {start}
    current = start
    cum_r = 0.0

    for _ in range(max_steps):
        if current == goal:
            break
        action = policy.get(current)
        if action is None:
            break
        nxt = _step(maze, current, action)
        cum_r += _reward(nxt, goal)
        path.append(list(nxt))
        if nxt in visited_set:
            break   # cycle guard
        visited_set.add(nxt)
        current = nxt

    visited_order = path[:]   # for MDP the rollout trace IS the path
    return path, visited_order, cum_r


# ───────────────────────────────────────────────────────────────────────────
# Algorithm 1 — Value Iteration
# ───────────────────────────────────────────────────────────────────────────

def _value_iteration(maze, goal, gamma, epsilon, max_iters, p_intended, p_sideways):
    """
    Core Bellman optimality loop.

    V_{k+1}(s) = max_a  Σ_{s'} T(s,a,s') · [R(s,a,s') + γ · V_k(s')]

    Stops when max|ΔV| < epsilon or max_iters is reached.

    Returns
    -------
    V         : dict {state → float}  – converged value table
    policy    : dict {state → action} – greedy action at each state
    iters     : int
    residuals : list of float         – max delta per iteration
    """
    states = _free_states(maze)
    actions = list(ACTIONS.values())

    V = {s: 0.0 for s in states}
    V[goal] = 0.0   # terminal state has 0 future value (reward is on transition)
    policy = {}
    residuals = []

    for iteration in range(max_iters):
        delta = 0.0
        V_new = {}

        for s in states:
            if s == goal:
                V_new[s] = 0.0
                policy[s] = (0, 0)
                continue

            best_val = -math.inf
            best_act = None
            for a in actions:
                q = sum(
                    prob * (_reward(ns, goal) + gamma * V[ns])
                    for prob, ns in _get_transitions(s, a, maze, p_intended, p_sideways)
                )
                if q > best_val:
                    best_val = q
                    best_act = a

            V_new[s] = best_val
            policy[s] = best_act
            delta = max(delta, abs(V_new[s] - V[s]))

        V = V_new
        residuals.append(delta)

        if delta < epsilon:
            return V, policy, iteration + 1, residuals

    return V, policy, max_iters, residuals


def mdp_value_iteration(maze, start, end, return_trace=False,
                        gamma=DEFAULT_GAMMA, epsilon=DEFAULT_EPSILON,
                        max_iters=DEFAULT_MAX_ITER,
                        p_intended=1.0, p_sideways=0.0):
    """
    Maze solver using MDP Value Iteration.

    Parameters mirror the BFS/DFS/A* API so the benchmark harness can call
    all algorithms uniformly.

    Extra stats are written to LAST_MDP_STATS after each call.
    """
    global LAST_MDP_STATS
    start = tuple(start)
    end   = tuple(end)

    t0 = time.perf_counter()
    V, policy, iters, residuals = _value_iteration(
        maze, end, gamma, epsilon, max_iters, p_intended, p_sideways
    )
    planning_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    path, visited_order, cum_reward = _extract_path(start, end, policy, maze)
    extraction_time = time.perf_counter() - t1

    # Discounted return along extracted path
    disc_return = sum(
        (gamma ** t) * (_reward(tuple(path[t + 1]), end) if t + 1 < len(path) else 0)
        for t in range(len(path) - 1)
    )

    LAST_MDP_STATS = {
        'planning_iters':    iters,
        'planning_time':     planning_time,
        'extraction_time':   extraction_time,
        'cumulative_reward': cum_reward,
        'discounted_return': disc_return,
        'states_valued':     len(V),
        'residuals':         residuals,
    }

    if return_trace:
        return path, visited_order
    return path


# ───────────────────────────────────────────────────────────────────────────
# Algorithm 2 — Policy Iteration
# ───────────────────────────────────────────────────────────────────────────

def _policy_evaluation(policy, V, maze, goal, gamma, eval_epsilon, p_intended, p_sideways):
    """
    Iterative policy evaluation — sweeps until the value function for the
    *fixed* policy converges.

    V^π(s) ≈ Σ_{s'} T(s,π(s),s') · [R(s,π(s),s') + γ · V^π(s')]
    """
    states = _free_states(maze)
    while True:
        delta = 0.0
        for s in states:
            if s == goal:
                continue
            a = policy[s]
            v = sum(
                prob * (_reward(ns, goal) + gamma * V[ns])
                for prob, ns in _get_transitions(s, a, maze, p_intended, p_sideways)
            )
            delta = max(delta, abs(v - V[s]))
            V[s] = v
        if delta < eval_epsilon:
            break
    return V


def _policy_iteration(maze, goal, gamma, epsilon, max_iters, p_intended, p_sideways):
    """
    Policy iteration: alternate policy evaluation and policy improvement
    until the policy is stable.

    Returns
    -------
    V         : dict {state → float}
    policy    : dict {state → action}
    iters     : int  – number of policy improvement sweeps
    residuals : list – value-change per improvement round (for comparison)
    """
    states  = _free_states(maze)
    actions = list(ACTIONS.values())

    # Initialise with a fixed default action (e.g., always try to go RIGHT)
    policy = {s: ACTIONS['RIGHT'] for s in states}
    policy[goal] = (0, 0)
    V = {s: 0.0 for s in states}
    residuals = []

    for iteration in range(max_iters):
        # ── Policy Evaluation ──────────────────────────────────────────────
        V_before = dict(V)
        V = _policy_evaluation(policy, V, maze, goal, gamma, epsilon, p_intended, p_sideways)

        delta = max(abs(V[s] - V_before[s]) for s in states)
        residuals.append(delta)

        # ── Policy Improvement ────────────────────────────────────────────
        policy_stable = True
        for s in states:
            if s == goal:
                continue
            old_action = policy[s]
            best_val = -math.inf
            best_act = old_action
            for a in actions:
                q = sum(
                    prob * (_reward(ns, goal) + gamma * V[ns])
                    for prob, ns in _get_transitions(s, a, maze, p_intended, p_sideways)
                )
                if q > best_val:
                    best_val = q
                    best_act = a
            policy[s] = best_act
            if best_act != old_action:
                policy_stable = False

        if policy_stable:
            return V, policy, iteration + 1, residuals

    return V, policy, max_iters, residuals


def mdp_policy_iteration(maze, start, end, return_trace=False,
                         gamma=DEFAULT_GAMMA, epsilon=DEFAULT_EPSILON,
                         max_iters=DEFAULT_MAX_ITER,
                         p_intended=1.0, p_sideways=0.0):
    """
    Maze solver using MDP Policy Iteration.

    Parameters mirror the BFS/DFS/A* API so the benchmark harness can call
    all algorithms uniformly.

    Extra stats are written to LAST_MDP_STATS after each call.
    """
    global LAST_MDP_STATS
    start = tuple(start)
    end   = tuple(end)

    t0 = time.perf_counter()
    V, policy, iters, residuals = _policy_iteration(
        maze, end, gamma, epsilon, max_iters, p_intended, p_sideways
    )
    planning_time = time.perf_counter() - t0

    t1 = time.perf_counter()
    path, visited_order, cum_reward = _extract_path(start, end, policy, maze)
    extraction_time = time.perf_counter() - t1

    disc_return = sum(
        (gamma ** t) * (_reward(tuple(path[t + 1]), end) if t + 1 < len(path) else 0)
        for t in range(len(path) - 1)
    )

    LAST_MDP_STATS = {
        'planning_iters':    iters,
        'planning_time':     planning_time,
        'extraction_time':   extraction_time,
        'cumulative_reward': cum_reward,
        'discounted_return': disc_return,
        'states_valued':     len(V),
        'residuals':         residuals,
    }

    if return_trace:
        return path, visited_order
    return path
