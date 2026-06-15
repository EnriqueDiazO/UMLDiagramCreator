from __future__ import annotations

import json
from pathlib import Path
from string import Template

from uml_diagram_creator.analyzer.model import GraphData
from uml_diagram_creator.render.mathmongo_controls import slugify


def render_graph_html(graph: GraphData, output_file: str | Path) -> Path:
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    groups = build_legend_groups(graph)
    html = HTML_TEMPLATE.substitute(
        title=escape_text(f"{graph.name} - UMLDiagramCreator"),
        heading=escape_text(graph.name),
        graph_type=escape_text(graph.graph_type),
        export_slug=json.dumps(slugify(f"{graph.graph_type}_{graph.name}")),
        nodes_json=json.dumps([node.to_vis() for node in graph.nodes], ensure_ascii=False),
        edges_json=json.dumps([edge.to_vis() for edge in graph.edges], ensure_ascii=False),
        groups_json=json.dumps(groups, ensure_ascii=False),
    )
    output.write_text(html, encoding="utf-8")
    return output


def build_legend_groups(graph: GraphData) -> list[dict[str, str]]:
    seen: dict[str, dict[str, str]] = {}
    for node in graph.nodes:
        if node.group not in seen:
            seen[node.group] = {
                "group": node.group,
                "label": node.group,
                "color": node.color or "#e5e7eb",
                "border": node.border_color or "#4b5563",
            }
    return [seen[group] for group in sorted(seen)]


def escape_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


HTML_TEMPLATE = Template(
    r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>$title</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    :root {
      color-scheme: light;
      --panel-bg: rgba(255, 255, 255, 0.94);
      --panel-border: #cbd5e1;
      --text: #111827;
      --muted: #64748b;
      --control: #f8fafc;
      --control-border: #cbd5e1;
      --accent: #2563eb;
    }
    html, body {
      width: 100%;
      height: 100%;
      margin: 0;
      overflow: hidden;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--text);
      background: #f8fafc;
    }
    #mynetwork {
      position: fixed;
      inset: 0;
      width: 100%;
      height: 100vh;
      background:
        linear-gradient(rgba(15, 23, 42, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(15, 23, 42, 0.035) 1px, transparent 1px),
        #f8fafc;
      background-size: 32px 32px;
    }
    .panel {
      position: fixed;
      z-index: 10;
      background: var(--panel-bg);
      border: 1px solid var(--panel-border);
      border-radius: 8px;
      box-shadow: 0 12px 30px rgba(15, 23, 42, 0.16);
      backdrop-filter: blur(8px);
    }
    #left-graph-controls {
      left: 12px;
      top: 54px;
      width: 282px;
      max-height: calc(100vh - 70px);
      overflow: auto;
      padding: 12px;
    }
    #physics-overlay {
      right: 12px;
      top: 12px;
      width: 268px;
      max-height: calc(100vh - 70px);
      overflow: auto;
      padding: 12px;
    }
    .toggle {
      position: fixed;
      z-index: 11;
      top: 12px;
      border: 1px solid var(--control-border);
      background: #ffffff;
      color: var(--text);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 13px;
      cursor: pointer;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
    }
    #toggle-left-controls { left: 12px; }
    #toggle-physics-overlay { right: 304px; }
    #toggle-physics-overlay.panel-hidden { right: 12px; }
    h1 {
      margin: 0 0 8px;
      font-size: 16px;
      line-height: 1.25;
    }
    h2 {
      margin: 14px 0 8px;
      font-size: 12px;
      line-height: 1.2;
      text-transform: uppercase;
      color: #334155;
    }
    label {
      display: block;
      margin: 8px 0 4px;
      font-size: 12px;
      color: #334155;
    }
    select, input, textarea {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid var(--control-border);
      border-radius: 6px;
      background: #ffffff;
      color: var(--text);
      font-size: 13px;
      padding: 7px;
    }
    input[type="range"] {
      padding: 0;
      accent-color: var(--accent);
    }
    textarea {
      min-height: 74px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
    }
    button {
      border: 1px solid var(--control-border);
      border-radius: 6px;
      background: var(--control);
      color: var(--text);
      font-size: 12px;
      padding: 7px 8px;
      cursor: pointer;
    }
    button:hover {
      border-color: #94a3b8;
      background: #eef2f7;
    }
    .button-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
    }
    .button-row {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .button-row button {
      flex: 1 1 120px;
    }
    .legend-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 6px 0;
      font-size: 12px;
    }
    .legend-dot {
      width: 13px;
      height: 13px;
      border-radius: 50%;
      border: 2px solid #64748b;
      flex: 0 0 auto;
    }
    .status {
      min-height: 16px;
      margin-top: 7px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    #node-info {
      margin-top: 8px;
      padding: 8px;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: #ffffff;
      font-size: 12px;
      line-height: 1.4;
      word-break: break-word;
    }
    .value-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: #334155;
    }
    .hidden {
      display: none !important;
    }
    @media (max-width: 820px) {
      #left-graph-controls, #physics-overlay {
        width: calc(100vw - 24px);
        max-height: 42vh;
      }
      #physics-overlay {
        top: auto;
        bottom: 12px;
      }
      #toggle-physics-overlay {
        right: 12px;
      }
    }
  </style>
