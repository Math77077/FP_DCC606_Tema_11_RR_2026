# Simplified Python Project Structure

```text
FP_DCC606_Tema_11_RR_2026/         
│
├── docs/                          # Project Documentation 
│   ├── templates/                 # SBC article templates (ZIP contents) 
│   └── report.pdf                 # Final 4+ page IEEE/SBC report 
│
├── data/                          # Input data files 
│   ├── synthetic/                 # Generated test files (10k to 100k nodes) 
│   └── metropolitan_mesh.json     # Base scenario (Station Central -> Airport) 
│
├── src/                           # Main Python Source Code
│   ├── __init__.py                # Makes 'src' a Python package
│   │
│   ├── core/                      # Módulo 1: Data structures and parsing 
│   │   ├── __init__.py
│   │   ├── graph.py               # Custom Multigraph Adjacency List 
│   │   └── models.py              # Edge vectors: [t(e), c(e), tr(e)] 
│   │
│   ├── engines/                   # Módulo 2: Computational Engines 
│   │   ├── __init__.py
│   │   └── parallel_dfs.py        # Custom Parallel DFS implementation 
│   │
│   ├── concurrency/               # Módulo 3: Coordination Layers 
│   │   ├── __init__.py
│   │   ├── work_stealing.py       # Load balancing / Task distribution logic 
│   │   └── thread_safe_pool.py    # Custom Lock/Queue coordination 
│   │
│   └── interface/                 # Visual components 
│       ├── __init__.py
│       └── app.py                 # Visual Panel (Tkinter / Streamlit) 
│
├── tests/                         # Test suites for verification 
│   ├── test_graph.py              # Verifies custom graph building 
│   └── test_engines.py            # Verifies routing logic accuracy 
│
├── benchmarks/                    # Performance testing & evaluation 
│   ├── runner.py                  # Script running the test batteries 
│   ├── table_10_rover.csv         # Results for Benchmarking Combinatório 
│   └── table_11_scalability.csv   # Results for Escalabilidade e Desempenho 
│
├── .gitignore                     # Ignores __pycache__/, .venv/, and local logs
├── README.md                      # Setup instructions, Team info, and run guide
└── requirements.txt               # Dependencies (e.g., streamlit, graphviz)

```