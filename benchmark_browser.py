import os
import time
import csv
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------

def compute_turn_count(path):
    """Count direction changes in a path (list of [row, col])."""
    if not path or len(path) < 3:
        return 0
    turns = 0
    for i in range(1, len(path) - 1):
        dr1 = path[i][0] - path[i - 1][0]
        dc1 = path[i][1] - path[i - 1][1]
        dr2 = path[i + 1][0] - path[i][0]
        dc2 = path[i + 1][1] - path[i][1]
        if (dr1, dc1) != (dr2, dc2):
            turns += 1
    return turns


def safe_div(numerator, denominator, default='N/A'):
    """Division that returns default instead of ZeroDivisionError."""
    if denominator is None or denominator == 0:
        return default
    return numerator / denominator


def compute_metrics(result, free_cells, optimal_path_length):
    """
    Derive all benchmark metrics from a raw algorithm result dict.

    Works for both search algorithms (BFS/DFS/A*) and MDP algorithms.
    MDP-specific fields (planning_iters, planning_time, etc.) are 'N/A'
    for search algorithms and populated from the result for MDP ones.

    Parameters
    ----------
    result : dict  – raw response from window.lastPythonResult
    free_cells : int – passable cells in the maze (total - walls)
    optimal_path_length : int | None – BFS path length for this maze

    Returns
    -------
    dict of all metrics (ready to drop straight into the CSV row)
    """
    path          = result.get('path', [])
    visited_nodes = result.get('visited_nodes', [])
    t             = result.get('time', 0)
    success       = bool(path)

    path_length   = len(path)
    turn_count    = compute_turn_count(path)

    # For MDP the meaningful "nodes expanded" is states_valued (every cell
    # that participated in the Bellman sweep).  For search it is visited_nodes.
    states_valued = result.get('states_valued', None)
    visited_count = states_valued if states_valued is not None else len(visited_nodes)

    # ------------------------------------------------------------------
    # Search / planning efficiency
    # ------------------------------------------------------------------
    search_coverage  = safe_div(visited_count, free_cells)
    search_eff_ratio = safe_div(path_length, visited_count)   # higher = less wasted work
    time_per_node    = safe_div(t, visited_count)

    # ------------------------------------------------------------------
    # Path quality (relative to BFS optimal)
    # ------------------------------------------------------------------
    if success and optimal_path_length and optimal_path_length > 0:
        optimality_ratio = path_length / optimal_path_length
        suboptimality    = (path_length - optimal_path_length) / optimal_path_length
    else:
        optimality_ratio = 'N/A'
        suboptimality    = 'N/A'

    # ------------------------------------------------------------------
    # MDP-specific metrics (N/A for search algorithms)
    # ------------------------------------------------------------------
    def _fmt(key, fmt=None):
        v = result.get(key)
        if v is None:
            return 'N/A'
        return f'{v:{fmt}}' if fmt else v

    planning_iters   = _fmt('planning_iters')
    planning_time    = _fmt('planning_time',  '.8f')
    extraction_time  = _fmt('extraction_time','.8f')
    cum_reward       = _fmt('cumulative_reward', '.4f')
    disc_return      = _fmt('discounted_return', '.4f')

    return {
        'success':           1 if success else 0,
        'time':              t,
        'visited_nodes':     visited_count,
        'path_length':       path_length,
        'turn_count':        turn_count,
        'search_coverage':   search_coverage,
        'search_eff_ratio':  search_eff_ratio,
        'time_per_node':     time_per_node,
        'optimality_ratio':  optimality_ratio,
        'suboptimality':     suboptimality,
        # MDP-only
        'planning_iters':    planning_iters,
        'planning_time':     planning_time,
        'extraction_time':   extraction_time,
        'cumulative_reward': cum_reward,
        'discounted_return': disc_return,
        'states_valued':     states_valued if states_valued is not None else 'N/A',
    }

# Configuration
DEBUG_MODE = False  # Run full benchmark
FRONTEND_PORT = 8000
BACKEND_PORT = 5000
# Updated paths to be relative to the expected CWD (/home/advik/AI) or the file location
# Since script is in path_finding/, but executed from there or from AI/
# Let's use abspath and __file__ to be safe
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "submodules/Maze_solver_py")
BACKEND_DIR = os.path.join(BASE_DIR, "submodules/Maze_solver_py") 
RESULTS_FILE = os.path.join(BASE_DIR, "benchmark_results.csv")
IMAGES_DIR = os.path.join(BASE_DIR, "benchmark_images")

