"""
test_graph.py — Testes de unidade para o módulo core.

Cobre:
  - Edge      : criação, validação, cost_vector
  - Node      : criação, igualdade
  - Path      : add_edge, backtrack, dominância de Pareto, clone
  - Multigraph: inserção, remoção, consultas, serialização
  - GraphFactory: small_urban_mesh, synthetic_random
"""

import sys
import os

# Garante que o diretório raiz do projeto está no PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.models import Modal, Edge, Node, Path
from src.core.graph  import Multigraph, GraphFactory


# ===========================================================================
# Helpers
# ===========================================================================

def assert_eq(label: str, got, expected) -> None:
    if got != expected:
        raise AssertionError(f"[FAIL] {label}: esperado={expected!r}, obtido={got!r}")
    print(f"  [OK]  {label}")

def assert_true(label: str, value: bool) -> None:
    if not value:
        raise AssertionError(f"[FAIL] {label}: esperado True, obtido False")
    print(f"  [OK]  {label}")

def assert_raises(label: str, exc_type, fn) -> None:
    try:
        fn()
        raise AssertionError(f"[FAIL] {label}: esperava {exc_type.__name__}, nenhuma exceção lançada")
    except exc_type:
        print(f"  [OK]  {label} — {exc_type.__name__} lançada corretamente")


# ===========================================================================
# Testes de Edge
# ===========================================================================

def test_edge_creation():
    print("\n--- Edge: criação e atributos ---")
    e = Edge("A", "B", 10.0, 4.50, 0, Modal.METRO)
    assert_eq("origin",      e.origin,      "A")
    assert_eq("destination", e.destination, "B")
    assert_eq("travel_time", e.travel_time, 10.0)
    assert_eq("fare",        e.fare,        4.50)
    assert_eq("transfer",    e.transfer,    0)
    assert_eq("modal",       e.modal,       Modal.METRO)
    assert_eq("cost_vector", e.cost_vector(), (10.0, 4.50, 0))

def test_edge_auto_id():
    print("\n--- Edge: ID automático ---")
    e = Edge("X", "Y", 5.0, 2.0, 1, Modal.TREM)
    assert_eq("edge_id", e.edge_id, "X->Y@Trem")

def test_edge_custom_id():
    print("\n--- Edge: ID personalizado ---")
    e = Edge("X", "Y", 5.0, 2.0, 1, Modal.TREM, edge_id="my_edge")
    assert_eq("custom edge_id", e.edge_id, "my_edge")

def test_edge_validation():
    print("\n--- Edge: validações de entrada ---")
    assert_raises("travel_time negativo", ValueError,
        lambda: Edge("A", "B", -1.0, 0.0, 0))
    assert_raises("fare negativa", ValueError,
        lambda: Edge("A", "B", 1.0, -1.0, 0))
    assert_raises("transfer inválido", ValueError,
        lambda: Edge("A", "B", 1.0, 0.0, 2))
    assert_raises("modal inválido", ValueError,
        lambda: Edge("A", "B", 1.0, 0.0, 0, "Aviao"))


# ===========================================================================
# Testes de Node
# ===========================================================================

def test_node_creation():
    print("\n--- Node: criação ---")
    n = Node("C", "Hospital", [Modal.ONIBUS])
    assert_eq("node_id", n.node_id, "C")
    assert_eq("name",    n.name,    "Hospital")
    assert_eq("modals",  n.modals,  [Modal.ONIBUS])

def test_node_equality():
    print("\n--- Node: igualdade por node_id ---")
    n1 = Node("X", "Praca", [])
    n2 = Node("X", "Outro Nome", [Modal.METRO])
    n3 = Node("Y", "Praca", [])
    assert_true("n1 == n2 (mesmo ID)", n1 == n2)
    assert_true("n1 != n3 (IDs distintos)", n1 != n3)


# ===========================================================================
# Testes de Path
# ===========================================================================

def test_path_basic():
    print("\n--- Path: operações básicas ---")
    p = Path("A")
    assert_eq("current_node inicial", p.current_node(), "A")
    assert_eq("length inicial",       p.length(),       0)
    assert_eq("total_time inicial",   p.total_time(),   0.0)

def test_path_add_and_backtrack():
    print("\n--- Path: add_edge + backtrack ---")
    e1 = Edge("A", "B", 10.0, 4.0, 0, Modal.METRO)
    e2 = Edge("B", "C",  8.0, 3.5, 1, Modal.ONIBUS)

    p = Path("A")
    p.add_edge(e1)
    assert_eq("current após add e1", p.current_node(), "B")
    assert_eq("time após e1",        p.total_time(),   10.0)
    assert_eq("transfer após e1",    p.total_transfers(), 0)

    p.add_edge(e2)
    assert_eq("current após add e2", p.current_node(), "C")
    assert_eq("time após e2",        p.total_time(),   18.0)
    assert_eq("transfer após e2",    p.total_transfers(), 1)
    assert_eq("nodes",               p.nodes(), ["A", "B", "C"])

    removed = p.remove_last_edge()
    assert_eq("aresta removida",     removed.edge_id, e2.edge_id)
    assert_eq("current após bt",     p.current_node(), "B")
    assert_eq("time após bt",        p.total_time(),   10.0)

