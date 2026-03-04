"""
Pathfinding Algorithm Benchmark  –  Comprehensive Visualisation
================================================================
Generates publication-quality plots from benchmark_results.csv.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
import os
import warnings
from matplotlib.gridspec import GridSpec

warnings.filterwarnings('ignore')

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STYLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

plt.rcParams.update({
    'font.family':        'serif',
    'font.serif':         ['Times New Roman', 'DejaVu Serif'],
    'mathtext.fontset':   'dejavuserif',
    'figure.figsize':     (12, 6),
    'figure.dpi':         150,
    'savefig.dpi':        300,
    'savefig.bbox':       'tight',
    'axes.titlesize':     14,
    'axes.titleweight':   'bold',
    'axes.labelsize':     12,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'legend.fontsize':    10,
    'legend.framealpha':  0.9,
    'xtick.labelsize':    10,
    'ytick.labelsize':    10,
    'grid.alpha':         0.3,
    'grid.linestyle':     '--',
})

OUTPUT = "plots"
os.makedirs(OUTPUT, exist_ok=True)

# Consistent palette & markers
ALGO_COLORS = {
    'DFS':      '#c0392b',
    'BFS':      '#2980b9',
    'AStar_h1': '#27ae60',
    'AStar_h2': '#e67e22',
    'MDP_VI':   '#8e44ad',
    'MDP_PI':   '#16a085',
}
ALGO_ORDER   = ['DFS', 'BFS', 'AStar_h1', 'AStar_h2', 'MDP_VI', 'MDP_PI']
ALGO_LABELS  = {'DFS':'DFS', 'BFS':'BFS', 'AStar_h1':'A* h₁ (Manhattan)',
                'AStar_h2':'A* h₂ (Corridor)', 'MDP_VI':'MDP-VI', 'MDP_PI':'MDP-PI'}
MARKERS      = {'DFS':'o', 'BFS':'s', 'AStar_h1':'D', 'AStar_h2':'^',
                'MDP_VI':'v', 'MDP_PI':'P'}

def _label(a):  return ALGO_LABELS.get(a, a)
def _color(a):  return ALGO_COLORS.get(a, '#333')
def _marker(a): return MARKERS.get(a, 'o')

def _save(fig, name):
    fig.savefig(os.path.join(OUTPUT, name), facecolor='white')
    plt.close(fig)
    print(f"  ✓  {name}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_data(path):
    df = pd.read_csv(path)
    for c in df.columns:
        if c != 'Algorithm':
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  1.  FAILURE REPORT  +  MISSING-RUN ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def report_failures_and_missing(df):
    all_runs = sorted(df['RunID'].dropna().unique().astype(int))
    total_runs = len(all_runs)
    run_range = set(range(int(min(all_runs)), int(max(all_runs)) + 1))

    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║                       FAILURE REPORT                           ║")
    print("╠══════════════════════════════════════════════════════════════════╣")

    # Explicit failures (Success != 1)
    fails = df[df['Success'] != 1]
    if fails.empty:
        print("║  ✅  No explicit failures (Success=0) in dataset.              ║")
    else:
        print(f"║  ⚠  {len(fails)} explicit failure(s):                              ║")
        for _, r in fails.iterrows():
            print(f"║    Run {int(r['RunID']):>3d}  Size={int(r['Size'])}  "
                  f"Paths={int(r['PathCount'])}  Algo={r['Algorithm']}")

    print("╠══════════════════════════════════════════════════════════════════╣")
    print("║               MISSING RUNS (timeouts / skips)                  ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    for algo in ALGO_ORDER:
        present = set(df[df['Algorithm'] == algo]['RunID'].dropna().astype(int))
        missing = sorted(run_range - present)
        n = len(present)
        print(f"║  {_label(algo):25s}  {n:>3d}/{total_runs} runs  ", end="")
        if missing:
            print(f" Missing: {missing}")
        else:
            print(f" (complete) ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  2.  SUBOPTIMAL PATH REPORT  +  BAR CHART
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def report_and_plot_suboptimality(df):
    succ = df[(df['Success'] == 1) & (df['PathOptimalityRatio'].notna())].copy()

    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                  SUBOPTIMAL PATH REPORT                        ║")
    print("╠═══════════════════════════════════════════════════════════════════╣")

    # OptRatio = L_opt / L_path  →  ratio < 1 = suboptimal, ratio > 1 = anomalous
    records = []
    for algo in ALGO_ORDER:
        alg = succ[succ['Algorithm'] == algo]
        total = len(alg)
        suboptimal = alg[alg['PathOptimalityRatio'] < 0.999]  # path longer than optimal
        anomalous  = alg[alg['PathOptimalityRatio'] > 1.001]  # shorter than ground truth(!?)
        optimal_pct = 100 * len(alg[(alg['PathOptimalityRatio'] >= 0.999) &
                                     (alg['PathOptimalityRatio'] <= 1.001)]) / total if total else 0
        records.append({
            'algo': algo, 'total': total,
            'suboptimal': len(suboptimal), 'anomalous': len(anomalous),
            'optimal_pct': optimal_pct,
            'worst': suboptimal['PathOptimalityRatio'].min() if len(suboptimal) else 1.0,
            'mean_sub': suboptimal['PathOptimalityRatio'].mean() if len(suboptimal) else 1.0,
        })

        print(f"║  {_label(algo):25s}  {total:>3d} runs  |  ", end="")
        if len(suboptimal):
            runs = sorted(suboptimal['RunID'].astype(int).tolist())
            print(f"{len(suboptimal):>2d} suboptimal (worst ratio={records[-1]['worst']:.3f})  "
                  f"RunIDs: {runs}")
        else:
            print(f"All optimal ✅")
        if len(anomalous):
            runs_a = sorted(anomalous['RunID'].astype(int).tolist())
            print(f"║  {'':25s}  {'':>3s}       |  "
                  f"{len(anomalous):>2d} anomalous (ratio>1, baseline may be wrong)  RunIDs: {runs_a}")

    print("╚═══════════════════════════════════════════════════════════════════╝\n")

    # ── Bar chart: % optimal vs % suboptimal ──
    fig, ax = plt.subplots(figsize=(10, 6.5))
    x = np.arange(len(records))
    width = 0.55

    optimal_pcts = [r['optimal_pct'] for r in records]
    sub_pcts     = [100 * r['suboptimal'] / r['total'] if r['total'] else 0 for r in records]

    bars_opt = ax.bar(x, optimal_pcts, width, label='Optimal (ratio = 1.0)',
                      color='#27ae60', edgecolor='white')
    bars_sub = ax.bar(x, sub_pcts, width, bottom=optimal_pcts,
                      label='Suboptimal (ratio < 1 \u2014 path longer)',
                      color='#e74c3c', edgecolor='white')

    ax.set_xticks(x)
    ax.set_xticklabels([f"{_label(r['algo'])}\n({r['total']} runs)" for r in records],
                        fontsize=10)
    ax.set_ylabel('Percentage of Runs (%)')
    ax.set_title('Path Optimality Breakdown per Algorithm\n'
                 r'(OptRatio = $L_{opt}/L_{path}$; 1.0 = optimal, <1 = suboptimal)')
    ax.set_ylim(0, 115)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Legend below x-axis labels, outside the plot
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18),
              ncol=2, frameon=True, fontsize=10)

    for i, r in enumerate(records):
        if r['optimal_pct'] > 5:
            ax.text(i, r['optimal_pct'] / 2, f"{r['optimal_pct']:.0f}%",
                    ha='center', va='center', fontweight='bold', fontsize=10, color='white')
        if sub_pcts[i] > 3:
            ax.text(i, optimal_pcts[i] + sub_pcts[i] / 2, f"{r['suboptimal']}",
                    ha='center', va='center', fontweight='bold', fontsize=10, color='white')

    fig.tight_layout()
    _save(fig, 'suboptimality_breakdown.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  3.  TIME COMPLEXITY vs MAZE SIZE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_time_vs_size(df):
    succ = df[df['Success'] == 1].copy()
    fig, ax = plt.subplots(figsize=(12, 7))

    for algo in ALGO_ORDER:
        s = succ[succ['Algorithm'] == algo].groupby('Size')['Time(s)'].agg(['mean','std']).reset_index()
        s.sort_values('Size', inplace=True)
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'], label=_label(algo),
                    color=_color(algo), marker=_marker(algo),
                    capsize=4, linewidth=2.2, markersize=8, markeredgecolor='white',
                    markeredgewidth=0.8)

    ax.set_yscale('log')
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel('Execution Time (s)  [log scale]')
    ax.set_title('Time Complexity vs Maze Size')
    ax.legend(title='Algorithm', frameon=True)
    ax.grid(True, which='both')
    _save(fig, '01_time_complexity.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  4.  SPACE COMPLEXITY (VISITED NODES) vs MAZE SIZE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_nodes_vs_size(df):
    succ = df[df['Success'] == 1].copy()
    fig, ax = plt.subplots(figsize=(12, 7))

    for algo in ALGO_ORDER:
        s = succ[succ['Algorithm'] == algo].groupby('Size')['VisitedNodes'].agg(['mean','std']).reset_index()
        s.sort_values('Size', inplace=True)
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'], label=_label(algo),
                    color=_color(algo), marker=_marker(algo),
                    capsize=4, linewidth=2.2, markersize=8, markeredgecolor='white',
                    markeredgewidth=0.8)

    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel('Visited / Valued Nodes')
    ax.set_title('Search Effort: Nodes Explored vs Maze Size')
    ax.legend(title='Algorithm', frameon=True)
    ax.grid(True)
    _save(fig, '02_space_complexity.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  5.  PATH OPTIMALITY vs SIZE and PATH COUNT  (capped at sensible range)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_optimality(df):
    succ = df[(df['Success'] == 1) & (df['PathOptimalityRatio'].notna())].copy()
    # Clamp: ratio should be in (0, 1] by definition; anything > 1 is an anomaly
    succ = succ[(succ['PathOptimalityRatio'] > 0.0) & (succ['PathOptimalityRatio'] <= 1.5)]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))

    for panel, (group_col, xlabel, title) in enumerate([
        ('Size', 'Maze Size ($N \\times N$)', 'Path Optimality vs Maze Size'),
        ('PathCount', 'Number of Possible Paths', 'Path Optimality vs Path Count'),
    ]):
        ax = axes[panel]
        for algo in ALGO_ORDER:
            s = succ[succ['Algorithm'] == algo].groupby(group_col)['PathOptimalityRatio']\
                    .agg(['mean','std']).reset_index().sort_values(group_col)
            if s.empty: continue
            ax.errorbar(s[group_col], s['mean'], yerr=s['std'], label=_label(algo),
                        color=_color(algo), marker=_marker(algo),
                        capsize=3, linewidth=2, markersize=7,
                        markeredgecolor='white', markeredgewidth=0.6)

        ax.axhline(1.0, color='#555', ls='--', lw=1.2, alpha=0.7, zorder=0)
        ax.text(ax.get_xlim()[1]*0.98, 1.01, 'Optimal', ha='right', va='bottom',
                fontsize=9, color='#555', fontstyle='italic')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(r'Optimality Ratio  $L_{opt}/L_{path}$  (1.0 = optimal, lower = worse)')
        ax.set_title(title)
        ax.set_ylim(top=1.08)
        if panel == 0:
            ax.legend(title='Algorithm', fontsize=9, frameon=True)
        ax.grid(True)

    fig.tight_layout()
    _save(fig, '03_path_optimality.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  6.  SEARCH COVERAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_search_coverage(df):
    succ = df[df['Success'] == 1].copy()
    # Cap coverage at 1.0 for display (MDP values all cells = 1.0 by design)
    succ['SearchCoverageCapped'] = succ['SearchCoverage'].clip(upper=1.0)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))

    # (a) Overall bar
    ax = axes[0]
    means = succ.groupby('Algorithm')['SearchCoverageCapped'].mean().reindex(ALGO_ORDER).dropna()
    bars = ax.bar(range(len(means)), means.values, width=0.6,
                  color=[_color(a) for a in means.index], edgecolor='white', linewidth=1.2)
    for i, (v, algo) in enumerate(zip(means.values, means.index)):
        ax.text(i, v + 0.01, f'{v:.2f}', ha='center', va='bottom',
                fontsize=11, fontweight='bold', color=_color(algo))
    ax.set_xticks(range(len(means)))
    ax.set_xticklabels([_label(a) for a in means.index], fontsize=10, rotation=20, ha='right')
    ax.axhline(1.0, color='#555', ls='--', lw=1, alpha=0.5)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel('Mean Search Coverage\n(fraction of free cells explored)')
    ax.set_title('Overall Search Coverage')
    ax.grid(axis='y')

    # (b) vs maze size
    ax = axes[1]
    for algo in ALGO_ORDER:
        s = succ[succ['Algorithm'] == algo].groupby('Size')['SearchCoverageCapped'].mean().reset_index()
        s.sort_values('Size', inplace=True)
        ax.plot(s['Size'], s['SearchCoverageCapped'], label=_label(algo),
                color=_color(algo), marker=_marker(algo),
                linewidth=2, markersize=7, markeredgecolor='white', markeredgewidth=0.6)
    ax.axhline(1.0, color='#555', ls='--', lw=1, alpha=0.5)
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel('Search Coverage')
    ax.set_title('Search Coverage vs Maze Size')
    ax.legend(title='Algorithm', fontsize=9, frameon=True)
    ax.grid(True)

    fig.tight_layout()
    _save(fig, '04_search_coverage.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  7.  A* HEURISTIC COMPARISON  (h1 = admissible  vs  h2 = non-admissible)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_astar_comparison(df):
    succ = df[(df['Success'] == 1)].copy()
    h1 = succ[succ['Algorithm'] == 'AStar_h1'].set_index('RunID')
    h2 = succ[succ['Algorithm'] == 'AStar_h2'].set_index('RunID')
    common = h1.index.intersection(h2.index)

    fig = plt.figure(figsize=(18, 10))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.35)

    # ── (a) Path length scatter h1 vs h2 ──
    ax = fig.add_subplot(gs[0, 0])
    pl_h1 = h1.loc[common, 'PathLength']
    pl_h2 = h2.loc[common, 'PathLength']
    sizes_c = h1.loc[common, 'Size']
    sc = ax.scatter(pl_h1, pl_h2, c=sizes_c, cmap='viridis', s=40, alpha=0.7,
                    edgecolors='k', linewidth=0.3, zorder=3)
    lim = max(pl_h1.max(), pl_h2.max()) * 1.05
    ax.plot([0, lim], [0, lim], 'k--', alpha=0.3, lw=1, label='$y=x$')
    ax.set_xlabel('A* h₁ Path Length')
    ax.set_ylabel('A* h₂ Path Length')
    ax.set_title('(a)  Path Length: h₁ vs h₂')
    ax.legend(fontsize=9)
    ax.grid(True)
    cbar = fig.colorbar(sc, ax=ax, shrink=0.8)
    cbar.set_label('Maze Size', fontsize=9)

    # Highlight anomalous points where h2 < h1
    anomalous = pl_h2 < pl_h1 * 0.99
    if anomalous.any():
        ax.scatter(pl_h1[anomalous], pl_h2[anomalous], facecolors='none',
                   edgecolors='red', s=100, linewidth=2, label='h₂ < h₁ (anomaly)', zorder=4)
        ax.legend(fontsize=9)

    # ── (b) Visited Nodes scatter ──
    ax = fig.add_subplot(gs[0, 1])
    vn_h1 = h1.loc[common, 'VisitedNodes']
    vn_h2 = h2.loc[common, 'VisitedNodes']
    ax.scatter(vn_h1, vn_h2, c=sizes_c, cmap='viridis', s=40, alpha=0.7,
               edgecolors='k', linewidth=0.3)
    lim2 = max(vn_h1.max(), vn_h2.max()) * 1.05
    ax.plot([0, lim2], [0, lim2], 'k--', alpha=0.3, lw=1)
    ax.set_xlabel('A* h₁ Visited Nodes')
    ax.set_ylabel('A* h₂ Visited Nodes')
    ax.set_title('(b)  Nodes Explored: h₁ vs h₂')
    ax.grid(True)

    # ── (c) Time scatter ──
    ax = fig.add_subplot(gs[0, 2])
    t_h1 = h1.loc[common, 'Time(s)']
    t_h2 = h2.loc[common, 'Time(s)']
    ax.scatter(t_h1, t_h2, c=sizes_c, cmap='viridis', s=40, alpha=0.7,
               edgecolors='k', linewidth=0.3)
    lim3 = max(t_h1.max(), t_h2.max()) * 1.05
    ax.plot([0, lim3], [0, lim3], 'k--', alpha=0.3, lw=1)
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('A* h₁ Time (s)')
    ax.set_ylabel('A* h₂ Time (s)')
    ax.set_title('(c)  Execution Time: h₁ vs h₂')
    ax.grid(True, which='both')

    # ── (d) Optimality distribution (violin) ──
    ax = fig.add_subplot(gs[1, 0])
    violin_data = []
    for algo_name, label, color in [('AStar_h1', 'h₁', _color('AStar_h1')),
                                      ('AStar_h2', 'h₂', _color('AStar_h2'))]:
        sub = succ[(succ['Algorithm'] == algo_name) & (succ['PathOptimalityRatio'].notna())]
        valid = sub['PathOptimalityRatio']
        valid = valid[(valid >= 0.5) & (valid <= 3.0)]  # sane range
        violin_data.append(valid.values)

    parts = ax.violinplot(violin_data, positions=[0, 1], showmeans=True, showmedians=True)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor([_color('AStar_h1'), _color('AStar_h2')][i])
        pc.set_alpha(0.6)
    ax.axhline(1.0, color='#555', ls='--', lw=1, alpha=0.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['A* h₁\n(admissible)', 'A* h₂\n(non-admissible)'])
    ax.set_ylabel('Path Optimality Ratio')
    ax.set_title('(d)  Optimality Distribution')
    ax.grid(axis='y')

    # ── (e) Suboptimality by maze size ──
    ax = fig.add_subplot(gs[1, 1])
    for algo, label in [('AStar_h1', 'h₁'), ('AStar_h2', 'h₂')]:
        sub = succ[(succ['Algorithm'] == algo) & (succ['Suboptimality'].notna())]
        valid = sub[(sub['Suboptimality'] >= -0.5) & (sub['Suboptimality'] <= 2.0)]
        s = valid.groupby('Size')['Suboptimality'].agg(['mean','std']).reset_index().sort_values('Size')
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'], label=f'A* {label}',
                    color=_color(f'AStar_{label.replace("₁","h1").replace("₂","h2")}' if label in ('h₁','h₂') else algo),
                    marker=_marker(algo), capsize=3, linewidth=2, markersize=7)
    ax.axhline(0.0, color='#555', ls='--', lw=1, alpha=0.5)
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel('Suboptimality\n(0 = optimal, >0 = longer)')
    ax.set_title('(e)  Suboptimality vs Maze Size')
    ax.legend(frameon=True)
    ax.grid(True)

    # ── (f) Wrong path occurrences ──
    ax = fig.add_subplot(gs[1, 2])
    # h2 found suboptimal (ratio > 1) or anomalously short (ratio < 1)
    h2_runs = succ[succ['Algorithm'] == 'AStar_h2'].copy()
    h2_runs['status'] = 'Optimal'
    h2_runs.loc[h2_runs['PathOptimalityRatio'] > 1.001, 'status'] = 'Suboptimal\n(longer than h₁)'
    h2_runs.loc[h2_runs['PathOptimalityRatio'] < 0.999, 'status'] = 'Anomalous\n(shorter than h₁)'
    counts = h2_runs.groupby(['Size', 'status']).size().unstack(fill_value=0)
    cols_order = [c for c in ['Optimal', 'Suboptimal\n(longer than h₁)', 'Anomalous\n(shorter than h₁)'] if c in counts.columns]
    color_map = {'Optimal': '#27ae60', 'Suboptimal\n(longer than h₁)': '#e74c3c',
                 'Anomalous\n(shorter than h₁)': '#f39c12'}
    counts[cols_order].plot(kind='bar', stacked=True, ax=ax,
                            color=[color_map.get(c, '#999') for c in cols_order],
                            edgecolor='white', width=0.7)
    ax.set_xlabel('Maze Size')
    ax.set_ylabel('Number of Runs')
    ax.set_title('(f)  A* h₂ Path Quality by Size')
    ax.legend(fontsize=8, frameon=True)
    ax.grid(axis='y')
    ax.tick_params(axis='x', rotation=0)

    fig.suptitle('A* Heuristic Comparison  —  h₁ (admissible) vs h₂ (non-admissible)',
                 fontsize=15, fontweight='bold', y=1.01)
    _save(fig, '05_astar_comparison.png')

    # Print specific wrong-path runs
    wrong = succ[(succ['Algorithm'] == 'AStar_h2') &
                 ((succ['PathOptimalityRatio'] > 1.001) | (succ['PathOptimalityRatio'] < 0.999))]
    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║          A* h₂  NON-OPTIMAL PATH RUNS                         ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    if wrong.empty:
        print("║  ✅  h₂ matched optimal on every successful run.              ║")
    else:
        above = wrong[wrong['PathOptimalityRatio'] > 1.001]
        below = wrong[wrong['PathOptimalityRatio'] < 0.999]
        if len(above):
            print(f"║  Suboptimal (h₂ path LONGER than h₁ optimal):              ║")
            for _, r in above.iterrows():
                print(f"║    Run {int(r['RunID']):>3d}  Size={int(r['Size'])}  "
                      f"h₂={int(r['PathLength'])}  optimal={int(r['AStarH1PathLength']) if pd.notna(r['AStarH1PathLength']) else '?'}  "
                      f"ratio={r['PathOptimalityRatio']:.4f}")
        if len(below):
            print(f"║  Anomalous (h₂ path SHORTER than h₁ — ground truth issue): ║")
            for _, r in below.iterrows():
                print(f"║    Run {int(r['RunID']):>3d}  Size={int(r['Size'])}  "
                      f"h₂={int(r['PathLength'])}  h₁_ref={int(r['AStarH1PathLength']) if pd.notna(r['AStarH1PathLength']) else '?'}  "
                      f"ratio={r['PathOptimalityRatio']:.4f}")
    print("╚══════════════════════════════════════════════════════════════════╝\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  8.  MDP-SPECIFIC ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_mdp_analysis(df):
    mdp = df[(df['Success'] == 1) & (df['Algorithm'].isin(['MDP_VI', 'MDP_PI']))].copy()
    mdp = mdp.dropna(subset=['PlanningIters', 'CumulativeReward', 'DiscountedReturn'])
    if mdp.empty:
        print("  ⚠  No MDP data – skipping.")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # (a) Planning Iterations
    ax = axes[0, 0]
    for algo in ['MDP_VI', 'MDP_PI']:
        s = mdp[mdp['Algorithm'] == algo].groupby('Size')['PlanningIters'].agg(['mean','std']).reset_index().sort_values('Size')
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'], label=_label(algo),
                    color=_color(algo), marker=_marker(algo), capsize=3, linewidth=2, markersize=7)
    ax.set_xlabel('Maze Size'); ax.set_ylabel('Planning Iterations')
    ax.set_title('(a)  Planning Iterations vs Maze Size')
    ax.legend(frameon=True); ax.grid(True)

    # (b) Planning Time
    ax = axes[0, 1]
    for algo in ['MDP_VI', 'MDP_PI']:
        s = mdp[mdp['Algorithm'] == algo].groupby('Size')['PlanningTime(s)'].agg(['mean','std']).reset_index().sort_values('Size')
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'], label=_label(algo),
                    color=_color(algo), marker=_marker(algo), capsize=3, linewidth=2, markersize=7)
    ax.set_yscale('log')
    ax.set_xlabel('Maze Size'); ax.set_ylabel('Planning Time (s)  [log]')
    ax.set_title('(b)  Planning Time vs Maze Size')
    ax.legend(frameon=True); ax.grid(True, which='both')

    # (c) Cumulative Reward vs Path Length
    ax = axes[1, 0]
    for algo in ['MDP_VI', 'MDP_PI']:
        sub = mdp[mdp['Algorithm'] == algo]
        ax.scatter(sub['PathLength'], sub['CumulativeReward'], label=_label(algo),
                   color=_color(algo), alpha=0.5, s=35, edgecolors='k', linewidth=0.3)
    ax.set_xlabel('Path Length'); ax.set_ylabel('Cumulative Reward')
    ax.set_title('(c)  Cumulative Reward vs Path Length')
    ax.legend(frameon=True); ax.grid(True)

    # (d) Discounted Return vs Size
    ax = axes[1, 1]
    for algo in ['MDP_VI', 'MDP_PI']:
        s = mdp[mdp['Algorithm'] == algo].groupby('Size')['DiscountedReturn'].agg(['mean','std']).reset_index().sort_values('Size')
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'], label=_label(algo),
                    color=_color(algo), marker=_marker(algo), capsize=3, linewidth=2, markersize=7)
    ax.set_xlabel('Maze Size'); ax.set_ylabel('Mean Discounted Return')
    ax.set_title('(d)  Discounted Return vs Maze Size')
    ax.legend(frameon=True); ax.grid(True)

    fig.suptitle('MDP-Specific Analysis  (Value Iteration vs Policy Iteration)',
                 fontsize=14, fontweight='bold', y=1.01)
    fig.tight_layout()
    _save(fig, '06_mdp_analysis.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  9.  SEARCH EFFICIENCY RATIO  &  TIME PER NODE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_efficiency_metrics(df):
    succ = df[df['Success'] == 1].copy()
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))

    # (a) Search Efficiency Ratio — MDPs excluded: they always visit every cell
    #     by design (coverage = 1.0), so their ratio is trivially low and
    #     tells us nothing about directed search quality.
    ax = axes[0]
    SEARCH_ALGOS = [a for a in ALGO_ORDER if not a.startswith('MDP')]
    for algo in SEARCH_ALGOS:
        s = succ[succ['Algorithm'] == algo].groupby('Size')['SearchEffRatio'].mean().reset_index().sort_values('Size')
        if s.empty: continue
        ax.plot(s['Size'], s['SearchEffRatio'], label=_label(algo),
                color=_color(algo), marker=_marker(algo), linewidth=2, markersize=7,
                markeredgecolor='white', markeredgewidth=0.6)
    ax.axhline(1.0, color='#555', ls='--', lw=1, alpha=0.5)
    ax.set_xlabel('Maze Size ($N \\times N$)'); ax.set_ylabel('Search Efficiency Ratio\n(PathLen / Visited;  1.0 = no waste)')
    ax.set_title('Search Efficiency vs Maze Size\n(MDPs excluded — full-space exploration by design)')
    ax.legend(title='Algorithm', fontsize=9, frameon=True); ax.grid(True)

    # (b) Time Per Node
    ax = axes[1]
    for algo in ALGO_ORDER:
        s = succ[succ['Algorithm'] == algo].groupby('Size')['TimePerNode'].mean().reset_index().sort_values('Size')
        if s.empty: continue
        ax.plot(s['Size'], s['TimePerNode'], label=_label(algo),
                color=_color(algo), marker=_marker(algo), linewidth=2, markersize=7,
                markeredgecolor='white', markeredgewidth=0.6)
    ax.set_yscale('log')
    ax.set_xlabel('Maze Size ($N \\times N$)'); ax.set_ylabel('Time per Node (s)  [log]')
    ax.set_title('Per-Node Overhead vs Maze Size')
    ax.legend(title='Algorithm', fontsize=9, frameon=True); ax.grid(True, which='both')

    fig.tight_layout()
    _save(fig, '07_efficiency_metrics.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  10.  RANKING HEATMAP  (who wins at each size?)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_ranking_heatmap(df):
    succ = df[df['Success'] == 1].copy()
    pivot = succ.groupby(['Size', 'Algorithm'])['Time(s)'].median().reset_index()
    mat   = pivot.pivot(index='Algorithm', columns='Size', values='Time(s)')
    ranked = mat.rank(axis=0, method='min')
    ranked = ranked.reindex(ALGO_ORDER).rename(index=ALGO_LABELS)

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(ranked, annot=True, fmt='.0f', cmap='RdYlGn_r', linewidths=1.5,
                linecolor='white', ax=ax, cbar_kws={'label': 'Rank (1 = fastest)'},
                annot_kws={'fontsize': 12, 'fontweight': 'bold'})
    ax.set_title('Speed Ranking by Maze Size  (1 = fastest median time)')
    ax.set_ylabel(''); ax.set_xlabel('Maze Size ($N \\times N$)')
    fig.tight_layout()
    _save(fig, '08_ranking_heatmap.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  11.  SCALABILITY  (log-log time vs free cells)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_scalability(df):
    succ = df[df['Success'] == 1].copy()
    fig, ax = plt.subplots(figsize=(12, 7))

    for algo in ALGO_ORDER:
        s = succ[succ['Algorithm'] == algo].groupby('FreeCells')['Time(s)'].median().reset_index().sort_values('FreeCells')
        if s.empty: continue
        ax.plot(s['FreeCells'], s['Time(s)'], label=_label(algo),
                color=_color(algo), marker=_marker(algo), linewidth=2, markersize=7,
                markeredgecolor='white', markeredgewidth=0.6, alpha=0.85)

    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('Free Cells  (log scale)  —  effective problem size')
    ax.set_ylabel('Median Execution Time (s)  [log]')
    ax.set_title('Scalability: Time vs Problem Size')
    ax.legend(title='Algorithm', frameon=True); ax.grid(True, which='both')
    fig.tight_layout()
    _save(fig, '09_scalability.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  12.  TURN COUNT  &  PATH LENGTH comparison
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_path_characteristics(df):
    succ = df[df['Success'] == 1].copy()
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))

    for panel, (col, ylabel, title) in enumerate([
        ('PathLength',  'Mean Path Length',  'Path Length vs Maze Size'),
        ('TurnCount',   'Mean Turn Count',   'Turn Count vs Maze Size'),
    ]):
        ax = axes[panel]
        for algo in ALGO_ORDER:
            s = succ[succ['Algorithm'] == algo].groupby('Size')[col].mean().reset_index().sort_values('Size')
            if s.empty: continue
            ax.plot(s['Size'], s[col], label=_label(algo),
                    color=_color(algo), marker=_marker(algo), linewidth=2, markersize=7,
                    markeredgecolor='white', markeredgewidth=0.6)
        ax.set_xlabel('Maze Size ($N \\times N$)'); ax.set_ylabel(ylabel)
        ax.set_title(title)
        if panel == 0:
            ax.legend(title='Algorithm', fontsize=9, frameon=True)
        ax.grid(True)

    fig.tight_layout()
    _save(fig, '10_path_characteristics.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  13.  COMPLETION RATE  (how many runs each algo actually finished)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_completion_rate(df):
    all_runs = sorted(df['RunID'].dropna().unique().astype(int))
    total = len(all_runs)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # (a) Overall bar
    ax = axes[0]
    rates = {}
    for algo in ALGO_ORDER:
        n = len(df[(df['Algorithm'] == algo) & (df['Success'] == 1)])
        rates[algo] = 100 * n / total
    bars = ax.bar(range(len(ALGO_ORDER)), [rates[a] for a in ALGO_ORDER], width=0.6,
                  color=[_color(a) for a in ALGO_ORDER], edgecolor='white')
    for i, algo in enumerate(ALGO_ORDER):
        n = len(df[(df['Algorithm'] == algo) & (df['Success'] == 1)])
        ax.text(i, rates[algo] + 1, f'{n}/{total}', ha='center', va='bottom',
                fontsize=10, fontweight='bold')
    ax.set_xticks(range(len(ALGO_ORDER)))
    ax.set_xticklabels([_label(a) for a in ALGO_ORDER], rotation=20, ha='right')
    ax.set_ylabel('Completion Rate (%)'); ax.set_ylim(0, 115)
    ax.set_title('Overall Completion Rate')
    ax.grid(axis='y')

    # (b) By maze size
    ax = axes[1]
    sizes = sorted(df['Size'].dropna().unique().astype(int))
    for algo in ALGO_ORDER:
        pcts = []
        for sz in sizes:
            total_sz = len(df[(df['Size'] == sz)]['RunID'].unique())
            done = len(df[(df['Algorithm'] == algo) & (df['Size'] == sz) & (df['Success'] == 1)])
            pcts.append(100 * done / total_sz if total_sz else 0)
        ax.plot(sizes, pcts, label=_label(algo), color=_color(algo),
                marker=_marker(algo), linewidth=2, markersize=7,
                markeredgecolor='white', markeredgewidth=0.6)
    ax.set_xlabel('Maze Size ($N \\times N$)'); ax.set_ylabel('Completion Rate (%)')
    ax.set_title('Completion Rate vs Maze Size')
    ax.set_ylim(0, 110)
    ax.legend(title='Algorithm', fontsize=9, frameon=True); ax.grid(True)

    fig.tight_layout()
    _save(fig, '11_completion_rate.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NEW  A.  SEARCH EFFICIENCY DEEP-DIVE
#  Coverage = N_visited / N_free
#  Efficiency Ratio = L_path / N_visited (higher = less wasted work)
#  Time per Node = T_total / N_visited
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_search_efficiency_deep(df):
    """
    Three-metric deep-dive:
      (a) Coverage  = N_visited / N_free   [violin per algo]
      (b) Efficiency Ratio = L_path / N_visited  [line vs maze size]
      (c) Time per Node = T_total / N_visited   [box plot per algo, log]
    """
    succ = df[df['Success'] == 1].copy()
    succ['SearchCoverageCapped'] = succ['SearchCoverage'].clip(upper=1.0)

    fig = plt.figure(figsize=(18, 6))
    gs  = GridSpec(1, 3, figure=fig, wspace=0.38)

    # ── (a) Coverage violin per algorithm ──────────────────────────────
    ax = fig.add_subplot(gs[0])
    data_cov  = [succ[succ['Algorithm'] == a]['SearchCoverageCapped'].dropna().values
                 for a in ALGO_ORDER]
    parts = ax.violinplot(data_cov, positions=range(len(ALGO_ORDER)),
                          showmeans=True, showmedians=True, widths=0.7)
    for i, (pc, algo) in enumerate(zip(parts['bodies'], ALGO_ORDER)):
        pc.set_facecolor(_color(algo))
        pc.set_alpha(0.55)
        pc.set_edgecolor('white')
    for k in ('cmeans', 'cmedians', 'cbars', 'cmaxes', 'cmins'):
        if k in parts:
            parts[k].set_color('#333')
            parts[k].set_linewidth(1.2)
    ax.axhline(1.0, color='#555', ls='--', lw=1, alpha=0.5,
               label='Full coverage')
    ax.set_xticks(range(len(ALGO_ORDER)))
    ax.set_xticklabels([_label(a) for a in ALGO_ORDER],
                       rotation=22, ha='right', fontsize=9)
    ax.set_ylabel(r'$\frac{N_{\mathrm{visited}}}{N_{\mathrm{free}}}$  (Search Coverage)',
                  fontsize=11)
    ax.set_title('(a)  Search Coverage Distribution')
    ax.set_ylim(-0.05, 1.15)
    ax.grid(axis='y')
    ax.legend(fontsize=9)

    # ── (b) Efficiency Ratio vs maze size ──────────────────────────────
    ax = fig.add_subplot(gs[1])
    for algo in ALGO_ORDER:
        s = (succ[succ['Algorithm'] == algo]
             .groupby('Size')['SearchEffRatio']
             .agg(['mean', 'std'])
             .reset_index()
             .sort_values('Size'))
        if s.empty:
            continue
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'],
                    label=_label(algo),
                    color=_color(algo), marker=_marker(algo),
                    capsize=3, linewidth=2, markersize=7,
                    markeredgecolor='white', markeredgewidth=0.7)
    ax.axhline(1.0, color='#555', ls='--', lw=1, alpha=0.5,
               label='$L_{path}=N_{visited}$')
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel(r'$\frac{L_{\mathrm{path}}}{N_{\mathrm{visited}}}$  (Efficiency Ratio)',
                  fontsize=11)
    ax.set_title('(b)  Efficiency Ratio vs Maze Size')
    ax.legend(fontsize=8, frameon=True, loc='upper right')
    ax.grid(True)
    ax.set_ylim(bottom=0)

    # ── (c) Time per Node — box plot, log scale ─────────────────────────
    ax = fig.add_subplot(gs[2])
    data_tpn = []
    labels_tpn = []
    colors_tpn = []
    for algo in ALGO_ORDER:
        vals = (succ[succ['Algorithm'] == algo]['TimePerNode']
                .dropna()
                .replace([np.inf, -np.inf], np.nan)
                .dropna())
        if vals.empty:
            continue
        data_tpn.append(vals.values)
        labels_tpn.append(_label(algo))
        colors_tpn.append(_color(algo))

    bp = ax.boxplot(data_tpn, patch_artist=True, widths=0.55,
                    medianprops={'color': 'white', 'linewidth': 2},
                    whiskerprops={'linewidth': 1.2},
                    capprops={'linewidth': 1.2},
                    flierprops={'marker': 'o', 'markersize': 3,
                                'alpha': 0.4, 'linestyle': 'none'})
    for patch, color in zip(bp['boxes'], colors_tpn):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_yscale('log')
    ax.set_xticks(range(1, len(labels_tpn) + 1))
    ax.set_xticklabels(labels_tpn, rotation=22, ha='right', fontsize=9)
    ax.set_ylabel(r'$\frac{T_{\mathrm{total}}}{N_{\mathrm{visited}}}$  (Time / Node, s)  [log]',
                  fontsize=11)
    ax.set_title('(c)  Per-Node Overhead Distribution')
    ax.grid(axis='y', which='both')

    fig.suptitle('Search Efficiency Metrics  —  Coverage · Efficiency Ratio · Time per Node',
                 fontsize=13, fontweight='bold', y=1.01)
    fig.tight_layout()
    _save(fig, '12_search_efficiency_deep.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NEW  B.  PATH QUALITY DEEP-DIVE
#  Optimality Ratio  =  L_path / L_opt
#  Suboptimality     =  (L_path - L_opt) / L_opt
#  Turn Count        =  N_turns
#  Path Cost         =  L_path  (= total edge weight on unweighted grid)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_path_quality_deep(df):
    """
    Four-panel path quality breakdown:
      (a) Optimality Ratio — KDE / strip plot per algorithm
      (b) Suboptimality magnitude vs maze size (only suboptimal runs)
      (c) Turn Count vs maze size
      (d) Path Cost (= path length on unweighted grid) vs maze size
    """
    succ = df[df['Success'] == 1].copy()
    succ_opt = succ[succ['PathOptimalityRatio'].notna()].copy()
    # Clamp sane range for display (ground-truth h1 failures on huge mazes skew ratio)
    succ_opt = succ_opt[
        (succ_opt['PathOptimalityRatio'] >= 0.7) &
        (succ_opt['PathOptimalityRatio'] <= 6.0)
    ]
    subopt = succ_opt[succ_opt['Suboptimality'].notna() &
                      (succ_opt['Suboptimality'] > 0.001)]  # only truly suboptimal

    fig = plt.figure(figsize=(20, 10))
    gs  = GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.38)

    # ── (a) Optimality Ratio KDE strip, one row per algorithm ──────────
    ax = fig.add_subplot(gs[0, 0])
    offsets = {a: i for i, a in enumerate(reversed(ALGO_ORDER))}
    for algo in ALGO_ORDER:
        vals = succ_opt[succ_opt['Algorithm'] == algo]['PathOptimalityRatio'].values
        if len(vals) == 0:
            continue
        y = offsets[algo]
        # jitter strip
        jitter = np.random.uniform(-0.25, 0.25, size=len(vals))
        ax.scatter(vals, y + jitter, color=_color(algo), alpha=0.35, s=12,
                   edgecolors='none', zorder=2)
        # mean marker
        ax.scatter([np.mean(vals)], [y], color=_color(algo), s=90,
                   edgecolors='white', linewidths=1.2, zorder=4,
                   marker=_marker(algo))
    ax.axvline(1.0, color='#555', ls='--', lw=1.2, alpha=0.7, label='Optimal')
    ax.set_yticks(list(offsets.values()))
    ax.set_yticklabels([_label(a) for a in reversed(ALGO_ORDER)], fontsize=10)
    ax.set_xlabel(r'Optimality Ratio  $\frac{L_{\mathrm{path}}}{L_{\mathrm{opt}}}$')
    ax.set_title('(a)  Optimality Ratio Distribution')
    ax.legend(fontsize=9)
    ax.grid(axis='x', which='both')
    ax.set_xlim(left=0.85)

    # ── (b) Suboptimality magnitude vs maze size ───────────────────────
    ax = fig.add_subplot(gs[0, 1])
    any_data = False
    for algo in ALGO_ORDER:
        s = (subopt[subopt['Algorithm'] == algo]
             .groupby('Size')['Suboptimality']
             .agg(['mean', 'std', 'count'])
             .reset_index()
             .sort_values('Size'))
        s = s[s['count'] >= 1]
        if s.empty:
            continue
        any_data = True
        ax.errorbar(s['Size'], s['mean'] * 100, yerr=s['std'] * 100,
                    label=_label(algo), color=_color(algo), marker=_marker(algo),
                    capsize=3, linewidth=2, markersize=7,
                    markeredgecolor='white', markeredgewidth=0.7)
    ax.axhline(0, color='#555', ls='--', lw=1, alpha=0.5)
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel(r'Mean Suboptimality  $\frac{L_{path}-L_{opt}}{L_{opt}}\times 100\%$')
    ax.set_title('(b)  Suboptimality Magnitude vs Maze Size\n(suboptimal runs only)')
    if any_data:
        ax.legend(fontsize=9, frameon=True)
    ax.grid(True)
    ax.set_ylim(bottom=0)

    # ── (c) Turn Count vs maze size ─────────────────────────────────────
    ax = fig.add_subplot(gs[1, 0])
    for algo in ALGO_ORDER:
        s = (succ[succ['Algorithm'] == algo]
             .groupby('Size')['TurnCount']
             .agg(['mean', 'std'])
             .reset_index()
             .sort_values('Size'))
        if s.empty:
            continue
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'],
                    label=_label(algo), color=_color(algo), marker=_marker(algo),
                    capsize=3, linewidth=2, markersize=7,
                    markeredgecolor='white', markeredgewidth=0.7)
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel(r'Mean Turn Count  $N_{\mathrm{turns}}$')
    ax.set_title('(c)  Turn Count vs Maze Size')
    ax.legend(fontsize=9, frameon=True)
    ax.grid(True)

    # ── (d) Path Cost (= path length) vs maze size ─────────────────────
    ax = fig.add_subplot(gs[1, 1])
    for algo in ALGO_ORDER:
        s = (succ[succ['Algorithm'] == algo]
             .groupby('Size')['PathLength']
             .agg(['mean', 'std'])
             .reset_index()
             .sort_values('Size'))
        if s.empty:
            continue
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'],
                    label=_label(algo), color=_color(algo), marker=_marker(algo),
                    capsize=3, linewidth=2, markersize=7,
                    markeredgecolor='white', markeredgewidth=0.7)
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel(r'Mean Path Cost  $\sum_{e \in path} w(e)$  (unit graph)')
    ax.set_title('(d)  Path Cost vs Maze Size')
    ax.legend(fontsize=9, frameon=True)
    ax.grid(True)

    fig.suptitle('Path Quality Metrics  —  Optimality · Suboptimality · Turns · Cost',
                 fontsize=13, fontweight='bold', y=1.01)
    _save(fig, '13_path_quality_deep.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NEW  C.  SUCCESS RATE + COVERAGE vs PATH-COUNT
#  Success Rate = P_success per algorithm / maze-size bin
#  Also shows how coverage and suboptimality shift as path_count rises
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_success_and_coverage_by_paths(df):
    """
    Three panels:
      (a) Success Rate heatmap — algo × maze size
      (b) Search Coverage vs PathCount (how open mazes affect exploration)
      (c) Suboptimality vs PathCount (more paths → more suboptimal?)
    """
    sizes = sorted(df['Size'].dropna().unique().astype(int))

    fig = plt.figure(figsize=(20, 7))
    gs  = GridSpec(1, 3, figure=fig, wspace=0.42)

    # ── (a) Success rate heatmap ─────────────────────────────────────────
    ax = fig.add_subplot(gs[0])
    mat = np.zeros((len(ALGO_ORDER), len(sizes)))
    for i, algo in enumerate(ALGO_ORDER):
        for j, sz in enumerate(sizes):
            total = len(df[(df['Size'] == sz)]['RunID'].unique())
            done  = len(df[(df['Algorithm'] == algo) &
                           (df['Size'] == sz) &
                           (df['Success'] == 1)])
            mat[i, j] = (100 * done / total) if total else 0

    im = ax.imshow(mat, cmap='RdYlGn', vmin=0, vmax=100,
                   aspect='auto', interpolation='nearest')
    for i in range(len(ALGO_ORDER)):
        for j in range(len(sizes)):
            ax.text(j, i, f'{mat[i, j]:.0f}%',
                    ha='center', va='center',
                    fontsize=10, fontweight='bold',
                    color='white' if mat[i, j] < 50 else '#222')
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([str(s) for s in sizes])
    ax.set_yticks(range(len(ALGO_ORDER)))
    ax.set_yticklabels([_label(a) for a in ALGO_ORDER], fontsize=10)
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_title(r'(a)  Success Rate  $P_{\mathrm{success}}$  (%)'
                 '\nby Algorithm and Maze Size')
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Success Rate (%)', fontsize=9)

    # ── (b) Coverage vs PathCount ──────────────────────────────────────
    ax = fig.add_subplot(gs[1])
    succ = df[df['Success'] == 1].copy()
    succ['SearchCoverageCapped'] = succ['SearchCoverage'].clip(upper=1.0)
    for algo in ALGO_ORDER:
        s = (succ[succ['Algorithm'] == algo]
             .groupby('PathCount')['SearchCoverageCapped']
             .mean()
             .reset_index()
             .sort_values('PathCount'))
        if s.empty:
            continue
        ax.plot(s['PathCount'], s['SearchCoverageCapped'],
                label=_label(algo), color=_color(algo), marker=_marker(algo),
                linewidth=2, markersize=7,
                markeredgecolor='white', markeredgewidth=0.7)
    ax.axhline(1.0, color='#555', ls='--', lw=1, alpha=0.5)
    ax.set_xlabel('Number of Available Paths')
    ax.set_ylabel(r'Search Coverage  $N_{visited}/N_{free}$')
    ax.set_title('(b)  Search Coverage vs Path Count\n(does more structure change exploration?)')
    ax.legend(fontsize=8, frameon=True)
    ax.grid(True)
    ax.set_ylim(-0.05, 1.15)

    # ── (c) Suboptimality vs PathCount ─────────────────────────────────
    ax = fig.add_subplot(gs[2])
    succ_opt = succ[succ['PathOptimalityRatio'].notna() &
                    (succ['PathOptimalityRatio'].between(0.7, 6.0))].copy()
    for algo in ALGO_ORDER:
        s = (succ_opt[succ_opt['Algorithm'] == algo]
             .groupby('PathCount')['PathOptimalityRatio']
             .agg(['mean', 'std'])
             .reset_index()
             .sort_values('PathCount'))
        if s.empty:
            continue
        ax.errorbar(s['PathCount'], s['mean'], yerr=s['std'],
                    label=_label(algo), color=_color(algo), marker=_marker(algo),
                    capsize=3, linewidth=2, markersize=7,
                    markeredgecolor='white', markeredgewidth=0.7)
    ax.axhline(1.0, color='#555', ls='--', lw=1.2, alpha=0.7, label='Optimal')
    ax.set_xlabel('Number of Available Paths')
    ax.set_ylabel(r'Optimality Ratio  $L_{path}/L_{opt}$')
    ax.set_title('(c)  Path Optimality vs Path Count\n(more routes → more h₂/DFS suboptimality?)')
    ax.legend(fontsize=8, frameon=True)
    ax.grid(True)

    fig.suptitle('Success Rate  ·  Coverage  ·  Suboptimality  vs  Maze Open-ness',
                 fontsize=13, fontweight='bold', y=1.01)
    _save(fig, '14_success_and_coverage_by_paths.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  NEW  D.  MEMORY & ROBUSTNESS
#  Peak Frontier = max |F|  (queue / stack / sweep depth)
#  Peak Memory   = max(M_bytes)  via tracemalloc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def plot_memory_metrics(df):
    """
    Two panels:
      (a) Peak Frontier (max |F|) vs maze size — line + error bands
      (b) Peak Memory (KB)        vs maze size — line + error bands
    Both on log-y scale so DFS stack vs BFS queue vs MDP sweep are all visible.
    """
    succ = df[df['Success'] == 1].copy()
    for col in ('PeakFrontier', 'PeakMemory(bytes)'):
        succ[col] = pd.to_numeric(succ[col], errors='coerce')
    succ_pf = succ.dropna(subset=['PeakFrontier'])
    succ_pm = succ.dropna(subset=['PeakMemory(bytes)'])

    if succ_pf.empty and succ_pm.empty:
        print("  ⚠  No PeakFrontier / PeakMemory data (old CSV — re-run benchmark).")
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # ── (a) Peak Frontier ──
    ax = axes[0]
    for algo in ALGO_ORDER:
        s = (succ_pf[succ_pf['Algorithm'] == algo]
             .groupby('Size')['PeakFrontier']
             .agg(['mean', 'std'])
             .reset_index()
             .sort_values('Size'))
        if s.empty:
            continue
        ax.errorbar(s['Size'], s['mean'], yerr=s['std'],
                    label=_label(algo), color=_color(algo), marker=_marker(algo),
                    capsize=3, linewidth=2, markersize=7,
                    markeredgecolor='white', markeredgewidth=0.7)
    ax.set_yscale('log')
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel(r'Peak Frontier  $\max|F|$  (nodes)  [log]')
    ax.set_title('(a)  Peak Frontier Size vs Maze Size\n'
                 '(BFS queue · DFS stack · A* open-heap · MDP state set)')
    ax.legend(title='Algorithm', fontsize=9, frameon=True)
    ax.grid(True, which='both')

    # ── (b) Peak Memory ──
    ax = axes[1]
    for algo in ALGO_ORDER:
        s = (succ_pm[succ_pm['Algorithm'] == algo]
             .groupby('Size')['PeakMemory(bytes)']
             .agg(['mean', 'std'])
             .reset_index()
             .sort_values('Size'))
        if s.empty:
            continue
        # Convert to KB for readability
        ax.errorbar(s['Size'], s['mean'] / 1024, yerr=s['std'] / 1024,
                    label=_label(algo), color=_color(algo), marker=_marker(algo),
                    capsize=3, linewidth=2, markersize=7,
                    markeredgecolor='white', markeredgewidth=0.7)
    ax.set_yscale('log')
    ax.set_xlabel('Maze Size ($N \\times N$)')
    ax.set_ylabel(r'Peak Memory  $\max(M)$  (KB, log)')
    ax.set_title('(b)  Peak Memory Usage vs Maze Size\n'
                 '(measured by tracemalloc during algorithm execution)')
    ax.legend(title='Algorithm', fontsize=9, frameon=True)
    ax.grid(True, which='both')

    fig.suptitle('Memory \u0026 Robustness  —  Peak Frontier  ·  Peak Memory',
                 fontsize=13, fontweight='bold', y=1.01)
    fig.tight_layout()
    _save(fig, '15_memory_metrics.png')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  15.  SUMMARY STATS TABLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def print_summary(df):
    all_runs = sorted(df['RunID'].dropna().unique().astype(int))
    total = len(all_runs)
    succ = df[df['Success'] == 1].copy()

    print("\n╔══════════════════════════════════════════════════════════════════╗")
    print("║                     SUMMARY STATISTICS                         ║")
    print("╠══════════════════════════════════════════════════════════════════╣")
    for algo in ALGO_ORDER:
        sub = succ[succ['Algorithm'] == algo]
        n = len(sub)
        print(f"║                                                                ║")
        print(f"║  {_label(algo):25s}   {n}/{total} runs completed              ║")
        print(f"║    Time(s)   : mean={sub['Time(s)'].mean():>10.4f}  "
              f"median={sub['Time(s)'].median():>10.4f}  max={sub['Time(s)'].max():>10.2f}")
        print(f"║    Visited   : mean={sub['VisitedNodes'].mean():>8.0f}  "
              f"median={sub['VisitedNodes'].median():>8.0f}  max={sub['VisitedNodes'].max():>8.0f}")
        opt = sub['PathOptimalityRatio'].dropna()
        if not opt.empty:
            pct_opt = 100*(opt.between(0.999, 1.001)).mean()
            print(f"║    Optimality: mean={opt.mean():>6.4f}  worst={opt.max():>6.4f}  "
                  f"% optimal={pct_opt:.1f}%")
    print("╚══════════════════════════════════════════════════════════════════╝\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_results.csv")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    print(f"Loading {csv_path} …")
    df = load_data(csv_path)
    total_runs = len(df['RunID'].dropna().unique())
    sizes_all  = sorted(df['Size'].dropna().unique().astype(int))
    print(f"  → {len(df)} rows  |  {total_runs} unique mazes  |  "
          f"sizes {sizes_all}  |  {df['Algorithm'].nunique()} algorithms")

    # ── Size filter: only use mazes ≤ 50×50 for all statistics & plots ──
    MAX_SIZE = 50
    df       = df[df['Size'] <= MAX_SIZE].copy()
    sizes    = sorted(df['Size'].dropna().unique().astype(int))
    dropped  = total_runs - len(df['RunID'].dropna().unique())
    print(f"  ↳ Filtered to size ≤ {MAX_SIZE}: {len(df)} rows  |  "
          f"sizes {sizes}  |  {dropped} maze(s) excluded\n")

    # ── Text reports ──
    report_failures_and_missing(df)
    report_and_plot_suboptimality(df)

    # ── Plots ──
    print("Generating plots …\n")
    plot_time_vs_size(df)
    plot_nodes_vs_size(df)
    plot_optimality(df)
    plot_search_coverage(df)
    plot_astar_comparison(df)
    plot_mdp_analysis(df)
    plot_efficiency_metrics(df)
    plot_ranking_heatmap(df)
    plot_scalability(df)
    plot_path_characteristics(df)
    plot_completion_rate(df)
    # ── New metrics panels ──
    plot_search_efficiency_deep(df)
    plot_path_quality_deep(df)
    plot_success_and_coverage_by_paths(df)
    plot_memory_metrics(df)

    # ── Summary ──
    print_summary(df)
    print(f"✅  All plots saved to '{OUTPUT}/' directory.\n")


if __name__ == "__main__":
    main()
