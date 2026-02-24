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
    with open(RESULTS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['RunID', 'Size', 'Algorithm', 'Time(s)', 'VisitedNodes', 'PathLength'])

    benchmark_configs = [
        {'size': 20, 'count': 10},
        {'size': 50, 'count': 10} 
    ]
    
    # Python Algorithms mapping in select
    # 6: DFS, 7: BFS, 8: A*
    algorithms = [
        {'name': 'DFS', 'value': '6'},
        {'name': 'BFS', 'value': '7'},
        {'name': 'AStar', 'value': '8'}
    ]

    run_id = 0

    for config in benchmark_configs:
        size = config['size']
        count = config['count']
        
        print(f"Starting benchmark for Size {size}x{size}...")
        
        # Set grid size for this batch
        driver.execute_script(f"""
            window.MAZE_CONFIG = window.MAZE_CONFIG || {{}};
            window.MAZE_CONFIG.grid = window.MAZE_CONFIG.grid || {{}};
            window.MAZE_CONFIG.grid.width = {size};
            window.MAZE_CONFIG.grid.height = {size};
            window.MAZE_CONFIG.grid.mode = 'fixed';
            hidden_clear();
        """)
        time.sleep(0.5)

        for i in range(count):
            run_id += 1
            print(f"  Run {i+1}/{count} (Total ID: {run_id})")

            # Use maze_generators() via the select, which calls hidden_clear() first.
            # hidden_clear() destroys and rebuilds the entire DOM table, giving a
            # 100% clean visual slate with no leftover cell_algo/cell_path classes.
            print("    Generating maze...")
            driver.execute_script("""
                document.querySelector('#slct_2').value = '1';
                maze_generators();
            """)

            # randomized_depth_first is synchronous; generating=false is set at its end.
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return generating === false")
            )

            wall_count = driver.execute_script("return document.querySelectorAll('.cell_wall').length")
            # total_cells = driver.execute_script("return document.querySelectorAll('.cell').length")
            # print(f"    [DEBUG] Walls: {wall_count}, Total Cells: {total_cells}")
            
            # For each solver
            for algo in algorithms:
                algo_name = algo['name']
                algo_val = algo['value']

                # Select Algorithm
                driver.execute_script(f"document.querySelector('#slct_1').value = '{algo_val}';")

                # Reset both flags before each run
                driver.execute_script("window.lastPythonResult = null; window.animation_complete = false;")

                # Trigger Solve (play button calls clear_grid + maze_solvers internally)
                driver.find_element(By.ID, "play").click()

                # Step 1: wait for Python backend to return a result
                try:
                    WebDriverWait(driver, 15).until(
                        lambda d: d.execute_script("return window.lastPythonResult !== null")
                    )
                except Exception:
                    print(f"    Timeout waiting for Python result for {algo_name}")
                    continue

                # Retrieve metrics immediately (Python exec time is in the result)
                result = driver.execute_script("return window.lastPythonResult;")

                # Step 2: wait for the patched interval to signal it has fully drawn everything
                try:
                    WebDriverWait(driver, 30).until(
                        lambda d: d.execute_script("return window.animation_complete === true")
                    )
                except Exception:
                    print(f"    Warning: animation_complete timeout for {algo_name}, screenshotting anyway")

                # One frame buffer for final repaint
                time.sleep(0.1) 
                
                metrics = {
                    'time': result.get('time', 0),
                    'visited': len(result.get('visited_nodes', [])),
                    'path': len(result.get('path', []))

                }
                
                print(f"    {algo_name}: {metrics}")
                
                # Save to CSV
                with open(RESULTS_FILE, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([run_id, size, algo_name, metrics['time'], metrics['visited'], metrics['path']])
                
                # Screenshot
                screenshot_path = os.path.join(IMAGES_DIR, f"run_{run_id}_{size}_{algo_name}.png")
                driver.save_screenshot(screenshot_path)
            
            if DEBUG_MODE:
                print("[DEBUG] Stopping after 1 maze. Press Enter to clean up and exit...")
                pass

finally:
    print("Cleaning up...")
    driver.quit()
    frontend_process.terminate()
    backend_process.terminate()
    print("Done.")
