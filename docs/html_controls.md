# HTML controls

The generated HTML follows the MathMongo-style interaction pattern from the reference Knowledge Graph: a full-screen graph, a left selector/legend panel, and a right `🧲 Physics Controls` panel.

## Left panel

The left panel contains:

- `nodeIdSelector` for selecting a node;
- `nodeTypeSelector` for filtering by group/type;
- dynamic color legend;
- node card in `node-info`;
- node exploration buttons for focus, neighbors, incoming edges, outgoing edges, component, same type, and full graph.

The legend is generated from groups present in the graph. The `🎨 Ocultar leyenda` / `🎨 Mostrar leyenda` button toggles the whole left panel with `display: none`, so no blank box remains over the graph.

## Right panel

The right panel contains:

- `🧲 Physics Controls`;
- `Herramientas de organización`;
- `Controles de enlaces`;
- `Tamaño de texto`;
- `Exportar estado`.

The visible buttons intentionally match the MathMongo Knowledge Graph:

- `▶ Activar física`;
- `📌 Congelar posiciones`;
- `♻ Resetear física`;
- `📌 Fijar nodos seleccionados`;
- `🔓 Liberar nodos seleccionados`;
- `🧲 Separar por tipo`;
- `🧭 Separar por fuente`;
- `🧩 Separar componentes`;
- `♻ Resetear posiciones`;
- `↔ Enderezar enlaces`;
- `🔁 Recalcular enlaces`;
- `📐 Alinear etiquetas`;
- `💾 Descargar grafo actual`;
- `📋 Copiar estado JSON`;
- `📥 Descargar estado JSON`.

Layouts can separate nodes by:

- group/type;
- module/source;
- connected component.

## Multi-selection

`vis-network` is configured with:

```js
interaction: {
  hover: true,
  navigationButtons: false,
  keyboard: true,
  multiselect: true,
  selectable: true,
  selectConnectedEdges: false,
  dragNodes: true,
  dragView: true,
  zoomView: true
}
```

Use `Ctrl + click` or `Shift + click` to select multiple nodes. The `selectNode` event only updates the node card with the last selected node; it does not call `selectNodes([id])`, so it does not collapse the selection to a single node.

`📌 Fijar nodos seleccionados` calls `fixSelectedNodes()` and fixes every id returned by `selectedNodeIds()`. `🔓 Liberar nodos seleccionados` calls `releaseSelectedNodes()` and releases every selected node before reactivating physics.

`📌 Congelar posiciones` is different: `freezePhysics()` stops the global simulation with `stopSimulation()` and disables physics, but it does not mark every node as fixed.

## Node exploration

The panel supports:

- focus node;
- show neighbors;
- show incoming calls/edges;
- show outgoing calls/edges;
- show component;
- show same type;
- show all.

The node card is filled from node metadata: id, kind, group, module, file, line, component, degree, arguments, bases, attributes, and docstring when available.

## Export and restore

The browser can export:

- current graph state JSON;
- copied JSON through the Clipboard API;
- current HTML with embedded state.

State includes:

- visible nodes and edges;
- full graph nodes and edges;
- selected nodes;
- physics values;
- text and edge controls;
- panel visibility flags.

Restoration can happen by pasting JSON into the restore text area or by opening a downloaded HTML that contains `window.EXPORTED_GRAPH_STATE`.

## Main JavaScript functions

- `filterByGroup(group)`;
- `filterByType(type)`;
- `focusNodeByInput()`;
- `focusNodeById(nodeId)`;
- `showSelectedNeighborhood()`;
- `showSelectedIncoming()`;
- `showSelectedOutgoing()`;
- `showSelectedComponent()`;
- `showSelectedType()`;
- `showAllNodes()`;
- `enablePhysics()`;
- `freezePhysics()`;
- `resetPhysics()`;
- `applyCurrentPhysics()`;
- `selectedNodeIds()`;
- `currentPositionUpdates(nodeIds, fixedValue)`;
- `fixSelectedNodes()`;
- `releaseSelectedNodes()`;
- `separateBy(field)`;
- `separateByType()`;
- `separateBySource()`;
- `separateByComponent()`;
- `applyEdgeStyle()`;
- `straightenEdges()`;
- `recalculateEdges()`;
- `alignEdgeLabels()`;
- `applyTextSizes()`;
- `currentGraphState()`;
- `restoreGraphState(state)`;
- `downloadCurrentGraphHtml()`;
- `copyGraphStateJson()`;
- `downloadGraphStateJson()`.

## Manual verification

1. Run `umlgraph analyze examples/simple_project --graph project --output results/simple_project`.
2. Open `results/simple_project/project_graph.html`.
3. Select several nodes with `Ctrl + click` or `Shift + click`.
4. Click `📌 Fijar nodos seleccionados`.
5. Click `▶ Activar física` and verify that fixed nodes remain still.
6. Select the same nodes and click `🔓 Liberar nodos seleccionados`.
7. Click `▶ Activar física` and verify that released nodes can move.
8. Click `📌 Congelar posiciones` and verify that the whole graph stops.
9. Toggle `🎨 Ocultar leyenda` / `🎨 Mostrar leyenda`.
10. Toggle `⚙️ Ocultar controles` / `⚙️ Mostrar controles`.
11. Export with `💾 Descargar grafo actual` and open the downloaded HTML.

## vis-network compatibility

The renderer uses plain `vis.DataSet` and `vis.Network` objects, stable node ids, stable edge ids, and standard options. Filtering is implemented by replacing the visible `DataSet` contents from preserved full-graph caches.
