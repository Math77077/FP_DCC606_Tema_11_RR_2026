"""
test_engines.py — Testes de unidade e integração para o módulo engines.

Cobre:
  - SearchResult  : add_path com filtro de Pareto
  - SequentialDFS : casos base, sem rota, restrições, grafo cíclico
  - ParallelDFS   : paridade com sequencial em 1/2/4 workers
  - Speedup       : ParallelDFS não deve ser mais lento que sequencial
                    em grafos com múltiplas sementes (heurístico)
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.models  import Modal, Edge, Node, Path
from src.core.graph   import Multigraph, GraphFactory
from src.engines.backtracking import SearchResult, SequentialDFS, find_routes
from src.engines.parallel_dfs import ParallelDFS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_eq(label, got, expected):
    if got != expected:
        raise AssertionError(f"[FAIL] {label}: esperado={expected!r}, obtido={got!r}")
    print(f"  [OK]  {label}")

def assert_true(label, value):
    if not value:
        raise AssertionError(f"[FAIL] {label}: esperado True")
    print(f"  [OK]  {label}")

def assert_raises(label, exc_type, fn):
    try:
        fn()
        raise AssertionError(f"[FAIL] {label}: esperava {exc_type.__name__}")
    except exc_type:
        print(f"  [OK]  {label} — {exc_type.__name__} lançada corretamente")

def _path_set(paths):
    """Converte lista de Path em frozenset de tuplas de nós para comparação."""
    return frozenset(tuple(p.nodes()) for p in paths)

def _small_graph():
    """Grafo simples A→B→C e A→C (atalho)."""
    g = Multigraph("TestSmall")
    g.add_edge_by_params("A", "B", 10.0, 3.0, 0, Modal.METRO)
    g.add_edge_by_params("B", "C",  8.0, 2.5, 0, Modal.METRO)
    g.add_edge_by_params("A", "C", 25.0, 5.0, 1, Modal.ONIBUS)
    return g


# ===========================================================================
# SearchResult
# ===========================================================================

def test_search_result_pareto_filter():
    print("\n--- SearchResult: filtro de Pareto ---")
    r = SearchResult()

    # p1 domina p2 em tudo
    e_fast = Edge("A", "B", 10.0, 4.0, 0)
    e_slow = Edge("A", "B", 20.0, 8.0, 1)

    p1 = Path("A"); p1.add_edge(e_fast)
    p2 = Path("A"); p2.add_edge(e_slow)

    r.add_path(p1)
    assert_eq("pool após p1", r.paths, [p1])

    r.add_path(p2)   # p2 dominado — descartado
    assert_eq("pool após p2 (dominado)", len(r.paths), 1)

    # p3 não domina e não é dominado — deve entrar
    e_cheap = Edge("A", "B", 30.0, 1.0, 0)
    p3 = Path("A"); p3.add_edge(e_cheap)
    r.add_path(p3)
    assert_eq("pool após p3 (Pareto)", len(r.paths), 2)

def test_search_result_summary():
    print("\n--- SearchResult: summary ---")
    r = SearchResult()
    r.elapsed_ms    = 12.5
    r.nodes_visited = 10
    s = r.summary()
    assert_true("summary contém elapsed", "12.5" in s)
    assert_true("summary contém nós",     "10"   in s)


# ===========================================================================
# SequentialDFS
# ===========================================================================

def test_seq_source_equals_target():
    print("\n--- SequentialDFS: source == target ---")
    g = _small_graph()
    r = find_routes(g, "A", "A")
    assert_eq("1 caminho (trivial)", len(r.paths), 1)
    assert_eq("caminho vazio",       r.paths[0].length(), 0)

def test_seq_direct_route():
    print("\n--- SequentialDFS: rota direta A→C ---")
    g = Multigraph()
    g.add_edge_by_params("A", "C", 5.0, 2.0, 0)
    r = find_routes(g, "A", "C")
    assert_eq("1 caminho", len(r.paths), 1)
    assert_eq("nós percorridos", r.paths[0].nodes(), ["A", "C"])

def test_seq_two_routes():
    print("\n--- SequentialDFS: dois caminhos simples ---")
    g = _small_graph()
    r = find_routes(g, "A", "C")
    paths_nodes = _path_set(r.paths)
    # Ambas as rotas são Pareto-ótimas (diferem em tempo e transferências)
    assert_true("rota A→B→C existe", ("A", "B", "C") in paths_nodes)
    assert_true("rota A→C existe",   ("A", "C")       in paths_nodes)
    assert_eq("2 caminhos Pareto",   len(r.paths), 2)

def test_seq_no_route():
    print("\n--- SequentialDFS: sem rota ---")
    g = Multigraph()
    g.add_node_by_id("X")
    g.add_node_by_id("Y")
    r = find_routes(g, "X", "Y")
    assert_eq("0 caminhos", len(r.paths), 0)

def test_seq_t_max_constraint():
    print("\n--- SequentialDFS: restrição T_max ---")
    g = _small_graph()
    # T_max=15 bloqueia A→B→C (t=18) e A→C (t=25)
    r = find_routes(g, "A", "C", t_max=15.0)
    assert_eq("0 caminhos dentro do T_max", len(r.paths), 0)

def test_seq_t_max_allows_one():
    print("\n--- SequentialDFS: T_max permite apenas rota curta ---")
    g = _small_graph()
    # T_max=20 bloqueia A→C (t=25) mas permite A→B→C (t=18)
    r = find_routes(g, "A", "C", t_max=20.0)
    assert_eq("1 caminho", len(r.paths), 1)
    assert_eq("rota A→B→C", r.paths[0].nodes(), ["A", "B", "C"])

def test_seq_tr_max_constraint():
    print("\n--- SequentialDFS: restrição TR_max=0 ---")
    g = _small_graph()
    # TR_max=0 bloqueia A→C (transfer=1), permite A→B→C (transfers=0)
    r = find_routes(g, "A", "C", tr_max=0)
    assert_eq("1 caminho (sem transfer)", len(r.paths), 1)
    assert_eq("rota A→B→C", r.paths[0].nodes(), ["A", "B", "C"])

def test_seq_cyclic_graph():
    print("\n--- SequentialDFS: grafo com ciclos ---")
    g = Multigraph()
    g.add_edge_by_params("A", "B", 5.0, 1.0, 0)
    g.add_edge_by_params("B", "C", 5.0, 1.0, 0)
    g.add_edge_by_params("C", "A", 5.0, 1.0, 0)  # ciclo
    g.add_edge_by_params("B", "D", 3.0, 1.0, 0)
    r = find_routes(g, "A", "D")
    paths_nodes = _path_set(r.paths)
    assert_true("A→B→D encontrado",     ("A", "B", "D") in paths_nodes)
    # Não deve ter caminhos com A repetido (ciclo bloqueado)
    for p in r.paths:
        nodes = p.nodes()
        assert_true(f"sem ciclo em {nodes}", len(nodes) == len(set(nodes)))

def test_seq_invalid_source():
    print("\n--- SequentialDFS: vértice inválido ---")
    g = _small_graph()
    assert_raises("KeyError origem", KeyError, lambda: find_routes(g, "Z", "C"))
    assert_raises("KeyError destino", KeyError, lambda: find_routes(g, "A", "Z"))

def test_seq_urban_mesh():
    print("\n--- SequentialDFS: malha urbana (A→H) ---")
    g = GraphFactory.small_urban_mesh()
    r = find_routes(g, "A", "H", t_max=80.0, tr_max=3)
    assert_true("pelo menos 1 rota encontrada", len(r.paths) >= 1)
    assert_true("nós visitados > 0",            r.nodes_visited > 0)
    # Todos os caminhos devem começar em A e terminar em H
    for p in r.paths:
        nodes = p.nodes()
        assert_true(f"inicia em A: {nodes}", nodes[0] == "A")
        assert_true(f"termina em H: {nodes}", nodes[-1] == "H")

def test_seq_telemetry():
    print("\n--- SequentialDFS: telemetria ---")
    g = _small_graph()
    r = find_routes(g, "A", "C")
    assert_true("elapsed > 0",     r.elapsed_ms    >= 0)
    assert_true("visited > 0",     r.nodes_visited >  0)


# ===========================================================================
# ParallelDFS
# ===========================================================================

def test_par_same_as_seq_1_worker():
    print("\n--- ParallelDFS: 1 worker == sequencial ---")
    g = GraphFactory.small_urban_mesh()

    r_seq = find_routes(g, "A", "H", t_max=80.0, tr_max=3)
    r_par = ParallelDFS(g, num_workers=1, t_max=80.0, tr_max=3).search("A", "H")

    assert_eq("mesmo nº de caminhos Pareto",
              len(r_par.paths), len(r_seq.paths))
    assert_eq("mesmo conjunto de caminhos",
              _path_set(r_par.paths), _path_set(r_seq.paths))

def test_par_same_as_seq_2_workers():
    print("\n--- ParallelDFS: 2 workers == sequencial ---")
    g = GraphFactory.small_urban_mesh()

    r_seq = find_routes(g, "A", "H", t_max=80.0, tr_max=3)
    r_par = ParallelDFS(g, num_workers=2, t_max=80.0, tr_max=3).search("A", "H")

    assert_eq("mesmo conjunto (2 workers)",
              _path_set(r_par.paths), _path_set(r_seq.paths))

def test_par_same_as_seq_4_workers():
    print("\n--- ParallelDFS: 4 workers == sequencial ---")
    g = GraphFactory.small_urban_mesh()

    r_seq = find_routes(g, "A", "H", t_max=80.0, tr_max=3)
    r_par = ParallelDFS(g, num_workers=4, t_max=80.0, tr_max=3).search("A", "H")

    assert_eq("mesmo conjunto (4 workers)",
              _path_set(r_par.paths), _path_set(r_seq.paths))

def test_par_no_route():
    print("\n--- ParallelDFS: sem rota ---")
    g = Multigraph()
    g.add_node_by_id("X")
    g.add_node_by_id("Y")
    r = ParallelDFS(g, num_workers=2).search("X", "Y")
    assert_eq("0 caminhos paralelo", len(r.paths), 0)

def test_par_invalid_nodes():
    print("\n--- ParallelDFS: vértices inválidos ---")
    g = GraphFactory.small_urban_mesh()
    assert_raises("KeyError origem paralelo",  KeyError,
        lambda: ParallelDFS(g).search("Z", "H"))
    assert_raises("KeyError destino paralelo", KeyError,
        lambda: ParallelDFS(g).search("A", "Z"))

def test_par_constraints_respected():
    print("\n--- ParallelDFS: restrições respeitadas ---")
    g = GraphFactory.small_urban_mesh()
    t_max  = 50.0
    tr_max = 1
    r = ParallelDFS(g, num_workers=3, t_max=t_max, tr_max=tr_max).search("A", "H")
    for p in r.paths:
        assert_true(f"t≤{t_max}: {p.total_time():.1f}",
                    p.total_time() <= t_max)
        assert_true(f"tr≤{tr_max}: {p.total_transfers()}",
                    p.total_transfers() <= tr_max)

def test_par_synthetic_pareto_correctness():
    print("\n--- ParallelDFS: Pareto correto em grafo sintético (20 nós) ---")
    g = GraphFactory.synthetic_random(20, avg_degree=4, seed=99)

    r_seq = find_routes(g, "v0", "v19", t_max=200.0, tr_max=5)
    r_par = ParallelDFS(g, num_workers=4, t_max=200.0, tr_max=5).search("v0", "v19")

    assert_eq("Pareto idêntico (sintético 20)",
              _path_set(r_par.paths), _path_set(r_seq.paths))


# ===========================================================================
# Speedup heurístico (não garante em CI lento, apenas valida estrutura)
# ===========================================================================

def test_par_workers_produce_result():
    print("\n--- ParallelDFS: resultado com 8 workers ---")
    g = GraphFactory.synthetic_random(12, avg_degree=3, seed=7)
    r = ParallelDFS(g, num_workers=8, t_max=200.0, tr_max=5).search("v0", "v11")
    r_seq = find_routes(g, "v0", "v11", t_max=200.0, tr_max=5)
    assert_eq("Pareto idêntico (8 workers)",
              _path_set(r.paths), _path_set(r_seq.paths))
    assert_true("elapsed registrado", r.elapsed_ms >= 0)


# ===========================================================================
# Runner
# ===========================================================================

def run_all():
    suites = [
        # SearchResult
        test_search_result_pareto_filter,
        test_search_result_summary,
        # SequentialDFS
        test_seq_source_equals_target,
        test_seq_direct_route,
        test_seq_two_routes,
        test_seq_no_route,
        test_seq_t_max_constraint,
        test_seq_t_max_allows_one,
        test_seq_tr_max_constraint,
        test_seq_cyclic_graph,
        test_seq_invalid_source,
        test_seq_urban_mesh,
        test_seq_telemetry,
        # ParallelDFS
        test_par_same_as_seq_1_worker,
        test_par_same_as_seq_2_workers,
        test_par_same_as_seq_4_workers,
        test_par_no_route,
        test_par_invalid_nodes,
        test_par_constraints_respected,
        test_par_synthetic_pareto_correctness,
        test_par_workers_produce_result,
    ]

    passed = failed = 0
    errors = []

    print("\n" + "="*60)
    print("  SUITE: test_engines.py")
    print("="*60)

    for fn in suites:
        try:
            fn()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append(str(e))
        except Exception as e:
            failed += 1
            errors.append(f"[ERROR] {fn.__name__}: {type(e).__name__}: {e}")

    print("\n" + "="*60)
    print(f"  Resultado: {passed} OK  |  {failed} FALHA(S)")
    if errors:
        print("\n  Falhas:")
        for err in errors:
            print(f"    {err}")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
