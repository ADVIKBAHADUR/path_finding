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
    
    # FORCE visualizer fix: Override hidden_clear to ALWAYS generate grid regardless of window size
    driver.execute_script("""
        window.hidden_clear = function() {
            for (let i = 0; i < timeouts.length; i++)
                clearTimeout(timeouts[i]);

            timeouts = [];
            clearInterval(my_interval);
            delete_grid();
            
            // ALWAYS generate grid, ignore window width check
            init_css_properties_before();
            generate_grid();
            init_css_properties_after();
            visualizer_event_listeners();
        };

        window.instant_render = function() {
            // Stop any existing intervals
            if (typeof my_interval !== 'undefined' && my_interval) clearInterval(my_interval);
            if (typeof timeouts !== 'undefined') {
                for(let t of timeouts) clearTimeout(t);
                timeouts = [];
            }
            
            // Draw Visited
            if (typeof node_list !== 'undefined') {
                for (let i = 0; i < node_list.length; i++) {
                    let node = node_list[i];
                    place_to_cell(node[0], node[1]).classList.add("cell_algo");
                }
            }
            
            // Draw Path
            if (typeof path_list !== 'undefined') {
                for (let i = 0; i < path_list.length; i++) {
                    let path_node = path_list[i];
                    place_to_cell(path_node[0], path_node[1]).classList.remove("cell_algo");
                    place_to_cell(path_node[0], path_node[1]).classList.add("cell_path");
                }
            }
            
            // Mark start/target explicitly to be safe
            if (typeof start_pos !== 'undefined') place_to_cell(start_pos[0], start_pos[1]).classList.add("start");
            if (typeof target_pos !== 'undefined') place_to_cell(target_pos[0], target_pos[1]).classList.add("target");

            window.rendering_complete = true;
        };

        // Override the interval function to just call instant_render
        window.maze_solvers_interval = function() {
            window.rendering_complete = false;
            // Delay slightly to ensure browser paints invalidation? No, just run.
            setTimeout(window.instant_render, 0);
        };
        
        // Also speed up generation if possible? 
        // We can override random_int or similar but user liked the look.
        // We will just wait.
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
        
        # Resize Grid
        driver.execute_script(f"""
            window.MAZE_CONFIG = window.MAZE_CONFIG || {{}};
            window.MAZE_CONFIG.grid = window.MAZE_CONFIG.grid || {{}};
            window.MAZE_CONFIG.grid.width = {size};
            window.MAZE_CONFIG.grid.height = {size};
            window.MAZE_CONFIG.grid.mode = 'fixed';
            
            // Ensure clean state before generation
            // Remove ALL tables to be safe
            var tables = document.querySelectorAll("#my_table");
            tables.forEach(t => t.remove());
            
            // Override delete_grid to be safe just in case hidden_clear calls it
            window.delete_grid = function() {{
                var t = document.querySelector("#my_table");
                if (t) t.remove();
            }};

            // Now call hidden_clear which will generate a NEW single grid
            hidden_clear(); 
        """)
        time.sleep(1) # Allow DOM update

        for i in range(count):
            run_id += 1
            print(f"  Run {i+1}/{count} (Total ID: {run_id})")
            
            # Generate Maze (Direct Call to avoid UI issues)
            # 'randomized_depth_first' corresponds to value '1'
            print("    Generating maze via JS direct call...")
            try:
                driver.execute_script("""
                    if (typeof randomized_depth_first === 'function') {
                        document.querySelector('#slct_2').value = '1';
                        randomized_depth_first();
                    } else {
                        console.error("randomized_depth_first is not defined!");
                        // Fallback to dispatch event incase it's scoped?
                        document.querySelector('#slct_2').value = '1';
                        document.querySelector('#slct_2').dispatchEvent(new Event('change'));
                    }
                """)
            except Exception as e:
                 print(f"Error executing generation script: {e}")
            
            # Wait for generation to likely complete (it's synchronous usually, but good to wait)
            time.sleep(1)

            print("    Waiting for any async generation flags...")
            try:
                # Wait for generating flag AND verify walls > 0
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return typeof generating !== 'undefined' && generating === false")
                )
                
                # Check actual wall population
                start_w = time.time()
                current_walls = 0
                while time.time() - start_w < 5:
                    current_walls = driver.execute_script("return document.querySelectorAll('.cell_wall').length")
                    if current_walls > 10: # Arbitrary threshold ensuring some walls exist
                         break
                    time.sleep(0.5)
                
                if current_walls == 0:
                     print("    ERROR: Generation finished but NO walls found! Retrying selection...")
                     # Retry selection forcefully
                     driver.execute_script("document.querySelector('#slct_2').value = '1';")
                     driver.execute_script("document.querySelector('#slct_2').dispatchEvent(new Event('change'));")
                     time.sleep(3)
                     
            except Exception as e:
                print(f"    WARNING: Generation timeout or error: {e}")
                driver.execute_script("generating = false;")
            
            time.sleep(2)

            wall_count = driver.execute_script("return document.querySelectorAll('.cell_wall').length")
            # total_cells = driver.execute_script("return document.querySelectorAll('.cell').length")
            # print(f"    [DEBUG] Walls: {wall_count}, Total Cells: {total_cells}")
            
            # Disable animations globally but PRESERVE original styling (images/colors)
            # We ONLY want to kill the transition time so screenshots are instant.
            driver.execute_script("""
                var style = document.createElement('style');
                style.innerHTML = `
                    .cell_algo { 
                        animation: none !important; 
                        transition: none !important; 
                        /* Do NOT override background-image or color - let CSS handle the dots */
                    }
                    .cell_path { 
                        animation: none !important; 
                        transition: none !important; 
                    }
                    .visited_cell {
                        animation: none !important;
                        transition: none !important;
                    }
                `;
                document.head.appendChild(style);
            """)

            # For each solver
            for algo in algorithms:
                algo_name = algo['name']
                algo_val = algo['value']
                
                # Select Algorithm
                driver.execute_script(f"document.querySelector('#slct_1').value = '{algo_val}';")
                
                # Reset flags
                driver.execute_script("window.rendering_complete = false; window.lastPythonResult = null;")
                
                # Trigger Solve
                driver.find_element(By.ID, "play").click()
                
                # Wait for Python Result
                try:
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return window.lastPythonResult && window.rendering_complete")
                    )
                except Exception as e:
                    print(f"    Timeout waiting for {algo_name}")
                    continue
                
                # Retrieve Metrics from Window object
                result = driver.execute_script("return window.lastPythonResult;")
                
                # Wait for render to stick (reduced since we disabled animations)
                time.sleep(0.5) 
                
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
