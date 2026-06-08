"""
models.py — Tipos de dados fundamentais para o grafo de transporte urbano.

Define as estruturas Edge, Node e Path usadas em todo o sistema.
Implementação 100% manual — sem uso de bibliotecas de grafos externas.

Complexidade de memória:
  - Edge  : O(1) por aresta
  - Node  : O(grau(v)) por vértice
  - Path  : O(|P|) por caminho (número de arestas percorridas)
"""

from __future__ import annotations
from typing import Optional


# ---------------------------------------------------------------------------
# Modal de transporte
# ---------------------------------------------------------------------------

class Modal:
    """Constantes para os modais disponíveis na rede multimodal."""
    METRO   = "Metro"
    TREM    = "Trem"
    ONIBUS  = "Onibus"

    ALL = (METRO, TREM, ONIBUS)


# ---------------------------------------------------------------------------
# Aresta (arco dirigido)
# ---------------------------------------------------------------------------

class Edge:
    """
    Representa um arco dirigido (u → v) com vetor de custos C(e) = [t, c, tr].

    Atributos
    ---------
    origin      : str   — identificador do vértice de origem
    destination : str   — identificador do vértice de destino
    travel_time : float — tempo de deslocamento em minutos  [t(e)]
    fare        : float — custo financeiro da passagem em R$ [c(e)]
    transfer    : int   — 1 se exige troca de modal, 0 caso contrário [tr(e)]
    modal       : str   — modal de transporte (Metro / Trem / Onibus)
    edge_id     : str   — identificador único da aresta

    Complexidade
    ------------
    __init__  : O(1)
    __repr__  : O(1)
    """

    def __init__(
        self,
        origin: str,
        destination: str,
        travel_time: float,
        fare: float,
        transfer: int,
        modal: str = Modal.ONIBUS,
        edge_id: Optional[str] = None,
    ) -> None:
        if travel_time < 0:
            raise ValueError(f"travel_time não pode ser negativo: {travel_time}")
        if fare < 0:
            raise ValueError(f"fare não pode ser negativo: {fare}")
        if transfer not in (0, 1):
            raise ValueError(f"transfer deve ser 0 ou 1, recebido: {transfer}")
        if modal not in Modal.ALL:
            raise ValueError(f"modal inválido: {modal}. Use Modal.METRO/TREM/ONIBUS")

        self.origin      : str   = origin
        self.destination : str   = destination
        self.travel_time : float = travel_time
        self.fare        : float = fare
        self.transfer    : int   = transfer
        self.modal       : str   = modal

        # Gera ID automático se não fornecido: "origem->destino@modal"
        self.edge_id: str = edge_id if edge_id else f"{origin}->{destination}@{modal}"

    # ------------------------------------------------------------------
    # Vetor de custo C(e) = [t(e), c(e), tr(e)]
    # ------------------------------------------------------------------

    def cost_vector(self) -> tuple[float, float, int]:
        """Retorna o vetor de custos (travel_time, fare, transfer). O(1)."""
        return (self.travel_time, self.fare, self.transfer)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Edge({self.origin!r} -> {self.destination!r} | "
            f"modal={self.modal} | t={self.travel_time}min | "
            f"R${self.fare:.2f} | tr={self.transfer})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return False
        return self.edge_id == other.edge_id

    def __hash__(self) -> int:
        return hash(self.edge_id)


# ---------------------------------------------------------------------------
# Vértice (nó da rede)
# ---------------------------------------------------------------------------

class Node:
    """
    Representa uma estação/parada no grafo de transporte.

    Atributos
    ---------
    node_id  : str  — identificador único
    name     : str  — nome legível (ex: "Estação Central")
    modals   : list — modais disponíveis neste ponto

    A lista de arestas de saída (adjacência) é mantida pelo Multigraph,
    não pelo Node, para separar responsabilidades.

    Complexidade
    ------------
    __init__ : O(1)
    """

    def __init__(
        self,
        node_id: str,
        name: str,
        modals: Optional[list[str]] = None,
    ) -> None:
        self.node_id : str       = node_id
        self.name    : str       = name
        self.modals  : list[str] = modals if modals else []

    def __repr__(self) -> str:
        return f"Node({self.node_id!r} | {self.name!r} | modals={self.modals})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return False
        return self.node_id == other.node_id

    def __hash__(self) -> int:
        return hash(self.node_id)


# ---------------------------------------------------------------------------
# Caminho (resultado de uma busca)
# ---------------------------------------------------------------------------

class Path:
    """
    Representa um caminho simples P = [e1, e2, ..., ek] no multigrafo.

    Mantém internamente:
      - sequência de arestas percorridas
      - conjunto de vértices visitados (para checagem O(1) de ciclo)
      - acumuladores de custo (tempo, tarifa, transferências)

    Complexidade
    ------------
    __init__       : O(1)
    add_edge       : O(1)  amortizado
    total_time     : O(1)
    total_fare     : O(1)
    total_transfer : O(1)
    nodes          : O(|P|)
    clone          : O(|P|)
    """

    def __init__(self, start: str) -> None:
        """
        Inicializa o caminho a partir do vértice 'start'.

        Parâmetros
        ----------
        start : str — identificador do vértice inicial
        """
        self._edges      : list[Edge]  = []          # arestas na ordem do percurso
        self._visited    : set[str]    = {start}      # vértices já visitados (O(1) lookup)
        self._time       : float       = 0.0          # soma de travel_time
        self._fare       : float       = 0.0          # soma de fare
        self._transfers  : int         = 0            # soma de transfer
        self.start_node  : str         = start

    # ------------------------------------------------------------------
    # Mutação (chamada durante a DFS)
    # ------------------------------------------------------------------

    def add_edge(self, edge: Edge) -> None:
        """
        Adiciona uma aresta ao caminho e atualiza os acumuladores. O(1).

        Lança ValueError se o destino já foi visitado (evita ciclos).
        """
        if edge.destination in self._visited:
            raise ValueError(
                f"Ciclo detectado: '{edge.destination}' já está no caminho."
            )
        self._edges.append(edge)
        self._visited.add(edge.destination)
        self._time      += edge.travel_time
        self._fare      += edge.fare
        self._transfers += edge.transfer

    def remove_last_edge(self) -> Edge:
        """
        Remove a última aresta (backtracking). O(1) amortizado.

        Lança IndexError se o caminho estiver vazio.
        """
        if not self._edges:
            raise IndexError("Tentativa de backtrack em caminho vazio.")
        edge = self._edges.pop()
        self._visited.discard(edge.destination)
        self._time      -= edge.travel_time
        self._fare      -= edge.fare
        self._transfers -= edge.transfer
        return edge

    # ------------------------------------------------------------------
    # Consultas (leitura)
    # ------------------------------------------------------------------

    def current_node(self) -> str:
        """Retorna o vértice atual (última ponta do caminho). O(1)."""
        return self._edges[-1].destination if self._edges else self.start_node

    def has_visited(self, node_id: str) -> bool:
        """Verifica se o vértice já foi visitado. O(1)."""
        return node_id in self._visited

    def total_time(self) -> float:
        """Soma acumulada de travel_time. O(1)."""
        return self._time

    def total_fare(self) -> float:
        """Soma acumulada de fare. O(1)."""
        return self._fare

    def total_transfers(self) -> int:
        """Soma acumulada de transferências. O(1)."""
        return self._transfers

    def edges(self) -> list[Edge]:
        """Retorna cópia da lista de arestas. O(|P|)."""
        return list(self._edges)

    def nodes(self) -> list[str]:
        """
        Retorna a lista ordenada de vértices percorridos (incluindo origem). O(|P|).
        """
        result = [self.start_node]
        for edge in self._edges:
            result.append(edge.destination)
        return result

    def length(self) -> int:
        """Número de arestas no caminho. O(1)."""
        return len(self._edges)

    def clone(self) -> "Path":
        """
        Cria uma cópia independente do caminho. O(|P|).
        Usado pelo motor paralelo para distribuir cópias de estado entre workers.
        """
        new_path = Path(self.start_node)
        new_path._edges     = list(self._edges)
        new_path._visited   = set(self._visited)
        new_path._time      = self._time
        new_path._fare      = self._fare
        new_path._transfers = self._transfers
        return new_path

    # ------------------------------------------------------------------
    # Dominância de Pareto (filtragem de rotas não-dominadas)
    # ------------------------------------------------------------------

    def dominates(self, other: "Path") -> bool:
        """
        Retorna True se este caminho domina 'other' em todos os objetivos:
          - menor ou igual tempo total
          - menor ou igual tarifa total
          - menor ou igual número de transferências
        E estritamente melhor em pelo menos um.

        Complexidade: O(1)
        """
        leq_all = (
            self._time      <= other._time      and
            self._fare      <= other._fare      and
            self._transfers <= other._transfers
        )
        any_better = (
            self._time      < other._time      or
            self._fare      < other._fare      or
            self._transfers < other._transfers
        )
        return leq_all and any_better

    # ------------------------------------------------------------------
    # Representação
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        node_seq = " -> ".join(self.nodes())
        return (
            f"Path[{self.length()} arestas | "
            f"t={self._time:.1f}min | "
            f"R${self._fare:.2f} | "
            f"tr={self._transfers}]: {node_seq}"
        )