# Ensure images directory exists
os.makedirs(IMAGES_DIR, exist_ok=True)

# Start Servers
print("Starting servers...")
frontend_log = open("frontend.log", "w")
backend_log = open("backend.log", "w")

frontend_process = subprocess.Popen(
    ["python3", "-m", "http.server", str(FRONTEND_PORT)],
    cwd=FRONTEND_DIR,
    stdout=frontend_log,
    stderr=frontend_log
)
backend_process = subprocess.Popen(
    ["python3", "backend/server.py"],
    cwd=BACKEND_DIR,
    stdout=backend_log,
    stderr=backend_log
)

# Give servers time to start
time.sleep(3)

# Setup Selenium
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Commented out to try and show UI (might fail if no display)
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=chrome_options
)

try:
    print("Loading page...")
    driver.get(f"http://localhost:{FRONTEND_PORT}/index.html")
    
    # Wait for page load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "slct_1")) # Algo selector
    )
    
    # Fix 1: override hidden_clear to always regenerate grid regardless of window size check
    # Fix 2: patch maze_solvers_interval to set window.animation_complete when fully done
    driver.execute_script("""
        window.hidden_clear = function() {
            for (let i = 0; i < timeouts.length; i++)
                clearTimeout(timeouts[i]);
            timeouts = [];
            clearInterval(my_interval);
            delete_grid();
            init_css_properties_before();
            generate_grid();
            init_css_properties_after();
            visualizer_event_listeners();
        };

        // Patch the global maze_solvers_interval so we get a reliable completion signal.
        // The original is defined at global scope so assigning here overrides it.
        window.animation_complete = false;
        window.maze_solvers_interval = function() {
            my_interval = window.setInterval(function() {
                if (!path) {
                    if (node_list_index >= node_list.length) {
                        if (!found) {
                            clearInterval(my_interval);
                            window.animation_complete = true;  // no-path end
                            return;
                        }
                        path = true;
                        place_to_cell(start_pos[0], start_pos[1]).classList.add('cell_path');
                        return;
                    }
                    let node = node_list[node_list_index];
                    place_to_cell(node[0], node[1]).classList.add('cell_algo');
                    node_list_index++;
                } else {
                    if (path_list_index >= path_list.length) {
                        place_to_cell(target_pos[0], target_pos[1]).classList.add('cell_path');
                        clearInterval(my_interval);
                        window.animation_complete = true;  // path-found end
                        return;
                    }
                    let path_node = path_list[path_list_index];
                    place_to_cell(path_node[0], path_node[1]).classList.remove('cell_algo');
                    place_to_cell(path_node[0], path_node[1]).classList.add('cell_path');
                    path_list_index++;
                }
            }, 10);
        };
    """)

    # Prepare CSV
    CSV_COLUMNS = [
        # ── maze context ──────────────────────────────────────────────
        'RunID', 'Size', 'PathCount', 'WallDensity', 'FreeCells', 'ManhattanDist', 'AStarH1PathLength',
        # ── per-algorithm ─────────────────────────────────────────────
        'Algorithm', 'Success',
        'Time(s)', 'VisitedNodes', 'PathLength', 'TurnCount',
        # ── search / planning efficiency ──────────────────────────────
        'SearchCoverage', 'SearchEffRatio', 'TimePerNode',
        # ── path quality ──────────────────────────────────────────────
        'PathOptimalityRatio', 'Suboptimality',
        # ── MDP-specific (N/A for search algorithms) ──────────────────
        'PlanningIters', 'PlanningTime(s)', 'ExtractionTime(s)',
        'CumulativeReward', 'DiscountedReturn', 'StatesValued',
    ]
    with open(RESULTS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)

    # Each config: size × path_counts × count_per mazes
    # path_count=0 → unsolvable (start walled off)
    # path_count=1 → perfect maze (one unique solution)
    # path_count>1 → N-1 extra wall holes punched = ≈N alternative routes
    benchmark_configs = [
        {'size': 20, 'path_counts': [0, 1, 2, 5, 10], 'count_per': 3},
        {'size': 50, 'path_counts': [0, 1, 2, 5, 10], 'count_per': 3},
    ]

    # Python Algorithms mapping in select
    # 1: DFS, 2: BFS, 3: A* h1 (Manhattan), 4: A* h2 (Corridor-Aware)
    # 5: MDP Value Iteration, 6: MDP Policy Iteration
    algorithms = [
        {'name': 'DFS',       'value': '1'},
        {'name': 'BFS',       'value': '2'},
        {'name': 'AStar_h1',  'value': '3'},
        {'name': 'AStar_h2',  'value': '4'},
        {'name': 'MDP_VI',    'value': '5'},
        {'name': 'MDP_PI',    'value': '6'},
    ]

    run_id = 0

    for config in benchmark_configs:
        size         = config['size']
        path_counts  = config['path_counts']
        count_per    = config['count_per']

        print(f"Starting benchmark for Size {size}x{size}...")

        # Set grid size for this batch (done once per size)
        driver.execute_script(f"""
            window.MAZE_CONFIG = window.MAZE_CONFIG || {{}};
            window.MAZE_CONFIG.grid = window.MAZE_CONFIG.grid || {{}};
            window.MAZE_CONFIG.grid.width = {size};
            window.MAZE_CONFIG.grid.height = {size};
            window.MAZE_CONFIG.grid.mode = 'fixed';
            hidden_clear();
        """)
        time.sleep(0.5)

        for path_count in path_counts:
          for i in range(count_per):
            run_id += 1
            print(f"  PathCount={path_count}  Rep {i+1}/{count_per}  (RunID {run_id})")

            # ------------------------------------------------------------------
            # Generate a fresh maze with the requested path-count setting
            # ------------------------------------------------------------------
            print("    Generating maze...")
            driver.execute_script(f"""
                window.TARGET_PATH_COUNT = {path_count};
                document.querySelector('#slct_2').value = '1';
                maze_generators();
            """)
            # Restore default after generation so the UI isn't affected
            driver.execute_script("window.TARGET_PATH_COUNT = 1;")

            # randomized_depth_first is synchronous; generating=false is set at its end.
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return generating === false")
            )

            # ------------------------------------------------------------------
            # Extract maze context metrics from the DOM / JS state
            # ------------------------------------------------------------------
            maze_info = driver.execute_script("""
                var total  = document.querySelectorAll('.cell').length;
                var walls  = document.querySelectorAll('.cell_wall').length;
                var free   = total - walls;
                var sp     = (typeof start_pos  !== 'undefined') ? start_pos  : [0, 0];
                var tp     = (typeof target_pos !== 'undefined') ? target_pos : [0, 0];
                var manhattan = Math.abs(sp[0] - tp[0]) + Math.abs(sp[1] - tp[1]);
                return {
                    total_cells:  total,
                    wall_cells:   walls,
                    free_cells:   free,
                    wall_density: total > 0 ? walls / total : 0,
                    manhattan:    manhattan
                };
            """)
            total_cells  = maze_info['total_cells']
            wall_cells   = maze_info['wall_cells']
            free_cells   = maze_info['free_cells']
            wall_density = maze_info['wall_density']
            manhattan    = maze_info['manhattan']
            print(f"    Maze info: {total_cells} cells, {wall_cells} walls "
                  f"(density={wall_density:.2f}), manhattan={manhattan}")

            # ------------------------------------------------------------------
            # Run every algorithm on the same maze; collect raw results first
            # ------------------------------------------------------------------
            raw_results = {}   # algo_name → raw result dict from backend

            for algo in algorithms:
                algo_name = algo['name']
                algo_val  = algo['value']

                driver.execute_script(f"document.querySelector('#slct_1').value = '{algo_val}';")
                driver.execute_script("window.lastPythonResult = null; window.animation_complete = false;")
                driver.find_element(By.ID, "play").click()

                # Wait for Python backend result
                try:
                    WebDriverWait(driver, 15).until(
                        lambda d: d.execute_script("return window.lastPythonResult !== null")
                    )
                except Exception:
                    print(f"    Timeout waiting for Python result for {algo_name}")
                    raw_results[algo_name] = None
                    continue

                result = driver.execute_script("return window.lastPythonResult;")

                # Wait for animation to finish
                try:
                    WebDriverWait(driver, 30).until(
                        lambda d: d.execute_script("return window.animation_complete === true")
                    )
                except Exception:
                    print(f"    Warning: animation_complete timeout for {algo_name}")

                time.sleep(0.1)  # one frame buffer for final repaint

                raw_results[algo_name] = result

                # Screenshot
                screenshot_path = os.path.join(IMAGES_DIR, f"run_{run_id}_{size}_pc{path_count}_{algo_name}.png")
                driver.save_screenshot(screenshot_path)

            # ------------------------------------------------------------------
            # Overlay screenshot: all 6 paths on one grid, no exploration dots
            # ------------------------------------------------------------------
            try:
                import json as _json
                js_paths = {}
                for algo in algorithms:
                    r = raw_results.get(algo['name'])
                    if r and r.get('path'):
                        js_paths[algo['name']] = r['path']

                driver.execute_script(f"""
                    var pathsData = {_json.dumps(js_paths)};
                    var resultsMap = {{}};
                    for (var k in pathsData) {{
                        resultsMap[k] = {{ path: pathsData[k] }};
                    }}
                    if (typeof show_overlay === 'function') {{
                        show_overlay(resultsMap);
                    }}
                """)
                time.sleep(0.4)  # let gradient repaint settle
                overlay_path = os.path.join(IMAGES_DIR, f"run_{run_id}_{size}_pc{path_count}_OVERLAY.png")
                driver.save_screenshot(overlay_path)
                driver.execute_script("""
                    if (typeof clear_overlay === 'function') clear_overlay();
                """)
            except Exception as e:
                print(f"    Warning: overlay screenshot failed: {e}")

            # ------------------------------------------------------------------
            # A* h1 (admissible Manhattan heuristic) gives the ground-truth
            # optimal path length.  Guaranteed-shortest on uniform-cost grids.
            # ------------------------------------------------------------------
            astar_h1_raw = raw_results.get('AStar_h1')
            if astar_h1_raw and astar_h1_raw.get('path'):
                optimal_path_length = len(astar_h1_raw['path'])
            else:
                optimal_path_length = None   # unsolvable maze or A*h1 failed

            # ------------------------------------------------------------------
            # Compute all metrics and write one CSV row per algorithm
            # ------------------------------------------------------------------
            with open(RESULTS_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                for algo in algorithms:
                    algo_name = algo['name']
                    raw = raw_results.get(algo_name)
                    if raw is None:
                        continue   # timed-out run; skip

                    m = compute_metrics(raw, free_cells, optimal_path_length)
                    print(f"    {algo_name}: success={m['success']}  "
                          f"t={m['time']:.5f}s  visited={m['visited_nodes']}  "
                          f"path={m['path_length']}  turns={m['turn_count']}  "
                          f"coverage={m['search_coverage']:.3f}  "
                          f"optRatio={m['optimality_ratio']}")

                    writer.writerow([
                        run_id, size, path_count,
                        f"{wall_density:.4f}", free_cells, manhattan, optimal_path_length if optimal_path_length else 'N/A',
                        algo_name, m['success'],
                        m['time'], m['visited_nodes'], m['path_length'], m['turn_count'],
                        f"{m['search_coverage']:.6f}"  if isinstance(m['search_coverage'],  float) else m['search_coverage'],
                        f"{m['search_eff_ratio']:.6f}" if isinstance(m['search_eff_ratio'],  float) else m['search_eff_ratio'],
                        f"{m['time_per_node']:.8f}"    if isinstance(m['time_per_node'],     float) else m['time_per_node'],
                        f"{m['optimality_ratio']:.6f}" if isinstance(m['optimality_ratio'],  float) else m['optimality_ratio'],
                        f"{m['suboptimality']:.6f}"    if isinstance(m['suboptimality'],     float) else m['suboptimality'],
                        # MDP-specific columns
                        m['planning_iters'],
                        m['planning_time'],
                        m['extraction_time'],
                        m['cumulative_reward'],
                        m['discounted_return'],
                        m['states_valued'],
                    ])

            if DEBUG_MODE:
                print("[DEBUG] Stopping after 1 maze. Press Enter to clean up and exit...")
                pass


finally:
    print("Cleaning up...")
    driver.quit()
    frontend_process.terminate()
    backend_process.terminate()
    print("Done.")