</head>
<body>
  <div id="mynetwork"></div>

  <button id="toggle-left-controls" class="toggle" type="button" aria-controls="left-graph-controls" aria-expanded="true" onclick="toggleLeftControls()">🎨 Ocultar leyenda</button>
  <button id="toggle-physics-overlay" class="toggle" type="button" aria-controls="physics-overlay" aria-expanded="true" onclick="togglePhysicsOverlay()">⚙️ Ocultar controles</button>

  <aside id="left-graph-controls" class="panel">
    <h1>$heading</h1>
    <label for="nodeIdSelector">Nodo</label>
    <select id="nodeIdSelector" onchange="focusNodeByInput()"></select>
    <input id="nodeSearchInput" type="text" list="nodeSearchList" placeholder="id o nombre" oninput="document.getElementById('nodeIdSelector').value = ''">
    <datalist id="nodeSearchList"></datalist>
    <div class="button-grid" style="margin-top:6px">
      <button type="button" onclick="focusNodeByInput()">🔎 Enfocar nodo</button>
      <button type="button" onclick="showSelectedNeighborhood()">🕸 Mostrar vecinos</button>
      <button type="button" onclick="showSelectedIncoming()">⬅ Mostrar entrantes</button>
      <button type="button" onclick="showSelectedOutgoing()">➡ Mostrar salientes</button>
    </div>
    <label for="nodeTypeSelector">Tipo</label>
    <select id="nodeTypeSelector" onchange="filterByType(this.value)"></select>
    <div class="button-grid" style="margin-top:6px">
      <button type="button" onclick="showSelectedComponent()">🧩 Mostrar componente</button>
      <button type="button" onclick="showSelectedType()">🧲 Mostrar mismo tipo</button>
    </div>
    <div class="button-row" style="margin-top:6px">
      <button type="button" onclick="showAllNodes()">🌐 Mostrar todo</button>
    </div>
    <h2>Leyenda de colores</h2>
    <div id="node-type-legend"></div>
    <h2>Ficha del nodo</h2>
    <div id="node-info">Selecciona un nodo para ver su ficha.</div>
  </aside>

  <aside id="physics-overlay" class="panel">
    <h4>🧲 Physics Controls</h4>
    <p class="physics-note">Ajusta estos controles para separar, compactar o estabilizar el grafo.</p>
    <div class="physics-control" title="Controla la repulsión entre nodos.">
      <label for="grav">Gravitational Constant</label>
      <div class="physics-help">Mas alto separa mas los nodos.</div>
      <input id="grav" type="range" min="0" max="300" value="120" oninput="applyCurrentPhysics()">
    </div>
    <div class="physics-control" title="Atrae los nodos hacia el centro.">
      <label for="central">Central Gravity</label>
      <div class="physics-help">Mas alto compacta el grafo.</div>
      <input id="central" type="range" min="0" max="10" value="1" oninput="applyCurrentPhysics()">
    </div>
    <div class="physics-control" title="Define la longitud ideal de las flechas.">
      <label for="springLen">Spring Length</label>
      <div class="physics-help">Mas alto alarga las flechas.</div>
      <input id="springLen" type="range" min="50" max="450" value="260" oninput="applyCurrentPhysics()">
    </div>
    <div class="physics-control" title="Controla la rigidez de las conexiones.">
      <label for="springConst">Spring Constant</label>
      <div class="physics-help">Mas alto tira mas fuerte de los nodos.</div>
      <input id="springConst" type="range" min="10" max="200" value="40" oninput="applyCurrentPhysics()">
    </div>
    <div class="physics-control" title="Reduce la velocidad del movimiento.">
      <label for="damping">Damping</label>
      <div class="physics-help">Mas alto estabiliza mas rapido.</div>
      <input id="damping" type="range" min="0" max="100" value="20" oninput="applyCurrentPhysics()">
    </div>
    <div class="physics-control" title="Limita la velocidad maxima de movimiento.">
      <label for="maxVel">Max Velocity</label>
      <div class="physics-help">Tope de velocidad de los nodos.</div>
      <input id="maxVel" type="range" min="10" max="100" value="50" oninput="applyCurrentPhysics()">
    </div>
    <div class="physics-control" title="Define cuando la simulacion se considera estable.">
      <label for="minVel">Min Velocity</label>
      <div class="physics-help">Umbral minimo antes de estabilizar.</div>
      <input id="minVel" type="range" min="0" max="50" value="10" oninput="applyCurrentPhysics()">
    </div>
    <div class="physics-control" title="Controla el tamano del paso de simulacion.">
      <label for="timestep">Timestep</label>
      <div class="physics-help">Mas alto mueve mas rapido; puede inestabilizar.</div>
      <input id="timestep" type="range" min="10" max="100" value="35" oninput="applyCurrentPhysics()">
    </div>

    <button onclick="enablePhysics()">▶ Activar física</button>
    <button onclick="freezePhysics()">📌 Congelar posiciones</button>
    <button onclick="resetPhysics()">♻ Resetear física</button>

    <div class="layout-section">
      <div class="layout-title">Herramientas de organización</div>
      <div class="layout-tip">Tip: Ctrl/Shift + click selecciona varios nodos; vis-network no incluye selección por caja aquí.</div>
      <button onclick="fixSelectedNodes()">📌 Fijar nodos seleccionados</button>
      <button onclick="releaseSelectedNodes()">🔓 Liberar nodos seleccionados</button>
      <button onclick="separateByType()">🧲 Separar por tipo</button>
      <button onclick="separateBySource()">🧭 Separar por fuente</button>
      <button onclick="separateByComponent()">🧩 Separar componentes</button>
      <button onclick="resetPositions()">♻ Resetear posiciones</button>
      <div id="layout-status" class="status"></div>
    </div>

    <div class="layout-section">
      <div class="layout-title">Controles de enlaces</div>
      <div class="layout-tip">Endereza o suaviza flechas sin mover nodos. El ajuste es global; vis-network no edita puntos intermedios manualmente aquí.</div>
      <label for="edgeStyle">Estilo de enlaces</label>
      <select id="edgeStyle" onchange="applyEdgeStyle()">
        <option value="straight">Rectos</option>
        <option value="soft">Suaves</option>
        <option value="curved">Curvos</option>
        <option value="dynamic" selected>Dinamicos</option>
      </select>
      <div class="value-row">
        <label for="edgeRoundness">Curvatura de enlaces</label>
        <span id="edgeRoundnessValue">0.15</span>
      </div>
      <div class="physics-help">Valores bajos hacen las flechas mas rectas; valores altos separan flechas paralelas.</div>
      <input id="edgeRoundness" type="range" min="0" max="60" value="15" oninput="applyEdgeStyle()">
      <button onclick="straightenEdges()">↔ Enderezar enlaces</button>
      <button onclick="recalculateEdges()">🔁 Recalcular enlaces</button>
      <button onclick="alignEdgeLabels()">📐 Alinear etiquetas</button>
      <div id="edge-status" class="status"></div>
    </div>

    <div class="layout-section">
      <div class="layout-title">Tamaño de texto</div>
      <div class="value-row">
        <label for="edgeLabelSize">Etiquetas de enlaces</label>
        <span id="edgeLabelSizeValue">13</span>
      </div>
      <input id="edgeLabelSize" type="range" min="8" max="100" value="13" oninput="applyTextSizes()">
      <div class="value-row">
        <label for="nodeLabelSize">Nombres de nodos</label>
        <span id="nodeLabelSizeValue">18</span>
      </div>
      <input id="nodeLabelSize" type="range" min="10" max="100" value="18" oninput="applyTextSizes()">
    </div>

    <div class="layout-section">
      <div class="layout-title">Exportar estado</div>
      <div class="layout-tip">Guarda posiciones, nodos fijados, física, estilos, selección y vista filtrada.</div>
      <button onclick="downloadCurrentGraphHtml()">💾 Descargar grafo actual</button>
      <button onclick="copyGraphStateJson()">📋 Copiar estado JSON</button>
      <button onclick="downloadGraphStateJson()">📥 Descargar estado JSON</button>
      <button onclick="restoreStateFromInput()">Restaurar estado</button>
      <textarea id="restoreStateInput" placeholder="Pega aqui un estado JSON"></textarea>
      <div id="download-status" class="status"></div>
    </div>
  </aside>

  <script>
    const GRAPH_TYPE = "$graph_type";
    const GRAPH_EXPORT_BASENAME = $export_slug;
    const ORIGINAL_NODES = $nodes_json;
    const ORIGINAL_EDGES = $edges_json;
    const LEGEND_GROUPS = $groups_json;
    const DEFAULT_PHYSICS = {
      grav: 120,
      central: 1,
      springLen: 260,
      springConst: 40,
      damping: 20,
      maxVel: 50,
      minVel: 10,
      timestep: 35
    };
    const DEFAULT_OPTIONS = {
      autoResize: true,
      layout: { improvedLayout: true },
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
      },
      physics: {
        enabled: true,
        solver: "forceAtlas2Based",
        forceAtlas2Based: {
          gravitationalConstant: -120,
          centralGravity: 0.01,
          springLength: 260,
          springConstant: 0.04,
          avoidOverlap: 0.8
        },
        damping: 0.2,
        maxVelocity: 50,
        minVelocity: 0.1,
        timestep: 0.35,
        stabilization: { enabled: false }
      },
      nodes: {
        borderWidth: 1,
        shadow: true,
        font: { size: 18, face: "Arial", color: "#334155", multi: false }
      },
      edges: {
        arrows: { to: { enabled: true, scaleFactor: 0.75 } },
        length: 260,
        smooth: { enabled: true, type: "dynamic", roundness: 0.15 },
        font: { size: 13, align: "middle", color: "#111827", strokeWidth: 4, strokeColor: "#ffffff" }
      }
    };

    let nodes = new vis.DataSet(cloneItems(ORIGINAL_NODES));
    let edges = new vis.DataSet(cloneItems(ORIGINAL_EDGES));
    let allNodes = mapById(cloneItems(ORIGINAL_NODES));
    let allEdges = mapEdges(cloneItems(ORIGINAL_EDGES));
    let visibleNodeIds = null;
    let visibleEdgeIds = null;
    let graphUiState = {
      leftVisible: true,
      rightVisible: true,
      edgeStyle: "dynamic",
      edgeRoundness: 0.15,
      nodeTextSize: 18,
      edgeTextSize: 13,
      physics: { mode: "active", enabled: true },
      ui: { leftControlsVisible: true, physicsOverlayVisible: true }
    };

    const network = new vis.Network(document.getElementById("mynetwork"), { nodes, edges }, DEFAULT_OPTIONS);
    window.mmNetwork = network;
    window.network = network;

    network.on("selectNode", function(params) {
      const id = params.nodes && params.nodes.length ? params.nodes[params.nodes.length - 1] : "";
      syncNodeInputs(id);
      updateNodeInfo(id);
    });
    network.on("deselectNode", function() {
      updateNodeInfo(null);
    });
    network.once("afterDrawing", function() {
      populateControls();
      applyTextSizes();
    });

    document.addEventListener("DOMContentLoaded", function() {
      populateControls();
      if (window.EXPORTED_GRAPH_STATE) {
        restoreGraphState(window.EXPORTED_GRAPH_STATE);
      }
    });

    function cloneItems(items) {
      return items.map(function(item) { return JSON.parse(JSON.stringify(item)); });
    }

    function mapById(items) {
      const out = {};
      items.forEach(function(item) { out[item.id] = item; });
      return out;
    }

    function edgeKey(edge) {
      return edge.id || (edge.from + "::" + edge.relation + "::" + edge.to);
    }

    function mapEdges(items) {
      const out = {};
      items.forEach(function(edge) { out[edgeKey(edge)] = edge; });
      return out;
    }

    function escapeHtml(value) {
      return String(value == null ? "" : value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function populateControls() {
      populateNodeSelect();
      populateNodeSearchList();
      populateGroupSelects();
      renderLegend();
    }

    function populateNodeSelect() {
      const select = document.getElementById("nodeIdSelector");
      if (!select) return;
      const current = select.value;
      const ids = Object.keys(allNodes).sort();
      select.innerHTML = '<option value="">Seleccionar nodo</option>' + ids.map(function(id) {
        const label = allNodes[id].label && allNodes[id].label !== id ? allNodes[id].label + " (" + id + ")" : id;
        return '<option value="' + escapeHtml(id) + '">' + escapeHtml(label) + '</option>';
      }).join("");
      select.value = current && allNodes[current] ? current : "";
    }

    function populateNodeSearchList() {
      const datalist = document.getElementById("nodeSearchList");
      if (!datalist) return;
      datalist.innerHTML = Object.keys(allNodes).sort().map(function(id) {
        return '<option value="' + escapeHtml(id) + '"></option>';
      }).join("");
    }

    function populateGroupSelects() {
      const groups = LEGEND_GROUPS.map(function(item) { return item.group; }).sort();
      ["nodeTypeSelector"].forEach(function(id) {
        const select = document.getElementById(id);
        if (!select) return;
        const current = select.value;
        select.innerHTML = '<option value="">Todos los tipos</option>' + groups.map(function(group) {
          return '<option value="' + escapeHtml(group) + '">' + escapeHtml(group) + '</option>';
        }).join("");
        select.value = groups.indexOf(current) >= 0 ? current : "";
      });
    }

    function renderLegend() {
      const legend = document.getElementById("node-type-legend");
      if (!legend) return;
      legend.innerHTML = LEGEND_GROUPS.map(function(item) {
        return '<button class="legend-row" type="button" data-group="' + escapeHtml(item.group) + '" onclick="filterByType(this.dataset.group)"><span class="legend-dot" style="background:' +
          escapeHtml(item.color) + ';border-color:' + escapeHtml(item.border) + '"></span><span>' +
          escapeHtml(item.label) + '</span></button>';
      }).join("");
    }

    function isLeftControlsVisible() {
      return graphUiState.ui.leftControlsVisible !== false;
    }

    function setLeftControlsVisible(visible) {
      const resolvedVisible = Boolean(visible);
      graphUiState.leftVisible = resolvedVisible;
      graphUiState.ui.leftControlsVisible = resolvedVisible;
      const panel = document.getElementById("left-graph-controls");
      const button = document.getElementById("toggle-left-controls");
      if (panel) panel.classList.toggle("hidden", !resolvedVisible);
      if (button) {
        button.textContent = resolvedVisible ? "🎨 Ocultar leyenda" : "🎨 Mostrar leyenda";
        button.setAttribute("aria-expanded", String(resolvedVisible));
      }
      if (window.mmNetwork) window.mmNetwork.redraw();
    }

    function toggleLeftControls() {
      setLeftControlsVisible(!isLeftControlsVisible());
    }

    function isPhysicsOverlayVisible() {
      return graphUiState.ui.physicsOverlayVisible !== false;
    }

    function setPhysicsOverlayVisible(visible) {
      const resolvedVisible = Boolean(visible);
      graphUiState.rightVisible = resolvedVisible;
      graphUiState.ui.physicsOverlayVisible = resolvedVisible;
      const panel = document.getElementById("physics-overlay");
      const button = document.getElementById("toggle-physics-overlay");
      if (panel) panel.classList.toggle("hidden", !resolvedVisible);
      if (button) {
        button.textContent = resolvedVisible ? "⚙️ Ocultar controles" : "⚙️ Mostrar controles";
        button.setAttribute("aria-expanded", String(resolvedVisible));
        button.classList.toggle("panel-hidden", !resolvedVisible);
      }
    }

    function togglePhysicsOverlay() {
      setPhysicsOverlayVisible(!isPhysicsOverlayVisible());
    }

    function syncNodeInputs(id) {
      const select = document.getElementById("nodeIdSelector");
      const input = document.getElementById("nodeSearchInput");
      if (select) select.value = id || "";
      if (input) input.value = id || "";
    }

    function selectNodeFromControl(id) {
      if (!id) return;
      showAllNodes(false);
      network.selectNodes([id], false);
      network.focus(id, { scale: 1.2, animation: true });
      syncNodeInputs(id);
      updateNodeInfo(id);
    }

    function selectedOrInputNodeId() {
      const input = document.getElementById("nodeSearchInput");
      const typed = input ? input.value.trim() : "";
      if (typed && allNodes[typed]) return typed;
      const selected = network.getSelectedNodes();
      if (selected.length) return selected[0];
      const select = document.getElementById("nodeIdSelector");
      return select && select.value ? select.value : "";
    }

    function setStatus(message) {
      const status = document.getElementById("layout-status");
      if (status) status.textContent = message || "";
    }

    function setDownloadStatus(message) {
      const status = document.getElementById("download-status");
      if (status) status.textContent = message || "";
    }

    function setLayoutStatus(message) {
      setStatus(message);
    }

    function graphNodes() {
      if (!window.mmNetwork || !window.mmNetwork.body || !window.mmNetwork.body.data) return null;
      return window.mmNetwork.body.data.nodes;
    }

    function graphEdges() {
      if (!window.mmNetwork || !window.mmNetwork.body || !window.mmNetwork.body.data) return null;
      return window.mmNetwork.body.data.edges;
    }

    function selectedNodeIds() {
      if (!window.mmNetwork) return [];
      return window.mmNetwork.getSelectedNodes();
    }

    function currentPositionUpdates(nodeIds, fixedValue) {
      const positions = window.mmNetwork.getPositions(nodeIds);
      return nodeIds.map((nodeId) => ({
        id: nodeId,
        x: positions[nodeId]?.x,
        y: positions[nodeId]?.y,
        fixed: { x: fixedValue, y: fixedValue }
      }));
    }

    function physicsValue(id) {
      const input = document.getElementById(id);
      return input ? Number(input.value) : DEFAULT_PHYSICS[id];
    }

    function physicsControlState(mode = graphUiState.physics.mode, enabled = graphUiState.physics.enabled) {
      return {
        mode,
        enabled,
        gravitationalConstant: physicsValue("grav"),
        centralGravity: physicsValue("central"),
        springLength: physicsValue("springLen"),
        springConstant: physicsValue("springConst"),
        damping: physicsValue("damping"),
        maxVelocity: physicsValue("maxVel"),
        minVelocity: physicsValue("minVel"),
        timestep: physicsValue("timestep")
      };
    }

    function setPhysicsState(mode, enabled) {
      graphUiState.physics = physicsControlState(mode, enabled);
    }

    function currentPhysicsOptions(enabled) {
      return {
        enabled: enabled,
        solver: "forceAtlas2Based",
        forceAtlas2Based: {
          gravitationalConstant: -physicsValue("grav"),
          centralGravity: physicsValue("central") / 100,
          springLength: physicsValue("springLen"),
          springConstant: physicsValue("springConst") / 1000,
          avoidOverlap: 0.8
        },
        damping: physicsValue("damping") / 100,
        maxVelocity: physicsValue("maxVel"),
        minVelocity: physicsValue("minVel") / 100,
        timestep: physicsValue("timestep") / 100,
        stabilization: { enabled: false }
      };
    }

    function applyCurrentPhysics() {
      network.setOptions({ physics: currentPhysicsOptions(true) });
      network.startSimulation();
      setPhysicsState("active", true);
    }

    function enablePhysics() {
      applyCurrentPhysics();
      setStatus("Fisica activada.");
    }

    function stopMotion() {
      network.stopSimulation();
      network.setOptions({ physics: { enabled: false } });
      setPhysicsState("paused", false);
      setStatus("Movimiento pausado.");
    }

    function freezePhysics() {
      window.mmNetwork.stopSimulation();
      window.mmNetwork.setOptions({ physics: { enabled: false } });
      setPhysicsState("frozen", false);
      setStatus("Posiciones congeladas.");
    }

    function resetPhysics() {
      Object.keys(DEFAULT_PHYSICS).forEach(function(id) {
        const input = document.getElementById(id);
        if (input) input.value = DEFAULT_PHYSICS[id];
      });
      applyCurrentPhysics();
      setStatus("Fisica reiniciada.");
    }

    function fixSelectedNodes() {
      const graphDataNodes = graphNodes();
      const selected = selectedNodeIds();
      if (!graphDataNodes || selected.length === 0) {
        setLayoutStatus("Selecciona nodos primero.");
        return;
      }
      graphDataNodes.update(currentPositionUpdates(selected, true));
      setLayoutStatus("Nodos fijados: " + selected.length);
    }

    function releaseSelectedNodes() {
      const graphDataNodes = graphNodes();
      const selected = selectedNodeIds();
      if (!graphDataNodes || selected.length === 0) {
        setLayoutStatus("Selecciona nodos primero.");
        return;
      }
      graphDataNodes.update(currentPositionUpdates(selected, false));
      setLayoutStatus("Nodos liberados: " + selected.length);
      applyCurrentPhysics();
    }

    function groupValue(node, field) {
      if (field === "module") return node.module || "external";
      if (field === "component") return node.component || "component";
      return node.group || node.kind || "node";
    }

    function separateBy(field) {
      const current = nodes.get();
      const groups = {};
      current.forEach(function(node) {
        const key = groupValue(node, field);
        if (!groups[key]) groups[key] = [];
        groups[key].push(node);
      });
      const keys = Object.keys(groups).sort();
      const updates = [];
      keys.forEach(function(key, groupIndex) {
        const group = groups[key].sort(function(a, b) { return String(a.id).localeCompare(String(b.id)); });
        const cols = Math.max(1, Math.ceil(Math.sqrt(group.length)));
        const centerX = (groupIndex - (keys.length - 1) / 2) * 560;
        group.forEach(function(node, i) {
          const col = i % cols;
          const row = Math.floor(i / cols);
          updates.push({
            id: node.id,
            x: centerX + (col - (cols - 1) / 2) * 170,
            y: row * 130,
            fixed: { x: false, y: false }
          });
        });
      });
      nodes.update(updates);
      network.setOptions({ physics: currentPhysicsOptions(true) });
      network.fit({ animation: true });
      setStatus("Separado por " + field + ".");
    }

    function separateByType() {
      separateBy("group");
      setLayoutStatus("Separado por tipo de concepto.");
    }

    function separateBySource() {
      separateBy("module");
      setLayoutStatus("Separado por fuente.");
    }

    function separateByComponent() {
      separateBy("component");
      setLayoutStatus("Separado por componente conexa.");
    }

    function resetPositions() {
      separateByType();
      setLayoutStatus("Posiciones reiniciadas por tipo.");
    }

    function applyEdgeStyle() {
      const style = document.getElementById("edgeStyle").value;
      const roundness = Number(document.getElementById("edgeRoundness").value || 15) / 100;
      graphUiState.edgeStyle = style;
      graphUiState.edgeRoundness = roundness;
      document.getElementById("edgeRoundnessValue").textContent = roundness.toFixed(2);
      let smooth = false;
      if (style === "soft") {
        smooth = { enabled: true, type: "continuous", roundness: roundness };
      } else if (style === "curved") {
        smooth = { enabled: true, type: "curvedCW", roundness: roundness };
      } else if (style !== "straight") {
        smooth = { enabled: true, type: "dynamic", roundness: roundness };
      }
      stopMotion();
      network.setOptions({ edges: { smooth: smooth } });
      network.redraw();
      const edgeStatus = document.getElementById("edge-status");
      if (edgeStatus) edgeStatus.textContent = "Enlaces recalculados sin mover nodos.";
    }

    function straightenEdges() {
      const select = document.getElementById("edgeStyle");
      const roundness = document.getElementById("edgeRoundness");
      if (select) select.value = "straight";
      if (roundness) roundness.value = 0;
      applyEdgeStyle();
      const edgeStatus = document.getElementById("edge-status");
      if (edgeStatus) edgeStatus.textContent = "Enlaces enderezados sin mover nodos.";
    }

    function recalculateEdges() {
      applyEdgeStyle();
      const edgeStatus = document.getElementById("edge-status");
      if (edgeStatus) edgeStatus.textContent = "Geometria de enlaces recalculada sin mover nodos.";
    }

    function alignEdgeLabels() {
      applyEdgeStyle();
      const edgeStatus = document.getElementById("edge-status");
      if (edgeStatus) edgeStatus.textContent = "Etiquetas alineadas; los colores por relacion se conservan.";
    }

    function applyTextSizes() {
      const nodeSize = Number(document.getElementById("nodeLabelSize").value || 18);
      const edgeSize = Number(document.getElementById("edgeLabelSize").value || 13);
      graphUiState.nodeTextSize = nodeSize;
      graphUiState.edgeTextSize = edgeSize;
      document.getElementById("nodeLabelSizeValue").textContent = String(nodeSize);
      document.getElementById("edgeLabelSizeValue").textContent = String(edgeSize);
      network.setOptions({
        nodes: { font: { size: nodeSize, face: "Arial", color: "#334155" } },
        edges: { font: { size: edgeSize, align: "middle", color: "#111827", strokeWidth: 4, strokeColor: "#ffffff" } }
      });
    }

    function filterByGroup(group) {
      syncGroupControls(group);
      if (!group) {
        showAllNodes(true, { preserveTypeSelector: true });
        return;
      }
      const ids = Object.keys(allNodes).filter(function(id) { return allNodes[id].group === group; });
      renderSubset(ids, edgeIdsForNodes(ids), "Grupo " + group + ": " + ids.length + " nodos.");
    }

    function filterByType(type) {
      filterByGroup(type);
    }

    function syncGroupControls(group) {
      ["nodeTypeSelector"].forEach(function(id) {
        const select = document.getElementById(id);
        if (select) select.value = group || "";
      });
    }

    function edgeIdsForNodes(ids) {
      const visible = new Set(ids);
      return Object.keys(allEdges).filter(function(key) {
        const edge = allEdges[key];
        return visible.has(edge.from) && visible.has(edge.to);
      });
    }

    function renderSubset(ids, edgeIds, message) {
      const idSet = new Set(ids);
      const edgeSet = new Set(edgeIds);
      stopMotion();
      nodes.clear();
      edges.clear();
      nodes.add(ids.filter(function(id) { return allNodes[id]; }).map(function(id) { return JSON.parse(JSON.stringify(allNodes[id])); }));
      edges.add(Object.keys(allEdges).filter(function(key) { return edgeSet.has(key); }).map(function(key) {
        return JSON.parse(JSON.stringify(allEdges[key]));
      }));
      visibleNodeIds = Array.from(idSet);
      visibleEdgeIds = Array.from(edgeSet);
      applyTextSizes();
      network.fit({ animation: true });
      stopMotion();
      setStatus(message);
    }

    function showAllNodes(fit = true, options = {}) {
      stopMotion();
      nodes.clear();
      edges.clear();
      nodes.add(cloneItems(ORIGINAL_NODES));
      edges.add(cloneItems(ORIGINAL_EDGES));
      allNodes = mapById(cloneItems(ORIGINAL_NODES));
      allEdges = mapEdges(cloneItems(ORIGINAL_EDGES));
      visibleNodeIds = null;
      visibleEdgeIds = null;
      if (!options.preserveTypeSelector) syncGroupControls("");
      applyTextSizes();
      if (fit !== false) network.fit({ animation: true });
      stopMotion();
      setStatus("Grafo completo visible.");
    }

    function showAll(fit, preserveGroup) {
      showAllNodes(fit, { preserveTypeSelector: preserveGroup });
    }

    function focusNodeByInput() {
      const id = selectedOrInputNodeId();
      if (!id || !allNodes[id]) {
        setStatus("Nodo no encontrado.");
        return;
      }
      focusNodeById(id);
    }

    function focusNodeById(id) {
      if (!id || !allNodes[id]) {
        setStatus("Nodo no encontrado.");
        return;
      }
      if (!nodes.get(id)) showAllNodes(false, { preserveTypeSelector: true });
      stopMotion();
      network.selectNodes([id], false);
      network.focus(id, { scale: 1.25, animation: true });
      syncNodeInputs(id);
      updateNodeInfo(id);
      setStatus("Nodo enfocado: " + id);
    }

    function showSelectedNeighborhood() {
      const id = selectedOrInputNodeId();
      if (!id) return;
      const ids = new Set([id]);
      const edgeIds = [];
      Object.keys(allEdges).forEach(function(key) {
        const edge = allEdges[key];
        if (edge.from === id || edge.to === id) {
          ids.add(edge.from);
          ids.add(edge.to);
          edgeIds.push(key);
        }
      });
      renderSubset(Array.from(ids), edgeIds, "Vecinos de " + id + ": " + ids.size + ".");
      network.selectNodes([id], false);
      updateNodeInfo(id);
    }

    function showSelectedIncoming() {
      const id = selectedOrInputNodeId();
      if (!id) return;
      const ids = new Set([id]);
      const edgeIds = [];
      Object.keys(allEdges).forEach(function(key) {
        const edge = allEdges[key];
        if (edge.to === id) {
          ids.add(edge.from);
          edgeIds.push(key);
        }
      });
      renderSubset(Array.from(ids), edgeIds, "Llamadas entrantes de " + id + ": " + edgeIds.length + ".");
      network.selectNodes([id], false);
      updateNodeInfo(id);
    }

    function showSelectedOutgoing() {
      const id = selectedOrInputNodeId();
      if (!id) return;
      const ids = new Set([id]);
      const edgeIds = [];
      Object.keys(allEdges).forEach(function(key) {
        const edge = allEdges[key];
        if (edge.from === id) {
          ids.add(edge.to);
          edgeIds.push(key);
        }
      });
      renderSubset(Array.from(ids), edgeIds, "Llamadas salientes de " + id + ": " + edgeIds.length + ".");
      network.selectNodes([id], false);
      updateNodeInfo(id);
    }

    function showNodeIncoming(nodeId) {
      syncNodeInputs(nodeId);
      showSelectedIncoming();
    }

    function showNodeOutgoing(nodeId) {
      syncNodeInputs(nodeId);
      showSelectedOutgoing();
    }

    function showSelectedComponent() {
      const id = selectedOrInputNodeId();
      if (!id || !allNodes[id]) return;
      const component = allNodes[id].component;
      const ids = Object.keys(allNodes).filter(function(nodeId) { return allNodes[nodeId].component === component; });
      renderSubset(ids, edgeIdsForNodes(ids), "Componente " + component + ": " + ids.length + " nodos.");
      network.selectNodes([id], false);
      updateNodeInfo(id);
    }

    function showSelectedType() {
      const id = selectedOrInputNodeId();
      if (!id || !allNodes[id]) return;
      const group = allNodes[id].group;
      const ids = Object.keys(allNodes).filter(function(nodeId) { return allNodes[nodeId].group === group; });
      renderSubset(ids, edgeIdsForNodes(ids), "Tipo " + group + ": " + ids.length + " nodos.");
      network.selectNodes([id], false);
      updateNodeInfo(id);
    }

    function showNeighborhood() { showSelectedNeighborhood(); }
    function showIncoming() { showSelectedIncoming(); }
    function showOutgoing() { showSelectedOutgoing(); }
    function showComponent() { showSelectedComponent(); }
    function showSameType() { showSelectedType(); }

    function updateNodeInfo(id) {
      const info = document.getElementById("node-info");
      if (!info) return;
      if (!id || !allNodes[id]) {
        info.textContent = "Selecciona un nodo para ver su ficha.";
        return;
      }
      const node = allNodes[id];
      const meta = node.metadata || {};
      const rows = [
        ["id", node.id],
        ["tipo", node.kind],
        ["grupo", node.group],
        ["modulo", node.module],
        ["archivo", node.file],
        ["linea", node.lineno || ""],
        ["componente", node.component],
        ["grado", node.degree],
        ["in", node.in_degree],
        ["out", node.out_degree],
        ["args", arrayText(meta.args)],
        ["bases", arrayText(meta.bases)],
        ["atributos", arrayText(meta.attributes)],
        ["docstring", meta.docstring || ""]
      ].filter(function(row) { return row[1] !== undefined && row[1] !== null && row[1] !== ""; });
      info.innerHTML = rows.map(function(row) {
        return "<div><strong>" + escapeHtml(row[0]) + ":</strong> " + escapeHtml(row[1]) + "</div>";
      }).join("");
    }

    function arrayText(value) {
      return Array.isArray(value) ? value.join(", ") : (value || "");
    }

    function currentGraphState() {
      const currentIds = nodes.getIds();
      const positions = network.getPositions(currentIds);
      const fullNodes = Object.keys(allNodes).map(function(id) {
        const item = JSON.parse(JSON.stringify(allNodes[id]));
        if (positions[id]) {
          item.x = positions[id].x;
          item.y = positions[id].y;
        }
        const current = nodes.get(id);
        if (current && current.fixed) item.fixed = current.fixed;
        return item;
      });
      return {
        version: 1,
        graphType: GRAPH_TYPE,
        exportedAt: new Date().toISOString(),
        nodes: nodes.get(),
        edges: edges.get(),
        fullNodes: fullNodes,
        fullEdges: Object.keys(allEdges).map(function(key) { return allEdges[key]; }),
        selection: network.getSelectedNodes(),
        visibleNodeIds: visibleNodeIds,
        visibleEdgeIds: visibleEdgeIds,
        ui: graphUiState.ui,
        uiControls: graphUiState.ui,
        physics: physicsControlState(graphUiState.physics.mode, graphUiState.physics.enabled),
        edgeControls: {
          style: document.getElementById("edgeStyle").value,
          roundness: Number(document.getElementById("edgeRoundness").value || 15) / 100
        },
        nodeControls: {
          edgeLabelSize: Number(document.getElementById("edgeLabelSize").value || 13),
          nodeLabelSize: Number(document.getElementById("nodeLabelSize").value || 18)
        }
      };
    }

    function restoreGraphState(state) {
      if (!state || !Array.isArray(state.fullNodes)) {
        setDownloadStatus("Estado invalido.");
        return;
      }
      allNodes = mapById(cloneItems(state.fullNodes));
      allEdges = mapEdges(cloneItems(state.fullEdges || []));
      graphUiState.ui = Object.assign(graphUiState.ui, state.uiControls || state.ui || {});
      if (state.physics) {
        document.getElementById("grav").value = state.physics.gravitationalConstant || 120;
        document.getElementById("central").value = state.physics.centralGravity || 1;
        document.getElementById("springLen").value = state.physics.springLength || 260;
        document.getElementById("springConst").value = state.physics.springConstant || 40;
        document.getElementById("damping").value = state.physics.damping || 20;
        document.getElementById("maxVel").value = state.physics.maxVelocity || 50;
        document.getElementById("minVel").value = state.physics.minVelocity || 10;
        document.getElementById("timestep").value = state.physics.timestep || 35;
        graphUiState.physics = Object.assign(graphUiState.physics, state.physics, { enabled: false, mode: "restored" });
      }
      if (state.edgeControls) {
        document.getElementById("edgeStyle").value = state.edgeControls.style || "dynamic";
        document.getElementById("edgeRoundness").value = Math.round((state.edgeControls.roundness || 0.15) * 100);
      }
      if (state.nodeControls) {
        document.getElementById("edgeLabelSize").value = state.nodeControls.edgeLabelSize || 13;
        document.getElementById("nodeLabelSize").value = state.nodeControls.nodeLabelSize || 18;
      }
      populateControls();
      if (state.visibleNodeIds && state.visibleNodeIds.length) {
        renderSubset(state.visibleNodeIds, state.visibleEdgeIds || edgeIdsForNodes(state.visibleNodeIds), "Estado restaurado.");
      } else {
        renderSubset(Object.keys(allNodes), Object.keys(allEdges), "Estado restaurado.");
      }
      if (Array.isArray(state.selection) && state.selection.length) {
        network.selectNodes(state.selection.filter(function(id) { return Boolean(allNodes[id]); }), false);
      }
      applyTextSizes();
      applyEdgeStyle();
      stopMotion();
      setLeftControlsVisible(graphUiState.ui.leftControlsVisible !== false);
      setPhysicsOverlayVisible(graphUiState.ui.physicsOverlayVisible !== false);
      setDownloadStatus("Estado restaurado.");
    }

    function restoreStateFromInput() {
      const input = document.getElementById("restoreStateInput");
      try {
        restoreGraphState(JSON.parse(input.value));
      } catch (error) {
        setDownloadStatus("No se pudo restaurar JSON: " + error.message);
      }
    }

    function stateJson() {
      return JSON.stringify(currentGraphState(), null, 2);
    }

    function timestamp() {
      return new Date().toISOString().replace(/[:.]/g, "-");
    }

    function downloadBlob(filename, content, type) {
      const blob = new Blob([content], { type: type });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }

    function downloadGraphStateJson() {
      downloadBlob(GRAPH_EXPORT_BASENAME + "_state_" + timestamp() + ".json", stateJson(), "application/json");
      setDownloadStatus("JSON descargado.");
    }

    function copyGraphStateJson() {
      const text = stateJson();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
          setDownloadStatus("JSON copiado.");
        }).catch(function() {
          downloadGraphStateJson();
        });
      } else {
        downloadGraphStateJson();
      }
    }

    function downloadCurrentGraphHtml() {
      const state = currentGraphState();
      const clone = document.documentElement.cloneNode(true);
      clone.querySelectorAll("#exported-state-script").forEach(function(node) { node.remove(); });
      const script = document.createElement("script");
      script.id = "exported-state-script";
      script.textContent = "window.EXPORTED_GRAPH_STATE = " + JSON.stringify(state) + ";";
      clone.querySelector("body").appendChild(script);
      const html = "<!doctype html>\n" + clone.outerHTML;
      downloadBlob(GRAPH_EXPORT_BASENAME + "_current_" + timestamp() + ".html", html, "text/html");
      setDownloadStatus("HTML descargado con estado actual.");
    }

    function downloadCurrentHtml() { downloadCurrentGraphHtml(); }
    function copyStateJson() { copyGraphStateJson(); }
    function downloadStateJson() { downloadGraphStateJson(); }
  </script>
</body>
</html>
"""
)
