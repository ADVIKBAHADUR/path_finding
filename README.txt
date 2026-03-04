================================================================================
                     PATHFINDING ALGORITHM BENCHMARK
================================================================================

Comparative study of six pathfinding algorithms on procedurally generated mazes:
DFS, BFS, A* (Manhattan), A* (Corridor-Aware), MDP Value Iteration, and MDP
Policy Iteration.


QUICK START
-----------

1. Install the package:

     pip install -e .

2. Start both servers (frontend + backend) in one command:

     python3 submodules/Maze_solver_py/start_servers.py

3. Open http://localhost:8000 in a browser.
   Select an algorithm from the dropdown and click Play.


Running the benchmark:

     python benchmark_browser.py
     # Results written to benchmark_results.csv / benchmark_results_g.csv


Generating outputs:

     python visualize_results.py           # Plots (16 figures -> plots/)
     python generate_metric_tables.py      # LaTeX tables (-> tables/)


PROJECT STRUCTURE
-----------------

path_finding/
|-- path_finding/                  Algorithm implementations (installable package)
|   |-- bfs.py                    Breadth-First Search
|   |-- dfs.py                    Depth-First Search
|   |-- Astar_h1.py               A* with Manhattan distance heuristic
|   |-- Astar_h2.py               A* with Euclidean corridor-aware heuristic
|   +-- mdp.py                    MDP Value Iteration & Policy Iteration
|
|-- submodules/
|   +-- Maze_solver_py/            Web-based maze generator & visualiser (git submodule)
|       |-- index.html             Frontend UI
|       +-- backend/server.py      Flask API bridging frontend to path_finding package
|
|-- benchmark_browser.py           Selenium-driven benchmark harness
|-- benchmark_results_g.csv        Raw benchmark data (94 runs x 6 algorithms)
|-- visualize_results.py           Generates all analysis plots
|-- generate_metric_tables.py      Generates LaTeX metric tables
|
|-- plots/                         Generated figures (16 PNGs)
|-- tables/                        Generated LaTeX tables (15 .tex files)
|
+-- pyproject.toml                 Package metadata & dependencies


ALGORITHMS
----------

  Algorithm    Type       Optimality                  Heuristic
  ---------    --------   ------------------------    -------------------------
  DFS          Search     No guarantee                None
  BFS          Search     Optimal                     None
  A* h1        Search     Optimal (admissible)        Manhattan distance
  A* h2        Search     Near-optimal (inadmissible) Euclidean + corridor weight
  MDP VI       Planning   Optimal (full state space)  N/A
  MDP PI       Planning   Optimal (full state space)  N/A


MDP Configuration
~~~~~~~~~~~~~~~~~

Both MDP solvers share the same configuration:

  - Discount factor (gamma)       = 0.99
  - Step cost                     = -1.0 per move
  - Goal reward                   = +100.0
  - Convergence threshold (eps)   = 1e-4
  - Max iterations                = 500
  - Deterministic transitions     (p_intended = 1.0)


BENCHMARK SETUP
---------------

Mazes are procedurally generated at six sizes (7x7 to 75x75) with varying path
counts (1-20 alternative routes). Start and goal positions are randomised with a
minimum Manhattan distance constraint. Each configuration runs multiple
repetitions, producing 94 maze instances x 6 algorithms = 564 runs total.

Metrics recorded:

  Search/Planning:
    - Execution time, nodes visited, search coverage, search efficiency ratio,
      time per node

  Path Quality:
    - Path length, turn count, optimality ratio (vs BFS baseline),
      suboptimality percentage

  Memory:
    - Peak frontier size, peak memory usage

  MDP-specific:
    - Planning iterations, planning time per state, extraction time per state,
      cumulative reward, discounted return


OUTPUTS
-------

Plots (plots/):

  01_time_complexity.png              Execution time vs maze size
  02_space_complexity.png             Nodes visited vs maze size
  03_path_optimality.png              Path quality comparison
  04_search_coverage.png              Fraction of state space explored
  05_astar_comparison.png             A* h1 vs h2 detailed comparison
  06_mdp_analysis.png                 MDP convergence and planning metrics
  07_efficiency_metrics.png           Time per node and search efficiency
  08_ranking_heatmap.png              Algorithm ranking across all metrics
  09_scalability.png                  Performance scaling with maze size
  10_path_characteristics.png         Turn count and path smoothness
  11_completion_rate.png              Success rates by algorithm and size
  12_search_efficiency_deep.png       Deep dive into efficiency ratio
  13_path_quality_deep.png            Suboptimality distribution
  14_success_and_coverage_by_paths    Effect of path count on performance
  15_memory_metrics.png               Memory usage comparison
  suboptimality_breakdown.png         DFS suboptimality breakdown

Tables (tables/):

  {Algorithm}_metrics_table.tex       Per-algorithm metric tables
  consolidated_metrics_table.tex      Consolidated comparison table
  mdp_planning_metrics_table.tex      MDP planning metrics (VI vs PI)
  mdp_reward_by_size_table.tex        MDP reward outcomes by maze size


DEPENDENCIES
------------

  - Python >= 3.8
  - Flask, Flask-CORS (backend server)
  - Selenium, webdriver-manager (benchmark automation)
  - pandas, matplotlib, numpy (analysis and plotting)

Install all:

     pip install -e ".[dev]"
     pip install pandas matplotlib numpy


LICENCE
-------

MIT -- see LICENSE.