def test_path_cycle_detection():
    print("\n--- Path: detecção de ciclo ---")
    e1 = Edge("A", "B", 5.0, 2.0, 0)
    e2 = Edge("B", "A", 5.0, 2.0, 0)  # ciclo
    p = Path("A")
    p.add_edge(e1)
    assert_raises("ciclo detectado", ValueError, lambda: p.add_edge(e2))

def test_path_clone():
    print("\n--- Path: clone independente ---")
    e1 = Edge("A", "B", 10.0, 4.0, 0)
    p  = Path("A")
    p.add_edge(e1)

    c = p.clone()
    assert_eq("clone length",       c.length(),       p.length())
    assert_eq("clone total_time",   c.total_time(),   p.total_time())
    assert_eq("clone current_node", c.current_node(), p.current_node())

    # Clone deve ser independente
    e2 = Edge("B", "C", 5.0, 2.0, 1)
    c.add_edge(e2)
    assert_eq("original não alterado", p.length(), 1)
    assert_eq("clone avançou",         c.length(), 2)

def test_path_dominance():
    print("\n--- Path: dominância de Pareto ---")
    # p1: t=10, fare=4, tr=0
    # p2: t=15, fare=5, tr=1  → p1 domina p2
    # p3: t=8,  fare=6, tr=0  → p1 e p3 não se dominam
    e_fast  = Edge("A", "B", 10.0, 4.0, 0)
    e_slow  = Edge("A", "B", 15.0, 5.0, 1)
    e_cheap = Edge("A", "B",  8.0, 6.0, 0)

    p1 = Path("A"); p1.add_edge(e_fast)
    p2 = Path("A"); p2.add_edge(e_slow)
    p3 = Path("A"); p3.add_edge(e_cheap)

    assert_true("p1 domina p2",        p1.dominates(p2))
    assert_true("p2 não domina p1",    not p2.dominates(p1))
    assert_true("p1 não domina p3",    not p1.dominates(p3))
    assert_true("p3 não domina p1",    not p3.dominates(p1))


# ===========================================================================
# Testes de Multigraph
# ===========================================================================

def test_graph_add_nodes():
    print("\n--- Multigraph: inserção de vértices ---")
    g = Multigraph("Teste")
    n = Node("A", "Estação A", [Modal.METRO])
    g.add_node(n)
    assert_eq("node_count", g.node_count(), 1)
    assert_true("has_node A", g.has_node("A"))
    assert_true("não tem B",  not g.has_node("B"))

def test_graph_duplicate_node():
    print("\n--- Multigraph: duplicata de vértice ignorada ---")
    g = Multigraph()
    g.add_node_by_id("A", "Parada A")
    g.add_node_by_id("A", "Duplicata A")
    assert_eq("node_count sem duplicata", g.node_count(), 1)

def test_graph_add_edges():
    print("\n--- Multigraph: inserção de arestas ---")
    g = Multigraph()
    g.add_node_by_id("A", "Parada A")
    g.add_node_by_id("B", "Parada B")
    g.add_edge(Edge("A", "B", 10.0, 3.5, 0, Modal.METRO))
    assert_eq("edge_count",  g.edge_count(), 1)
    assert_true("has_edge",  g.has_edge("A", "B"))
    assert_true("sem reversa", not g.has_edge("B", "A"))

def test_graph_bidirectional():
    print("\n--- Multigraph: aresta bidirecional ---")
    g = Multigraph()
    g.add_edge_by_params("X", "Y", 5.0, 2.0, 0, Modal.ONIBUS, bidirectional=True)
    assert_eq("edge_count bidirecional", g.edge_count(), 2)
    assert_true("X→Y", g.has_edge("X", "Y"))
    assert_true("Y→X", g.has_edge("Y", "X"))

def test_graph_auto_create_nodes():
    print("\n--- Multigraph: auto-criação de vértices ao inserir aresta ---")
    g = Multigraph()
    g.add_edge(Edge("P", "Q", 1.0, 1.0, 0))
    assert_true("P criado", g.has_node("P"))
    assert_true("Q criado", g.has_node("Q"))

def test_graph_multiparallelism():
    print("\n--- Multigraph: arestas paralelas (multigrafo) ---")
    g = Multigraph()
    g.add_edge(Edge("A", "B", 10.0, 4.0, 0, Modal.METRO))
    g.add_edge(Edge("A", "B",  8.0, 6.0, 1, Modal.TREM))
    assert_eq("2 arestas paralelas", g.edge_count(), 2)
    assert_eq("grau de saída de A",  g.out_degree("A"), 2)

def test_graph_get_neighbors():
    print("\n--- Multigraph: get_neighbors ---")
    g = Multigraph()
    g.add_edge(Edge("A", "B", 10.0, 4.0, 0))
    g.add_edge(Edge("A", "C",  5.0, 2.5, 1))
    neighbors = g.get_neighbors("A")
    dests = {e.destination for e in neighbors}
    assert_eq("vizinhos de A", dests, {"B", "C"})

