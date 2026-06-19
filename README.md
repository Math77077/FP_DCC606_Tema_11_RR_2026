# Urban Multi-Modal Routing Engine via Parallel Depth-First Search (PDFS)

An asynchronous, multi-core alternative path routing engine designed for complex, metropolitan multi-modal transit networks. This system implements a custom-built **Parallel Depth-First Search (PDFS)** routine using decentralized load balancing via **Work-Stealing** to tackle combinatorial route explosions under explicit latency and operational constraints.

This project was built to satisfy the core academic guidelines for an Intelligent Transportation System (ITS) benchmarking task.

---

## Scientific Context & Project Intent

In modern Smart Cities, localized network disruptions (e.g., a stalled subway or a massive traffic incident) require immediate, large-scale recalculation of alternative routes to shed transit passenger loads safely. While classical algorithms like single-pair Dijkstra or $A^*$ excel at isolating a single minimal path, discovering multiple viable, disjoint alternative routes requires a deep, exhaustive state-space scan.

Because lexicographical Depth-First Search is historically classified as a **P-complete** problem, it resists trivial parallel expansion because each step depends strictly on the prior exploration states. This engine implements custom multi-processing worker stacks coordinated by real-time inter-process messaging loops to split search trees safely without relying on a centralized global lock bottleneck.

### Architectural Approach

* **Asynchronous Search Splitting**: Bypasses traditional centralized bottlenecks by forcing isolated workers onto local process memory layers.

* **Dynamic Work Stealing**: Idle workers act as "thief processes," polling overloaded "victim processes" to safely offload execution tasks and split search trees on demand.

---

## Project Blueprint & System Architecture

The engine is engineered natively without relying on heavy off-the-shelf graphing suites (such as NetworkX or igraph), fulfilling the fundamental project engineering constraints:

```text
├── benchmarks/
│   ├── generate_synthetic_data.py   # Synthetic metropolitan topology generator
│   └── run_experiments.py          # Empirical scalability test runner & telemetry suite 
├── data/
│   └── .gitkeep                     # Targets for JSON graph network configurations
├── reports/
│   └── metrics_scalability.csv      # Telemetry tracking for Sp and Ep metrics
└── src/
    ├── concurrency/
    │   ├── __init__.py
    │   ├── thread_safe_pool.py      # Lock-guarded multiprocessing proxy solution bucket
    │   └── work_stealing.py        # Coarse-grained task splitting & steal managers 
    ├── core/
    │   ├── __init__.py
    │   ├── graph.py                 # Core adjacency-list based Multigraph structure 
    │   ├── loaders.py               # JSON multi-modal mesh deserializer 
    │   └── models.py                # Frozen immutable TransitEdge cost vectors 
    └── engines/
        ├── __init__.py
        └── parallel_dfs.py          # Sequential baseline vs. Parallel multi-process DFS loops 

```

### Module Mapping vs. System Requirements

1. **Module 1: Road Network Ingestion and Modeling** 

* Fully implemented in `src/core/graph.py` and `src/core/loaders.py`. It tracks dynamic directed connections featuring distinct cost matrices: Travel Time ($t$), Financial Cost ($c$), and Transfer Indicators ($tr$) across **Subway, Train, and Bus** modals.

2. **Module 2: The Native Parallel-DFS Search Engine** 

* Fully implemented across `src/engines/parallel_dfs.py` and `src/concurrency/work_stealing.py`. Handles fine-grained asynchronous loops, tracking running workers via shared primitives, cycle isolation, and proactive pruning if maximum parameters are violated.

3. **Module 3: Concurrency Coordination and Aggregation** 

* Controlled via `src/concurrency/thread_safe_pool.py. Uses atomic context locks over shared managed lists to record newly discovered end-to-end itineraries across separated worker processes without data corruption.

---

## Current Operational Capabilities & Limits (Dev Branch Status)

This release represents the initial fully-functional, **stable implementation** of the decentralized parallel processing engine before adding aggressive runtime path pruning:

* **Stable Scale**: Optimally configured for maps of **up to ~500 nodes**.
* **The 1000-Node Computational Threshold**: Since this version lacks global multi-process dominance pruning frontiers (such as an active Pareto-optimal pruning archive across processes), networks with more than 1,000 nodes running loose constraints can prompt exponential path explosions. This can cause workers to become trapped in exhaustive branch tracking, leading to high CPU load or memory overhead.
* *Note: Advanced runtime bounding structures to address this limit are actively being developed in the `feature/scale-optimization` branch.*

---

## Environment Setup & Usage

### Dependencies & Requirements

* **Python 3.9+** is required.

* **No external third-party pip packages are needed.** The project relies entirely on Python's native standard library primitives (`multiprocessing`, `queue`, `dataclasses`, `statistics`, and `json`).

### Installation

1. Clone the repository and move to your local working space:
```bash
git clone https://github.com/Math77077/FP_DCC606_Tema_11_RR_2026
cd FP_DCC606_Tema_11_RR_2026
```

2. (Recommended) Isolate the runtime environment using a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### Running Experiments & Benchmarks

To run the automated validation routine, trigger the script from your project root:

```bash
python3 -m benchmarks.run_experiments
```

#### What happens during execution:

1. **Topology Generation**: The engine verifies if a target map exists in `data/synthetic/`. If missing, it uses `generate_synthetic_data.py` to construct a 100-node multi-modal network mapping local stations and hub connections.

2. **Sequential Baseline ($T_1$)**: Executes a single-threaded deterministic DFS search to capture baseline performance and establish a validation checksum fingerprint.
3. **Parallel Iterations ($T_p$)**: Launches individual parallel engines across `[2, 4, 8]` worker process groups using full work-stealing protocols.
4. 
**Telemetry Export**: Computes algorithm verification checks, Speedup ($S_p$), and Efficiency ($E_p$) ratios across 13 test cycles, saving the metrics to `reports/metrics_scalability.csv`.


---

## Telemetry & Mathematical Evaluation

The engine uses performance telemetry to measure runtime behavior across worker pools:

$$\text{Speedup } (S_p) = \frac{T_1}{T_p} \quad \quad \text{Efficiency } (E_p) = \frac{S_p}{p}$$

The performance logging output format matches the required layout:

```text
[TEST SETUP] Loading multi-modal topology from data/synthetic/network_100_nodes.json...
[TEST EXECUTION] Initiating benchmarking routine from Station_0 to Station_4...
Constraints: Max Time = 60.0s, Max Transfers = 4

Running Sequential Baseline (13 iterations)...
Sequential Execution Mean (T_1): 0.00003 seconds
Total valid alternative paths discovered: 1

======================================================================
Workers (p) Mean Time (Tp)    Speedup (Sp)    Efficiency (Ep)
======================================================================
2           0.06939           0.000           0.024%        
4           0.13112           0.000           0.006%        
8           0.21547           0.000           0.002%        
======================================================================
```

All compiled experiment data is appended to `reports/metrics_scalability.csv` for downstream performance analysis and audit tracking.