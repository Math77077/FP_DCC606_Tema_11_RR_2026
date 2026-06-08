"""
graph.py — Multigrafo Dirigido com Lista de Adjacência Dinâmica.

Implementação 100% manual — sem NetworkX, igraph, BGL ou similares.

Estrutura interna
-----------------
  _nodes : dict[str, Node]        — índice de vértices (id → Node)
  _adj   : dict[str, list[Edge]]  — lista de adjacência (id → [Edge, ...])

Um multigrafo permite múltiplas arestas paralelas entre o mesmo par (u, v),
o que é necessário quando dois pontos são conectados por mais de um modal
(ex.: ônibus E metrô entre a mesma dupla de paradas).

Complexidades (n = |V|, m = |E|, d = grau médio de saída)
----------------------------------------------------------
  add_node          : O(1) amortizado
  add_edge          : O(1) amortizado
  get_neighbors     : O(1)  (retorna referência à lista)
  has_node          : O(1)
  has_edge          : O(grau(u))
  remove_node       : O(n + m)  — precisa varrer adj para limpar arestas
  remove_edge       : O(grau(u))
  node_count        : O(1)
  edge_count        : O(n)   — soma os graus
  to_adjacency_matrix: O(n²) — apenas para grafos pequenos/debug
  from_dict         : O(n + m)
"""

from __future__ import annotations
from typing import Optional, Iterator

from src.core.models import Node, Edge, Modal


