#!/usr/bin/env python3
"""
Generate per-algorithm LaTeX metric tables from benchmark_results.csv.

Each algorithm gets three horizontal tables (metrics as columns):
  1. Search Efficiency
  2. Path Quality
  3. Memory & Robustness

Output: one standalone .tex file per algorithm in tables/ directory.
"""

import os
import pandas as pd
import numpy as np

CSV_PATH = os.path.join(os.path.dirname(__file__), "benchmark_results_g.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "tables")

# ---------------------------------------------------------------------------
# Metric definitions: (display_name, csv_col_or_None, format_spec)
# If csv_col is None, it is computed separately.
# ---------------------------------------------------------------------------

SEARCH_EFFICIENCY = [
    ("Coverage",           "SearchCoverage",       ".4f",  None),
    ("Eff.\\ Ratio",       "SearchEffRatio",       ".4f",  None),
    ("Time/Node ($\\mu$s)", "TimePerNode",          ".2f",  1e6),
]

PATH_QUALITY = [
    ("Opt.\\ Ratio",    "PathOptimalityRatio",  ".4f",  None),
    ("Suboptimality",   "Suboptimality",        ".4f",  None),
    ("Turns/Size",      "NormTurnCount",        ".2f",  None),
]

MEMORY_ROBUSTNESS = [
    ("Peak Frontier",    "PeakFrontier",         ".1f",  None),
    ("Peak Mem.\\ (KB)", "PeakMemory(bytes)",    ".1f",  1/1024),
    ("Success Rate",     None,                   ".4f",  None),   # computed
]

# MDP-only metrics.
# PlanningTimePerState stored in µs; shown in ms (scale=1/1000) to keep columns compact.
# ExtractionTimePerState in µs/state — values are small so µs is fine.
# PlanningIters uses median [Q1, Q3] (see fmt_median_iqr) because the distribution is
# bimodal: small mazes converge in ~35 iters while large mazes often hit the 500-iter cap.
# RewardPerStep is CumulativeReward / PathLength on successful runs.
#
# Two-line column headers: use '\\\\' (two backslashes in Python string = '\\' in file
# = LaTeX newline inside a table cell). Gives compact but fully-spelled-out headers.
MDP_SPECIFIC = [
    ("Planning Iterations",              "PlanningIters",          ".0f",  None),
    ("Planning Time (ms/state)",         "PlanningTimePerState",   ".1f",  1/1000),
    ("Extraction Time ($\\mu$s/state)",  "ExtractionTimePerState", ".2f",  None),
]

CONSOLIDATED_METRICS = [
    ("Time/Node ($\\mu$s)", "TimePerNode",          ".2f",  1e6),
    ("Peak Mem.\\ (KB)",   "PeakMemory(bytes)",    ".1f",  1/1024),
    ("Opt.\\ Ratio",      "PathOptimalityRatio",  ".4f",  None),
    ("Coverage",           "SearchCoverage",       ".4f",  None),
]


def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Strip any whitespace from column names (Windows line-endings, etc.)
    df.columns = df.columns.str.strip()
    return df


def compute_algorithm_stats(df: pd.DataFrame) -> dict:
    """Return {algorithm: {metric_col: (mean, std), 'SuccessRate': (mean, std)}}."""

    # Compute normalised turn count (per grid size)
    df["NormTurnCount"] = df["TurnCount"] / df["Size"]

    # ------------------------------------------------------------------
    # MDP-specific derived columns (computed globally before grouping)
    # ------------------------------------------------------------------
    # PlanningTimePerState: planning wall-clock time in µs per state (FreeCells)
    # This removes the strong grid-size dependence and makes VI vs PI comparable.
    df["PlanningTimePerState"] = (
        pd.to_numeric(df["PlanningTime(s)"], errors="coerce")
        / df["FreeCells"] * 1e6
    )
    # ExtractionTimePerState: path-extraction time in µs per state
    df["ExtractionTimePerState"] = (
        pd.to_numeric(df["ExtractionTime(s)"], errors="coerce")
        / df["FreeCells"] * 1e6
    )
    # RewardPerStep: cumulative reward divided by path length (successful runs only)
    # Normalises out path-length dependence so short and long paths are comparable.
    df["RewardPerStep"] = (
        pd.to_numeric(df["CumulativeReward"], errors="coerce")
        / pd.to_numeric(df["PathLength"], errors="coerce")
    )

    stats = {}
    for algo, grp in df.groupby("Algorithm"):
        algo_stats = {}

        # Success rate computed over ALL runs
        algo_stats["SuccessRate"] = (grp["Success"].mean(), grp["Success"].std(ddof=1))

        # For path-quality metrics, only consider successful runs
        successful = grp[grp["Success"] == 1]

        # Collect all metric columns (standard + MDP-specific)
        metric_cols = set()
        for section in (SEARCH_EFFICIENCY, PATH_QUALITY, MEMORY_ROBUSTNESS,
                        CONSOLIDATED_METRICS, MDP_SPECIFIC):
            for _, col, _, _ in section:
                if col is not None:
                    metric_cols.add(col)

        # Path-quality and reward-per-step metrics should use successful runs only
        path_quality_cols = {
            "PathOptimalityRatio", "Suboptimality", "NormTurnCount", "RewardPerStep",
        }

        for col in metric_cols:
            subset = successful if col in path_quality_cols else grp
            vals = pd.to_numeric(subset[col], errors="coerce").dropna()
            if len(vals) > 0:
                algo_stats[col] = (vals.mean(), vals.std(ddof=1))
            else:
                algo_stats[col] = (float("nan"), float("nan"))

        # Robust statistics for PlanningIters: distribution is bimodal because
        # small mazes converge fast (~35 iters) while large mazes hit the 500-iter cap.
        # Store median and IQR so the table can use fmt_median_iqr.
        pi_vals = pd.to_numeric(grp["PlanningIters"], errors="coerce").dropna()
        if len(pi_vals) > 0:
            algo_stats["PlanningIters_median"] = pi_vals.median()
            algo_stats["PlanningIters_q25"]    = pi_vals.quantile(0.25)
            algo_stats["PlanningIters_q75"]    = pi_vals.quantile(0.75)
        else:
            algo_stats["PlanningIters_median"] = float("nan")
            algo_stats["PlanningIters_q25"]    = float("nan")
            algo_stats["PlanningIters_q75"]    = float("nan")

        stats[algo] = algo_stats
    return stats


def fmt_val(mean: float, std: float, spec: str, scale: float = None) -> str:
    """Format as  mean ± std  in LaTeX math mode (compact)."""
    if np.isnan(mean):
        return "---"
    if scale is not None:
        mean = mean * scale
        std = std * scale
    m = f"{mean:{spec}}"
    s = f"{std:{spec}}"
    return f"${m} \\pm {s}$"


def fmt_median_iqr(median: float, q25: float, q75: float, spec: str) -> str:
    """Format as  median [Q1, Q3]  in LaTeX math mode.

    Used for PlanningIters, whose distribution is bimodal across maze sizes
    (small mazes converge quickly; large mazes frequently hit the iteration cap).
    Median [IQR] is more informative than mean ± std in this case.
    """
    if np.isnan(median):
        return "---"
    return f"${median:{spec}}\ [{q25:{spec}}, {q75:{spec}}]$"


def build_horizontal_table(section_name: str, metrics: list, algo_stats: dict, algo: str) -> str:
    """Build a tabularx table with equal centred columns, full \\linewidth."""
    n_cols = len(metrics)
    col_spec = " ".join([">{\\centering\\arraybackslash}X"] * n_cols)

    lines = []
    headers = [m[0] for m in metrics]
    header_line = " & ".join(headers) + " \\\\"

    vals = []
    for display, col, spec, scale in metrics:
        if col is None:
            mean, std = algo_stats.get("SuccessRate", (float("nan"), float("nan")))
        else:
            mean, std = algo_stats.get(col, (float("nan"), float("nan")))
        vals.append(fmt_val(mean, std, spec, scale))
    value_line = " & ".join(vals) + " \\\\"

    lines.append(f"\\begin{{tabularx}}{{\\linewidth}}{{{col_spec}}}")
    lines.append("\\toprule")
    lines.append(header_line)
    lines.append("\\midrule")
    lines.append(value_line)
    lines.append("\\bottomrule")
    lines.append("\\end{tabularx}")

    return "\n".join(lines)


ALGO_DISPLAY = {
    "DFS":      "Depth-First Search (DFS)",
    "BFS":      "Breadth-First Search (BFS)",
    "AStar_h1": "A* with Heuristic $h_1$ (Manhattan)",
    "AStar_h2": "A* with Heuristic $h_2$ (Euclidean)",
    "MDP_VI":   "MDP Value Iteration",
    "MDP_PI":   "MDP Policy Iteration",
}


def _mdp_cells(algo_stats: dict) -> list:
    """Return formatted cell strings for the MDP-specific metrics row.

    PlanningIters uses median [Q1, Q3] instead of mean ± std because the
    distribution is bimodal across maze sizes.
    """
    cells = []
    for _, col, spec, scale in MDP_SPECIFIC:
        if col == "PlanningIters":
            cells.append(fmt_median_iqr(
                algo_stats.get("PlanningIters_median", float("nan")),
                algo_stats.get("PlanningIters_q25",    float("nan")),
                algo_stats.get("PlanningIters_q75",    float("nan")),
                spec,
            ))
        else:
            mean, std = algo_stats.get(col, (float("nan"), float("nan")))
            cells.append(fmt_val(mean, std, spec, scale))
    return cells


def _mdp_section(algo_stats: dict) -> str:
    """Build the MDP Planning Metrics horizontal table snippet."""
    n_cols = len(MDP_SPECIFIC)
    col_spec = " ".join([">{{\\centering\\arraybackslash}}X"] * n_cols)
    # Bold each two-line header
    headers  = ["\\textbf{" + m[0] + "}" for m in MDP_SPECIFIC]
    header_line = " & ".join(headers) + " \\\\"
    value_line  = " & ".join(_mdp_cells(algo_stats)) + " \\\\"
    return "\n".join([
        f"\\begin{{tabularx}}{{\\linewidth}}{{{col_spec}}}",
        "\\toprule",
        header_line,
        "\\midrule",
        value_line,
        "\\bottomrule",
        "\\end{tabularx}",
    ])


def generate_tex_file(algo: str, algo_stats: dict) -> str:
    """Return a complete, standalone LaTeX document for one algorithm."""
    display = ALGO_DISPLAY.get(algo, algo)
    is_mdp = algo.startswith("MDP")

    search_table   = build_horizontal_table("Search Efficiency",   SEARCH_EFFICIENCY, algo_stats, algo)
    quality_table  = build_horizontal_table("Path Quality",        PATH_QUALITY,       algo_stats, algo)
    memory_table   = build_horizontal_table("Memory & Robustness",  MEMORY_ROBUSTNESS,  algo_stats, algo)
    mdp_block = f"""
\\vspace{{6pt}}
\\textbf{{MDP Planning Metrics}}\\\\[2pt]
{_mdp_section(algo_stats)}
""" if is_mdp else ""

    tex = f"""%% Auto-generated metric table for {algo}
\\documentclass{{article}}
\\usepackage{{booktabs, amsmath, tabularx, float}}
\\begin{{document}}

\\begin{{table}}[H]
\\centering
\\caption{{Performance metrics for {display}.}}
\\label{{tab:metrics-{algo.lower().replace('_', '-')}}}

\\vspace{{4pt}}
\\textbf{{Search Efficiency}}\\\\[2pt]
{search_table}

\\vspace{{6pt}}
\\textbf{{Path Quality}}\\\\[2pt]
{quality_table}

\\vspace{{6pt}}
\\textbf{{Memory \\& Robustness}}\\\\[2pt]
{memory_table}
{mdp_block}
\\end{{table}}

\\end{{document}}
"""
    return tex


def generate_table_only(algo: str, algo_stats: dict) -> str:
    """Return ONLY the table environment (no documentclass) for inclusion via \\input."""
    display = ALGO_DISPLAY.get(algo, algo)
    is_mdp = algo.startswith("MDP")

    search_table   = build_horizontal_table("Search Efficiency",   SEARCH_EFFICIENCY, algo_stats, algo)
    quality_table  = build_horizontal_table("Path Quality",        PATH_QUALITY,       algo_stats, algo)
    memory_table   = build_horizontal_table("Memory & Robustness",  MEMORY_ROBUSTNESS,  algo_stats, algo)
    mdp_block = f"""
\\vspace{{6pt}}
\\textbf{{MDP Planning Metrics}}\\\\[2pt]
{_mdp_section(algo_stats)}
""" if is_mdp else ""

    tex = f"""%% Auto-generated metric table for {algo}
\\begin{{table}}[H]
\\centering
\\caption{{Performance metrics for {display}.}}
\\label{{tab:metrics-{algo.lower().replace('_', '-')}}}

\\vspace{{4pt}}
\\textbf{{Search Efficiency}}\\\\[2pt]
{search_table}

\\vspace{{6pt}}
\\textbf{{Path Quality}}\\\\[2pt]
{quality_table}

\\vspace{{6pt}}
\\textbf{{Memory \\& Robustness}}\\\\[2pt]
{memory_table}
{mdp_block}
\\end{{table}}
"""
    return tex


# Short display names for the MDP consolidated table (no 'MDP' prefix).
_MDP_SHORT = {
    "MDP_VI": "Value Iteration (VI)",
    "MDP_PI": "Policy Iteration (PI)",
}


def generate_mdp_consolidated_table(stats: dict) -> str:
    """Return a standalone 2-row table comparing MDP_VI and MDP_PI on MDP-specific metrics."""
    metrics = MDP_SPECIFIC
    n_metric = len(metrics)
    # Single braces (not double) — this is a plain string, not an f-string template.
    col_spec = ">{\\raggedright\\arraybackslash}X " + " ".join([">{\\centering\\arraybackslash}X"] * n_metric)

    lines = [
        "%% Auto-generated MDP-specific consolidated metric table",
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{MDP planning phase metrics: Value Iteration (VI) vs.\\ Policy Iteration (PI). "
        "Planning and extraction times are normalised by the number of free cells (state space size) "
        "to allow fair comparison across maze sizes. "
        "\\emph{Planning Iterations} is reported as median [Q\\textsubscript{1}, Q\\textsubscript{3}] "
        "because the distribution is bimodal---small mazes converge in $\\sim$35 iterations "
        "while large mazes frequently reach the 500-iteration cap; "
        "all other columns report mean $\\pm$ std. "
        "Reward outcomes (cumulative reward, discounted return) are strongly size-dependent "
        "and are reported per maze size in Table~\\ref{tab:mdp-reward-by-size}.}",
        "\\label{tab:metrics-mdp-planning}",
        "\\vspace{4pt}",
        f"\\begin{{tabularx}}{{\\linewidth}}{{{col_spec}}}",
        "\\toprule",
    ]
    headers = ["\\textbf{Algorithm}"] + ["\\textbf{" + m[0] + "}" for m in metrics]
    lines.append(" & ".join(headers) + " \\\\"
                 + "\n\\addlinespace[-2pt]")
    lines.append("\\midrule")

    for algo in ("MDP_VI", "MDP_PI"):
        if algo not in stats:
            continue
        algo_stats = stats[algo]
        display = _MDP_SHORT.get(algo, algo)
        vals = [display] + _mdp_cells(algo_stats)
        lines.append(" & ".join(vals) + " \\\\")

    lines += ["\\bottomrule", "\\end{tabularx}", "\\end{table}"]
    return "\n".join(lines)


def generate_consolidated_table(stats: dict, algo_order: list) -> str:
    """Return ONLY the table environment for a consolidated summary table."""
    metrics = CONSOLIDATED_METRICS
    n_cols = len(metrics) + 1
    col_spec = ">{\\raggedright\\arraybackslash}X " + " ".join([">{\\centering\\arraybackslash}X"] * len(metrics))

    lines = []
    headers = ["Algorithm"] + [m[0] for m in metrics]
    header_line = " & ".join(headers) + " \\\\"

    lines.append(f"%% Auto-generated consolidated metric table")
    lines.append(f"\\begin{{table}}[H]")
    lines.append(f"\\centering")
    lines.append(f"\\caption{{Consolidated performance comparison across selected metrics.}}")
    lines.append(f"\\label{{tab:metrics-consolidated}}")
    lines.append(f"\\vspace{{4pt}}")
    lines.append(f"\\begin{{tabularx}}{{\\linewidth}}{{{col_spec}}}")
    lines.append("\\toprule")
    lines.append(header_line)
    lines.append("\\midrule")

    for algo in algo_order:
        if algo not in stats:
            continue
        algo_stats = stats[algo]
        display = ALGO_DISPLAY.get(algo, algo)
        vals = [display]
        for _, col, spec, scale in metrics:
            mean, std = algo_stats.get(col, (float("nan"), float("nan")))
            vals.append(fmt_val(mean, std, spec, scale))
        lines.append(" & ".join(vals) + " \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabularx}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def main():
    df = load_data(CSV_PATH)
    stats = compute_algorithm_stats(df)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    algo_order = ["DFS", "BFS", "AStar_h1", "AStar_h2", "MDP_VI", "MDP_PI"]

    for algo in algo_order:
        if algo not in stats:
            print(f"[WARN] Algorithm '{algo}' not found in data, skipping.")
            continue

        # Standalone .tex (full document)
        standalone = generate_tex_file(algo, stats[algo])
        standalone_path = os.path.join(OUTPUT_DIR, f"{algo}_metrics.tex")
        with open(standalone_path, "w") as f:
            f.write(standalone)

        # Table-only .tex (for \input{})
        table_only = generate_table_only(algo, stats[algo])
        table_only_path = os.path.join(OUTPUT_DIR, f"{algo}_metrics_table.tex")
        with open(table_only_path, "w") as f:
            f.write(table_only)

        print(f"[OK] {algo}")
        print(f"     Standalone : {standalone_path}")
        print(f"     Table-only : {table_only_path}")

    # Generate standard consolidated table (all algorithms, selected metrics)
    consolidated_table = generate_consolidated_table(stats, algo_order)
    consolidated_path = os.path.join(OUTPUT_DIR, "consolidated_metrics_table.tex")
    with open(consolidated_path, "w") as f:
        f.write(consolidated_table)
    print(f"\n[OK] Consolidated summary written to: {consolidated_path}")

    # Generate MDP-specific consolidated table (VI vs PI, normalised metrics)
    mdp_consolidated = generate_mdp_consolidated_table(stats)
    mdp_consolidated_path = os.path.join(OUTPUT_DIR, "mdp_planning_metrics_table.tex")
    with open(mdp_consolidated_path, "w") as f:
        f.write(mdp_consolidated)
    print(f"[OK] MDP planning metrics table written to: {mdp_consolidated_path}")

    print(f"\nAll tables written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