def test_graph_remove_node():
    print("\n--- Multigraph: remoção de vértice ---")
    g = Multigraph()
    g.add_edge(Edge("A", "B", 10.0, 4.0, 0))
    g.add_edge(Edge("B", "C",  5.0, 2.5, 0))
    g.remove_node("B")
    assert_true("B removido",         not g.has_node("B"))
    assert_eq("node_count pós-remoção", g.node_count(), 2)
    # A→B deve ter sido removida
    assert_true("A→B removida", not g.has_edge("A", "B"))
    # C ainda existe
    assert_true("C ainda existe", g.has_node("C"))

def test_graph_remove_nonexistent():
    print("\n--- Multigraph: remoção de vértice inexistente ---")
    g = Multigraph()
    assert_raises("KeyError esperado", KeyError, lambda: g.remove_node("Z"))

def test_graph_serialization():
    print("\n--- Multigraph: serialização/desserialização ---")
    g = Multigraph("RoundTrip")
    g.add_edge_by_params("A", "B", 10.0, 4.5, 0, Modal.METRO)
    g.add_edge_by_params("B", "C",  8.0, 3.0, 1, Modal.ONIBUS)

    d   = g.to_dict()
    g2  = Multigraph.from_dict(d)

    assert_eq("nome preservado",    g2.name,        "RoundTrip")
    assert_eq("node_count",         g2.node_count(), g.node_count())
    assert_eq("edge_count",         g2.edge_count(), g.edge_count())
    assert_true("aresta A→B",       g2.has_edge("A", "B"))
    assert_true("aresta B→C",       g2.has_edge("B", "C"))

def test_adjacency_matrix():
    print("\n--- Multigraph: matriz de adjacência ---")
    g = Multigraph()
    g.add_edge_by_params("A", "B", 10.0, 4.0, 0)
    g.add_edge_by_params("B", "C",  5.0, 2.0, 0)
    labels, mat = g.to_adjacency_matrix()
    idx = {l: i for i, l in enumerate(labels)}
    INF = float("inf")
    assert_eq("A→B", mat[idx["A"]][idx["B"]], 10.0)
    assert_eq("B→C", mat[idx["B"]][idx["C"]],  5.0)
    assert_eq("A→C (sem aresta direta)", mat[idx["A"]][idx["C"]], INF)


# ===========================================================================
# Testes de GraphFactory
# ===========================================================================

def test_factory_small_mesh():
    print("\n--- GraphFactory: small_urban_mesh ---")
    g = GraphFactory.small_urban_mesh()
    assert_true("8 vértices", g.node_count() == 8)
    assert_true("arestas > 0", g.edge_count() > 0)
    assert_true("Central existe",   g.has_node("A"))
    assert_true("Aeroporto existe", g.has_node("H"))
    assert_true("aresta A→B existe", g.has_edge("A", "B"))

def test_factory_synthetic_10():
    print("\n--- GraphFactory: synthetic_random(10) ---")
    g = GraphFactory.synthetic_random(10, avg_degree=3, seed=7)
    assert_eq("10 vértices", g.node_count(), 10)
    assert_true("arestas > 9", g.edge_count() > 9)   # ao menos o caminho hamiltoniano

def test_factory_synthetic_100():
    print("\n--- GraphFactory: synthetic_random(100) ---")
    g = GraphFactory.synthetic_random(100, avg_degree=4, seed=0)
    assert_eq("100 vértices", g.node_count(), 100)
    assert_true("arestas ≥ 99", g.edge_count() >= 99)


# ===========================================================================
# Runner
# ===========================================================================

def run_all():
    suites = [
        # Edge
        test_edge_creation,
        test_edge_auto_id,
        test_edge_custom_id,
        test_edge_validation,
        # Node
        test_node_creation,
        test_node_equality,
        # Path
        test_path_basic,
        test_path_add_and_backtrack,
        test_path_cycle_detection,
        test_path_clone,
        test_path_dominance,
        # Multigraph
        test_graph_add_nodes,
        test_graph_duplicate_node,
        test_graph_add_edges,
        test_graph_bidirectional,
        test_graph_auto_create_nodes,
        test_graph_multiparallelism,
        test_graph_get_neighbors,
        test_graph_remove_node,
        test_graph_remove_nonexistent,
        test_graph_serialization,
        test_adjacency_matrix,
        # GraphFactory
        test_factory_small_mesh,
        test_factory_synthetic_10,
        test_factory_synthetic_100,
    ]

    passed = 0
    failed = 0
    errors = []

    print("\n" + "="*60)
    print("  SUITE: test_graph.py")
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
            errors.append(f"[ERROR] {fn.__name__}: {e}")

    print("\n" + "="*60)
    print(f"  Resultado: {passed} OK  |  {failed} FALHA(S)")
    if errors:
        print("\n  Falhas:")
        for err in errors:
            print(f"    {err}")
    print("="*60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