class Multigraph:
    """
    Multigrafo dirigido e ponderado para representação de redes de transporte.

    Cada vértice tem um identificador único (str) e cada aresta carrega
    o vetor de custos C(e) = [t(e), c(e), tr(e)].
    """

    def __init__(self, name: str = "TransportGraph") -> None:
        self.name   : str                      = name
        self._nodes : dict[str, Node]          = {}   # id → Node
        self._adj   : dict[str, list[Edge]]    = {}   # id → lista de arestas de saída

    # ==================================================================
    # Inserção
    # ==================================================================

    def add_node(self, node: Node) -> None:
        """
        Insere um vértice no grafo. Ignora silenciosamente duplicatas. O(1).

        Parâmetros
        ----------
        node : Node — objeto Node a ser inserido
        """
        if node.node_id not in self._nodes:
            self._nodes[node.node_id] = node
            self._adj[node.node_id]   = []   # lista de adjacência vazia

    def add_node_by_id(
        self,
        node_id: str,
        name: Optional[str] = None,
        modals: Optional[list[str]] = None,
    ) -> Node:
        """
        Atalho: cria e insere um Node a partir de strings. O(1).
        Retorna o Node criado (ou o já existente se for duplicata).
        """
        if node_id in self._nodes:
            return self._nodes[node_id]
        node = Node(node_id, name or node_id, modals or [])
        self.add_node(node)
        return node

    def add_edge(self, edge: Edge) -> None:
        """
        Insere uma aresta dirigida (origin → destination). O(1) amortizado.

        Garante que ambos os vértices existam antes de inserir.
        Permite múltiplas arestas entre o mesmo par (multigrafo).

        Parâmetros
        ----------
        edge : Edge — objeto Edge a ser inserido
        """
        # Garante existência dos vértices extremos
        if edge.origin not in self._nodes:
            self.add_node_by_id(edge.origin)
        if edge.destination not in self._nodes:
            self.add_node_by_id(edge.destination)

        self._adj[edge.origin].append(edge)

    def add_edge_by_params(
        self,
        origin: str,
        destination: str,
        travel_time: float,
        fare: float,
        transfer: int,
        modal: str = Modal.ONIBUS,
        bidirectional: bool = False,
    ) -> Edge:
        """
        Atalho: cria e insere uma aresta a partir de parâmetros. O(1).

        Se bidirectional=True, insere também a aresta reversa com os
        mesmos custos (útil para vias de mão dupla).

        Retorna a aresta de ida criada.
        """
        edge = Edge(origin, destination, travel_time, fare, transfer, modal)
        self.add_edge(edge)

        if bidirectional:
            rev = Edge(destination, origin, travel_time, fare, transfer, modal)
            self.add_edge(rev)

        return edge

    # ==================================================================
    # Remoção
    # ==================================================================

    def remove_node(self, node_id: str) -> None:
        """
        Remove um vértice e todas as arestas incidentes a ele. O(n + m).

        Lança KeyError se o vértice não existir.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Vértice não encontrado: {node_id!r}")

        del self._nodes[node_id]
        del self._adj[node_id]

        # Remove arestas de outros vértices que apontam para node_id
        for adj_list in self._adj.values():
            # Filtra in-place: mantém apenas arestas cujo destino ≠ node_id
            to_remove = [e for e in adj_list if e.destination == node_id]
            for e in to_remove:
                adj_list.remove(e)

    def remove_edge(self, edge_id: str) -> None:
        """
        Remove a primeira aresta com o edge_id fornecido. O(m) pior caso.

        Lança KeyError se nenhuma aresta com esse ID existir.
        """
        for adj_list in self._adj.values():
            for i, edge in enumerate(adj_list):
                if edge.edge_id == edge_id:
                    adj_list.pop(i)
                    return
        raise KeyError(f"Aresta não encontrada: {edge_id!r}")

    # ==================================================================
    # Consultas
    # ==================================================================

    def has_node(self, node_id: str) -> bool:
        """O(1)."""
        return node_id in self._nodes

    def has_edge(self, origin: str, destination: str) -> bool:
        """
        Retorna True se existe pelo menos uma aresta origin → destination. O(grau(origin)).
        """
        if origin not in self._adj:
            return False
        return any(e.destination == destination for e in self._adj[origin])

    def get_node(self, node_id: str) -> Node:
        """Retorna o Node. Lança KeyError se não existir. O(1)."""
        if node_id not in self._nodes:
            raise KeyError(f"Vértice não encontrado: {node_id!r}")
        return self._nodes[node_id]

    def get_neighbors(self, node_id: str) -> list[Edge]:
        """
        Retorna a lista de arestas de saída de node_id. O(1).
        (Retorna referência — não modifique externamente.)

        Lança KeyError se o vértice não existir.
        """
        if node_id not in self._adj:
            raise KeyError(f"Vértice não encontrado: {node_id!r}")
        return self._adj[node_id]

    def node_count(self) -> int:
        """Número de vértices. O(1)."""
        return len(self._nodes)

    def edge_count(self) -> int:
        """Número total de arestas (soma dos graus de saída). O(n)."""
        return sum(len(adj) for adj in self._adj.values())

    def out_degree(self, node_id: str) -> int:
        """Grau de saída de node_id. O(1)."""
        return len(self._adj[node_id])

    def nodes(self) -> Iterator[Node]:
        """Iterador sobre todos os vértices. O(1) por iteração."""
        return iter(self._nodes.values())

    def all_edges(self) -> Iterator[Edge]:
        """Iterador sobre todas as arestas. O(1) por iteração."""
        for adj_list in self._adj.values():
            for edge in adj_list:
                yield edge

    # ==================================================================
    # Serialização / Desserialização
    # ==================================================================

    def to_dict(self) -> dict:
        """
        Serializa o grafo para um dicionário Python (compatível com JSON). O(n + m).

        Formato:
        {
            "name": str,
            "nodes": [{"node_id": str, "name": str, "modals": [...]}],
            "edges": [{"origin": str, "destination": str, "travel_time": float,
                       "fare": float, "transfer": int, "modal": str, "edge_id": str}]
        }
        """
        return {
            "name": self.name,
            "nodes": [
                {"node_id": n.node_id, "name": n.name, "modals": n.modals}
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "origin":      e.origin,
                    "destination": e.destination,
                    "travel_time": e.travel_time,
                    "fare":        e.fare,
                    "transfer":    e.transfer,
                    "modal":       e.modal,
                    "edge_id":     e.edge_id,
                }
                for e in self.all_edges()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Multigraph":
        """
        Desserializa um dicionário (gerado por to_dict ou carregado de JSON). O(n + m).

        Parâmetros
        ----------
        data : dict — dicionário no formato de to_dict()
        """
        graph = cls(name=data.get("name", "TransportGraph"))

        for n in data.get("nodes", []):
            graph.add_node(Node(n["node_id"], n["name"], n.get("modals", [])))

        for e in data.get("edges", []):
            graph.add_edge(Edge(
                origin      = e["origin"],
                destination = e["destination"],
                travel_time = e["travel_time"],
                fare        = e["fare"],
                transfer    = e["transfer"],
                modal       = e.get("modal", Modal.ONIBUS),
                edge_id     = e.get("edge_id"),
            ))

        return graph

    # ==================================================================
    # Diagnóstico / Debug
    # ==================================================================

    def to_adjacency_matrix(self) -> tuple[list[str], list[list[float]]]:
        """
        Gera matriz de adjacência (tempo) para grafos pequenos/debug. O(n²).

        Retorna
        -------
        (labels, matrix) onde labels[i] = node_id e matrix[i][j] = tempo
        mínimo da aresta i→j (inf se não existe aresta direta).
        """
        labels = sorted(self._nodes.keys())
        idx    = {nid: i for i, nid in enumerate(labels)}
        n      = len(labels)
        INF    = float("inf")
        matrix = [[INF] * n for _ in range(n)]

        for i, nid in enumerate(labels):
            matrix[i][i] = 0.0  # custo de ir a si mesmo é zero
            for edge in self._adj[nid]:
                j = idx[edge.destination]
                # No multigrafo, mantém o menor tempo entre arestas paralelas
                if edge.travel_time < matrix[i][j]:
                    matrix[i][j] = edge.travel_time

        return labels, matrix

    def print_summary(self) -> None:
        """Imprime um resumo do grafo no stdout. O(n + m)."""
        print(f"\n{'='*55}")
        print(f"  Grafo: {self.name!r}")
        print(f"  Vértices : {self.node_count()}")
        print(f"  Arestas  : {self.edge_count()}")
        print(f"{'='*55}")
        for node in sorted(self._nodes.values(), key=lambda n: n.node_id):
            neighbors = self._adj[node.node_id]
            print(f"  [{node.node_id}] {node.name}")
            for e in neighbors:
                print(
                    f"      → {e.destination:<12} "
                    f"t={e.travel_time:5.1f}min  "
                    f"R${e.fare:5.2f}  "
                    f"tr={e.transfer}  "
                    f"modal={e.modal}"
                )
        print(f"{'='*55}\n")

    def __repr__(self) -> str:
        return (
            f"Multigraph(name={self.name!r}, "
            f"nodes={self.node_count()}, "
            f"edges={self.edge_count()})"
        )


# ===========================================================================
# Fábrica de grafos sintéticos (para testes e benchmarks)
# ===========================================================================

class GraphFactory:
    """
    Gera instâncias de Multigraph para testes sem dados reais.

    Todos os métodos são estáticos e retornam objetos Multigraph prontos.
    """

    @staticmethod
    def small_urban_mesh() -> Multigraph:
        """
        Malha urbana pequena com 8 vértices e ~14 arestas.
        Representa: Estação Central → Aeroporto com rotas alternativas.

        Topologia (orientada, com bidirecionalidade seletiva):

            [A] Central ──(Metro 10min)──► [B] Praça ──(Metro 8min)──► [E] Shopping
             |                              |                              |
          (Bus 15min)                   (Bus 12min)                  (Bus 6min)
             ▼                              ▼                              ▼
            [C] Hospital ──(Bus 9min)──► [D] Parque ──(Bus 7min)──► [F] Rodoviária
                                                                        |
                                                                     (Trem 14min)
                                                                        ▼
                                                                     [G] Ponte ──(Bus 5min)──► [H] Aeroporto
        """
        g = Multigraph("MalhaUrbana_Pequena")

        # Vértices
        for nid, nome, modals in [
            ("A", "Estacao_Central",  [Modal.METRO, Modal.ONIBUS]),
            ("B", "Praca_Central",    [Modal.METRO, Modal.ONIBUS]),
            ("C", "Hospital_Geral",   [Modal.ONIBUS]),
            ("D", "Parque_Aquático",  [Modal.ONIBUS]),
            ("E", "Shopping_Norte",   [Modal.METRO, Modal.ONIBUS]),
            ("F", "Rodoviaria",       [Modal.TREM, Modal.ONIBUS]),
            ("G", "Ponte_Sul",        [Modal.TREM, Modal.ONIBUS]),
            ("H", "Aeroporto",        [Modal.ONIBUS]),
        ]:
            g.add_node_by_id(nid, nome, modals)

        # Arestas (origin, destination, travel_time, fare, transfer, modal, bidir)
        edges = [
            # Corredor metrô principal
            ("A", "B", 10.0, 4.50, 0, Modal.METRO,  True),
            ("B", "E",  8.0, 4.50, 0, Modal.METRO,  False),
            # Linhas de ônibus
            ("A", "C", 15.0, 3.80, 1, Modal.ONIBUS, False),
            ("B", "D", 12.0, 3.80, 1, Modal.ONIBUS, False),
            ("C", "D",  9.0, 3.80, 0, Modal.ONIBUS, True),
            ("D", "F",  7.0, 3.80, 0, Modal.ONIBUS, False),
            ("E", "F",  6.0, 3.80, 1, Modal.ONIBUS, False),
            # Linha de trem para o aeroporto
            ("F", "G", 14.0, 8.00, 1, Modal.TREM,   False),
            ("G", "H",  5.0, 8.00, 0, Modal.TREM,   False),
            # Atalho extra: ônibus direto E → H (mais lento, sem baldeação de trem)
            ("E", "H", 25.0, 5.00, 1, Modal.ONIBUS, False),
            # Atalho extra: ônibus C → F
            ("C", "F", 18.0, 3.80, 0, Modal.ONIBUS, False),
        ]

        for origin, dest, t, fare, tr, modal, bidir in edges:
            g.add_edge_by_params(origin, dest, t, fare, tr, modal, bidir)

        return g

    @staticmethod
    def synthetic_random(
        num_nodes: int,
        avg_degree: int = 4,
        seed: int = 42,
    ) -> Multigraph:
        """
        Gera um multigrafo dirigido aleatório com num_nodes vértices.

        Algoritmo:
          1. Cria vértices v0..v(n-1).
          2. Garante conectividade: encadeia v0→v1→...→v(n-1) (caminho hamiltoniano).
          3. Adiciona (avg_degree - 1) * n arestas extras aleatórias.

        Parâmetros
        ----------
        num_nodes  : int — número de vértices
        avg_degree : int — grau médio de saída desejado
        seed       : int — semente para reprodutibilidade

        Complexidade: O(n * avg_degree)
        """
        # LCG simples para não depender do módulo random
        # x_{i+1} = (a * x_i + c) mod m
        _state = [seed]
        def _rand(lo: float, hi: float) -> float:
            _state[0] = (1664525 * _state[0] + 1013904223) & 0xFFFFFFFF
            t = _state[0] / 0xFFFFFFFF
            return lo + t * (hi - lo)

        def _rand_int(lo: int, hi: int) -> int:
            return int(_rand(lo, hi + 0.9999))

        modals_list = list(Modal.ALL)

        g = Multigraph(f"Sintetico_{num_nodes}nos")

        # Cria vértices
        for i in range(num_nodes):
            g.add_node_by_id(f"v{i}", f"Parada_{i}", [modals_list[i % 3]])

        # Caminho hamiltoniano para garantir conectividade
        for i in range(num_nodes - 1):
            modal = modals_list[i % 3]
            tr    = 1 if modal != modals_list[(i + 1) % 3] else 0
            g.add_edge_by_params(
                f"v{i}", f"v{i+1}",
                travel_time = round(_rand(2.0, 20.0), 1),
                fare        = round(_rand(2.0, 10.0), 2),
                transfer    = tr,
                modal       = modal,
            )

        # Arestas extras aleatórias
        extra = (avg_degree - 1) * num_nodes
        attempts = 0
        added    = 0
        while added < extra and attempts < extra * 5:
            attempts += 1
            u = f"v{_rand_int(0, num_nodes - 1)}"
            v = f"v{_rand_int(0, num_nodes - 1)}"
            if u == v:
                continue
            modal = modals_list[_rand_int(0, 2)]
            g.add_edge_by_params(
                u, v,
                travel_time = round(_rand(2.0, 30.0), 1),
                fare        = round(_rand(2.0, 12.0), 2),
                transfer    = _rand_int(0, 1),
                modal       = modal,
            )
            added += 1

        return g
