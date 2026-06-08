"""
core — Módulo 1: Estruturas de dados e parsing do grafo de transporte.

Exportações públicas:
  - Modal       : constantes de modal de transporte
  - Edge        : aresta dirigida com vetor de custos C(e) = [t, c, tr]
  - Node        : vértice da rede
  - Path        : caminho simples com acumuladores de custo
  - Multigraph  : multigrafo dirigido com lista de adjacência dinâmica
  - GraphFactory: fábrica de grafos sintéticos para testes
"""

from src.core.models import Modal, Edge, Node, Path
from src.core.graph  import Multigraph, GraphFactory

__all__ = [
    "Modal",
    "Edge",
    "Node",
    "Path",
    "Multigraph",
    "GraphFactory",
]
