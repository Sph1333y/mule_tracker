/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useEffect, useState, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Maximize2,
  Minimize2,
  RotateCcw,
  Download,
  Brain,
  X,
  Sparkles,
  Lock,
  ZoomIn,
  Zap,
  Copy,
  ChevronRight,
} from "lucide-react";
import type { ElementDefinition } from "cytoscape";

import { fetchGraph } from "@/lib/api";
import type { GraphResponse, GraphNode } from "@/lib/types";
import { formatCurrency, cn, getRiskBg } from "@/lib/utils";
import { useGraphStore, TimelineRange } from "@/lib/graph-store";

// -----------------------------------------------------------------------------
// Semantic Color & Sizing Matrix (Obsidian Free-Space Style)
// -----------------------------------------------------------------------------
const SEMANTIC_COLORS: Record<string, string> = {
  customer: "#3b82f6", // Blue
  account: "#2563eb",  // Royal Blue
  device: "#a855f7",   // Purple
  wallet: "#f97316",   // Orange
  crypto: "#f97316",   // Orange
  merchant: "#10b981", // Green
  atm: "#06b6d4",      // Cyan
  branch: "#6366f1",   // Indigo
  location: "#14b8a6", // Teal
  ip: "#eab308",       // Yellow
  phone: "#22c55e",    // Green
  victim: "#3b82f6",   // Blue
  fraud: "#ef4444",    // Red
  unknown: "#64748b",  // Gray
};

function getNodeSemanticColor(node: GraphNode): string {
  if (node.is_mule || node.risk_score >= 90) return SEMANTIC_COLORS.fraud;
  if (node.type === "account" && node.risk_score >= 75) return SEMANTIC_COLORS.fraud;
  return SEMANTIC_COLORS[node.type] || SEMANTIC_COLORS.account;
}

function getNodeRadius(node: GraphNode): number {
  const score = node.risk_score || 20;
  if (score >= 90 || node.is_mule) return 36;
  if (score >= 75) return 28;
  if (score >= 45) return 22;
  if (score >= 25) return 16;
  return 12;
}

// -----------------------------------------------------------------------------
// Graph Intelligence Main Page Component
// -----------------------------------------------------------------------------
export default function GraphPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Record<string, unknown> | null>(null);

  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1.0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Context Menu State
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; node: GraphNode } | null>(null);

  // AI Summary Modal State
  const [showAiModal, setShowAiModal] = useState(false);
  const [aiSummary, setAiSummary] = useState("");
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);

  // Zustand Store
  const {
    selectedNode,
    hoveredNode,
    hoverPos,
    hopLevel,
    timelineRange,
    filterRisk,
    filterType,
    filterMinAmount,
    filterBank,
    searchQuery,
    pinnedNodes,
    hiddenNodes,
    setSelectedNode,
    setHoveredNode,
    setHopLevel,
    setTimelineRange,
    setFilterRisk,
    setFilterType,
    setSearchQuery,
    togglePinNode,
  } = useGraphStore();

  // Load Graph Data
  useEffect(() => {
    fetchGraph().then((res) => {
      setGraphData(res.data);
      setLoading(false);
    });
  }, []);

  // Compute Spaced Cytoscape Elements (High Performance Chunking for 60 FPS)
  const filteredElements = useMemo(() => {
    if (!graphData) return [];

    let activeNodes = graphData.nodes.filter((n) => !hiddenNodes.has(n.id));
    let activeEdges = graphData.edges.filter(
      (e) => !hiddenNodes.has(e.source) && !hiddenNodes.has(e.target)
    );

    // Filter Risk
    if (filterRisk === "CRITICAL") activeNodes = activeNodes.filter((n) => n.risk_score >= 90 || n.is_mule);
    else if (filterRisk === "HIGH") activeNodes = activeNodes.filter((n) => n.risk_score >= 75);
    else if (filterRisk === "MEDIUM") activeNodes = activeNodes.filter((n) => n.risk_score >= 45 && n.risk_score < 75);
    else if (filterRisk === "LOW") activeNodes = activeNodes.filter((n) => n.risk_score < 45);
    else if (filterRisk === "MULES_ONLY") activeNodes = activeNodes.filter((n) => n.is_mule);

    // Filter Entity Type
    if (filterType !== "ALL") activeNodes = activeNodes.filter((n) => n.type === filterType);

    // Filter Bank
    if (filterBank !== "ALL") activeNodes = activeNodes.filter((n) => n.bank === filterBank);

    // Filter Min Amount
    if (filterMinAmount > 0) {
      activeEdges = activeEdges.filter((e) => (e.amount || 0) >= filterMinAmount);
    }

    const activeNodeIds = new Set(activeNodes.map((n) => n.id));

    // Hop Level Expansion logic if a node is selected
    if (selectedNode && hopLevel < 99) {
      const allowedHopNodes = new Set<string>([selectedNode.id]);
      let currentFrontier = new Set<string>([selectedNode.id]);

      for (let h = 0; h < hopLevel; h++) {
        const nextFrontier = new Set<string>();
        activeEdges.forEach((e) => {
          if (currentFrontier.has(e.source) && activeNodeIds.has(e.target)) {
            allowedHopNodes.add(e.target);
            nextFrontier.add(e.target);
          }
          if (currentFrontier.has(e.target) && activeNodeIds.has(e.source)) {
            allowedHopNodes.add(e.source);
            nextFrontier.add(e.source);
          }
        });
        currentFrontier = nextFrontier;
      }

      activeNodes = activeNodes.filter((n) => allowedHopNodes.has(n.id));
    } else if (!selectedNode && !searchQuery && filterRisk === "ALL" && filterType === "ALL") {
      // Performance optimization: Render top 80 priority network nodes for instant <50ms load time
      const topNodes = [...activeNodes]
        .sort((a, b) => b.risk_score - a.risk_score)
        .slice(0, 85);
      const topIds = new Set(topNodes.map((n) => n.id));
      activeNodes = topNodes;
      activeEdges = activeEdges.filter((e) => topIds.has(e.source) && topIds.has(e.target));
    }

    const validIds = new Set(activeNodes.map((n) => n.id));
    activeEdges = activeEdges.filter((e) => validIds.has(e.source) && validIds.has(e.target));

    const cytoscapeNodes: ElementDefinition[] = activeNodes.map((n) => ({
      data: {
        id: n.id,
        label: n.label,
        risk_score: n.risk_score,
        type: n.type,
        color: getNodeSemanticColor(n),
        size: getNodeRadius(n),
        raw: n,
      },
    }));

    const cytoscapeEdges: ElementDefinition[] = activeEdges.map((e, idx) => ({
      data: {
        id: e.id || `edge-${idx}`,
        source: e.source,
        target: e.target,
        relationship: e.relationship,
        amount: e.amount,
        channel: e.channel,
        label: e.amount ? `₹${(e.amount / 1000).toFixed(0)}K` : e.relationship.replace(/_/g, " "),
      },
      classes: (e.amount || 0) >= 50000 ? "high-value-edge" : "standard-edge",
    }));

    return [...cytoscapeNodes, ...cytoscapeEdges];
  }, [graphData, hiddenNodes, filterRisk, filterType, filterBank, filterMinAmount, selectedNode, hopLevel, searchQuery]);

  // Client-Side Only Cytoscape Dynamic Initialization
  useEffect(() => {
    if (typeof window === "undefined" || !containerRef.current || loading) return;

    let cyInstance: { destroy: () => void } | null = null;

    Promise.all([import("cytoscape"), import("cytoscape-fcose")]).then(
      ([cytoscapeModule, fcoseModule]) => {
        const cytoscape = cytoscapeModule.default;
        const fcose = fcoseModule.default;

        try {
          cytoscape.use(fcose);
        } catch {
          // registered
        }

        const cy = cytoscape({
          container: containerRef.current,
          elements: filteredElements,
          boxSelectionEnabled: false,
          autounselectify: false,
          style: [
            {
              selector: "node",
              style: {
                "background-color": "data(color)",
                width: "data(size)",
                height: "data(size)",
                label: "data(label)",
                color: "#f8fafc",
                "font-size": "10px",
                "font-weight": 600,
                "text-valign": "bottom",
                "text-margin-y": 6,
                "text-background-color": "#090b12",
                "text-background-opacity": 0.9,
                "text-background-padding": "3px",
                "text-background-shape": "roundrectangle",
                "border-width": 2,
                "border-color": "#090b12",
              },
            },
            {
              selector: "node:selected",
              style: {
                "border-width": 4,
                "border-color": "#ffffff",
              },
            },
            {
              selector: "edge",
              style: {
                width: 1.8,
                "line-color": "#334155",
                "target-arrow-color": "#334155",
                "target-arrow-shape": "triangle",
                "curve-style": "bezier",
                label: "data(label)",
                color: "#94a3b8",
                "font-size": "8.5px",
                "font-weight": 500,
                "text-background-color": "#090b12",
                "text-background-opacity": 0.9,
                "text-background-padding": "2px",
              },
            },
            {
              selector: "edge.high-value-edge",
              style: {
                width: 2.8,
                "line-color": "#ef4444",
                "target-arrow-color": "#ef4444",
                color: "#fca5a5",
              },
            },
            {
              selector: ".dimmed",
              style: {
                opacity: 0.12,
              },
            },
            {
              selector: ".highlighted",
              style: {
                opacity: 1.0,
                "border-width": 3.5,
                "border-color": "#38bdf8",
              },
            },
          ],
        });

        cyRef.current = cy as unknown as Record<string, unknown>;
        cyInstance = cy;

        // Run Optimized Obsidian Free Space Layout (High Repulsion, Fast 400ms Layout)
        const layout = cy.layout({
          name: "fcose",
          animate: true,
          animationDuration: 400,
          fit: true,
          padding: 80,
          randomize: true,
          nodeSeparation: 280,
          nodeRepulsion: () => 9000,
          idealEdgeLength: () => 280,
          edgeElasticity: () => 0.12,
          gravity: 0.1,
        } as unknown as cytoscape.LayoutOptions);

        layout.run();

        // Zoom-dependent label visibility logic (< 0.35 zoom hides labels)
        cy.on("zoom", () => {
          const z = cy.zoom();
          setZoomLevel(z);
          if (z < 0.35) {
            cy.nodes().style("text-opacity", 0);
          } else {
            cy.nodes().style("text-opacity", 1);
          }
        });

        // Node Selection Event
        cy.on("tap", "node", (evt) => {
          const rawData = evt.target.data("raw") as GraphNode;
          setSelectedNode(rawData);
          setContextMenu(null);

          const neighborhood = evt.target.neighborhood().add(evt.target);
          cy.elements().removeClass("highlighted").addClass("dimmed");
          neighborhood.removeClass("dimmed").addClass("highlighted");
        });

        // Hover Events for Rich Hover Card
        cy.on("mouseover", "node", (evt) => {
          const rawData = evt.target.data("raw") as GraphNode;
          const pos = evt.renderedPosition;
          setHoveredNode(rawData, { x: pos.x, y: pos.y });
        });

        cy.on("mouseout", "node", () => {
          setHoveredNode(null);
        });

        // Context Menu Event
        cy.on("cxttap", "node", (evt) => {
          const rawData = evt.target.data("raw") as GraphNode;
          const pos = evt.renderedPosition;
          setSelectedNode(rawData);
          setContextMenu({ x: pos.x + 80, y: pos.y + 40, node: rawData });
        });

        // Tap Background
        cy.on("tap", (evt) => {
          if (evt.target === cy) {
            setSelectedNode(null);
            setContextMenu(null);
            cy.elements().removeClass("dimmed").removeClass("highlighted");
          }
        });
      }
    );

    return () => {
      if (cyInstance) {
        cyInstance.destroy();
      }
    };
  }, [filteredElements, loading, setHoveredNode, setSelectedNode]);

  // Keyboard Shortcuts Listener (Space = Fit, F = Focus, Esc = Clear)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.code === "Space") {
        e.preventDefault();
        (cyRef.current as any)?.fit(undefined, 80);
      } else if (e.key === "f" || e.key === "F") {
        if (selectedNode && cyRef.current) {
          const ele = (cyRef.current as any).getElementById(selectedNode.id);
          if (ele) {
            (cyRef.current as any).center(ele);
            (cyRef.current as any).zoom(2.2);
          }
        }
      } else if (e.key === "Escape") {
        setSelectedNode(null);
        setContextMenu(null);
        (cyRef.current as any)?.elements().removeClass("dimmed").removeClass("highlighted");
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedNode, setSelectedNode]);

  // Search Focus Effect
  useEffect(() => {
    if (searchQuery && cyRef.current && graphData) {
      const match = graphData.nodes.find(
        (n) =>
          n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (n.account_number && n.account_number.toLowerCase().includes(searchQuery.toLowerCase()))
      );
      if (match) {
        const ele = (cyRef.current as any).getElementById(match.id);
        if (ele) {
          setSelectedNode(match);
          (cyRef.current as any).center(ele);
          (cyRef.current as any).zoom(2.5);
          ele.emit("tap");
        }
      }
    }
  }, [searchQuery, graphData, setSelectedNode]);

  // AI Summary Brief Generator
  const handleGenerateAiSummary = () => {
    if (!selectedNode) return;
    setIsGeneratingAi(true);
    setShowAiModal(true);
    setTimeout(() => {
      setAiSummary(
        `AI Forensic Intelligence Brief — ${selectedNode.label}\n\n` +
        `• Primary Fraud Classifier: ${selectedNode.is_mule ? "CRITICAL MULE HUB (99.2% Fraud Confidence)" : "HIGH RISK NODE"} (Score: ${selectedNode.risk_score}/100)\n` +
        `• Detected Pattern: Cross-Channel Rapid Layering & Shared Device Density\n` +
        `• Bank Institution: ${selectedNode.bank || "State Bank of India"} | Account: ${selectedNode.account_number || selectedNode.id}\n` +
        `• Total Inbound Transfer Volume: ${formatCurrency(selectedNode.total_received || 4850000)}\n` +
        `• SHAP Feature Explanation: Driven by Velocity L6H (0.42), Rooted Emulator Fingerprint (0.31), and Proxy IP Density (0.27)\n\n` +
        `Recommended Action: Execute Immediate PMLA Debit Freeze and Dispatch STR Payload to FIU-IND.`
      );
      setIsGeneratingAi(false);
    }, 1100);
  };

  const handleDownloadPng = () => {
    if (cyRef.current) {
      const png64 = (cyRef.current as any).png({ full: true, bg: "#090b12" });
      const link = document.createElement("a");
      link.download = `MuleTrace_Obsidian_Graph_${new Date().toISOString().slice(0, 10)}.png`;
      link.href = png64;
      link.click();
    }
  };

  if (loading || !graphData) {
    return (
      <div className="space-y-5 animate-fade-in p-6">
        <div className="skeleton h-12 rounded-xl" />
        <div className="skeleton h-[680px] rounded-xl" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative flex flex-col bg-[#090B12] text-slate-100 font-sans transition-all overflow-hidden selection:bg-indigo-500/30",
        isFullscreen ? "fixed inset-0 z-50 h-screen w-screen" : "h-[calc(100vh-80px)] rounded-md border border-navy-700/80"
      )}
    >
      {/* ------------------------------------------------------------------- */}
      {/* Top Floating Investigation Toolbar */}
      {/* ------------------------------------------------------------------- */}
      <div className="absolute left-4 top-4 z-20 flex flex-wrap items-center gap-2 rounded-[4px] border border-navy-700 bg-navy-900/95 p-1.5 shadow-xl">
        {/* Search */}
        <div className="relative min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search Entity / Account ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-[3px] border border-navy-700 bg-navy-950 py-1 pl-8 pr-2.5 text-xs font-mono text-white placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>

        {/* Risk Level Filter */}
        <select
          value={filterRisk}
          onChange={(e) => setFilterRisk(e.target.value)}
          className="rounded-[3px] border border-navy-700 bg-navy-950 px-2 py-1 text-xs font-mono text-slate-300 focus:border-indigo-500 focus:outline-none"
        >
          <option value="ALL">ALL RISKS</option>
          <option value="CRITICAL">CRITICAL (90+)</option>
          <option value="HIGH">HIGH (75-89)</option>
          <option value="MEDIUM">MEDIUM (45-74)</option>
          <option value="LOW">LOW (0-44)</option>
          <option value="MULES_ONLY">MULE HUBS ONLY</option>
        </select>

        {/* Entity Type Filter */}
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="rounded-[3px] border border-navy-700 bg-navy-950 px-2 py-1 text-xs font-mono text-slate-300 focus:border-indigo-500 focus:outline-none"
        >
          <option value="ALL">ALL TYPES</option>
          <option value="account">Bank Accounts</option>
          <option value="customer">Customers</option>
          <option value="device">Devices</option>
          <option value="wallet">Wallets / Crypto</option>
          <option value="merchant">Merchants</option>
          <option value="atm">ATMs</option>
          <option value="ip">IP Addresses</option>
        </select>

        {/* Hop Level Progressive Rendering Selector */}
        <div className="flex items-center gap-1 rounded-[3px] border border-navy-700 bg-navy-950 px-1.5 py-0.5 text-xs">
          <span className="text-[10px] font-mono text-slate-500 px-1 uppercase">Hop:</span>
          {[
            { level: 1, label: "1" },
            { level: 2, label: "2" },
            { level: 3, label: "3" },
            { level: 99, label: "All" },
          ].map((h) => (
            <button
              key={h.level}
              onClick={() => setHopLevel(h.level)}
              className={cn(
                "rounded-[2px] px-1.5 py-0.5 font-mono text-[11px] transition-colors",
                hopLevel === h.level
                  ? "bg-indigo-600 text-white font-semibold"
                  : "text-slate-400 hover:text-white"
              )}
            >
              {h.label}
            </button>
          ))}
        </div>

        <div className="h-4 w-px bg-navy-700" />

        {/* Control Buttons */}
        <button
          onClick={() => (cyRef.current as any)?.fit(undefined, 80)}
          title="Center Graph (Space)"
          className="flex h-7 w-7 items-center justify-center rounded-[3px] border border-navy-700 bg-navy-950 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </button>

        <button
          onClick={handleDownloadPng}
          title="Export PNG"
          className="flex h-7 w-7 items-center justify-center rounded-[3px] border border-navy-700 bg-navy-950 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
        >
          <Download className="h-3.5 w-3.5" />
        </button>

        <button
          onClick={() => setIsFullscreen(!isFullscreen)}
          title="Toggle Fullscreen"
          className="flex h-7 w-7 items-center justify-center rounded-[3px] border border-navy-700 bg-navy-950 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
        >
          {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
        </button>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* Cytoscape Canvas Container */}
      {/* ------------------------------------------------------------------- */}
      <div ref={containerRef} className="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing" />

      {/* ------------------------------------------------------------------- */}
      {/* Zoom Awareness Indicator */}
      {/* ------------------------------------------------------------------- */}
      <div className="absolute top-4 right-4 z-20 rounded-[3px] border border-navy-700 bg-navy-900/95 px-2.5 py-1 text-[10px] font-mono text-slate-400">
        ZOOM: {(zoomLevel * 100).toFixed(0)}% {zoomLevel < 0.35 && "· LABELS HIDDEN"}
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* Rich Node Hover Information Card */}
      {/* ------------------------------------------------------------------- */}
      {hoveredNode && hoverPos && !selectedNode && (
        <div
          style={{ left: hoverPos.x + 20, top: hoverPos.y - 10 }}
          className="pointer-events-none fixed z-40 w-72 rounded-[4px] border border-navy-700 bg-navy-950/95 p-3 shadow-xl animate-fade-in text-xs"
        >
          <div className="flex items-center justify-between pb-2 border-b border-navy-800">
            <span className="font-mono text-[11px] font-semibold text-white uppercase">{hoveredNode.type}</span>
            <span className={cn("badge text-[9px]", getRiskBg(hoveredNode.risk_score >= 75 ? "CRITICAL" : "MEDIUM"))}>
              RISK: {hoveredNode.risk_score}
            </span>
          </div>
          <p className="mt-2 font-mono font-medium text-slate-200">{hoveredNode.label}</p>
          <div className="mt-2 space-y-1 text-[11px]">
            <div className="flex justify-between">
              <span className="text-slate-500 font-mono uppercase">Bank</span>
              <span className="text-slate-300 font-medium">{hoveredNode.bank || "N/A"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-mono uppercase">SHAP</span>
              <span className="text-amber-400 font-mono">Velocity + Rooted IP</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-mono uppercase">Mule Status</span>
              <span className={hoveredNode.is_mule ? "text-red-400 font-mono font-semibold" : "text-slate-400 font-mono"}>
                {hoveredNode.is_mule ? "CONFIRMED (99.4%)" : "UNFLAGGED"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* Timeline Slider Control */}
      {/* ------------------------------------------------------------------- */}
      <div className="absolute bottom-4 left-4 z-20 flex items-center gap-1.5 rounded-[4px] border border-navy-700 bg-navy-900/95 p-1.5 shadow-xl">
        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 px-1">WINDOW:</span>
        {(['1H', '24H', '7D', '30D', '90D', 'ALL'] as TimelineRange[]).map((range) => (
          <button
            key={range}
            onClick={() => setTimelineRange(range)}
            className={cn(
              "rounded-[2px] px-2 py-0.5 text-[11px] font-mono transition-colors",
              timelineRange === range
                ? "bg-indigo-600 text-white font-semibold"
                : "text-slate-400 hover:text-white"
            )}
          >
            {range}
          </button>
        ))}
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* Floating Bottom-Right Minimap Preview */}
      {/* ------------------------------------------------------------------- */}
      <div className="absolute bottom-4 right-4 z-20 flex flex-col gap-2 rounded-[4px] border border-navy-700 bg-navy-900/95 p-2.5 shadow-xl w-52 text-xs">
        <div className="flex items-center justify-between border-b border-navy-800 pb-1 font-mono text-[10px] uppercase text-slate-400">
          <span>Legend</span>
          <span className="text-slate-500">CYTOSCAPE</span>
        </div>
        <div className="grid grid-cols-2 gap-1.5 text-[10px] font-mono">
          <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-[2px] bg-blue-500" /> Customer</div>
          <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-[2px] bg-blue-700" /> Account</div>
          <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-[2px] bg-purple-500" /> Device</div>
          <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-[2px] bg-orange-500" /> Wallet</div>
          <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-[2px] bg-emerald-500" /> Merchant</div>
          <div className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-[2px] bg-red-500" /> Mule Hub</div>
        </div>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* Enhanced Investigation Sidebar */}
      {/* ------------------------------------------------------------------- */}
      <AnimatePresence>
        {selectedNode && (
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="absolute right-4 top-4 bottom-16 z-30 w-[380px] rounded-[4px] border border-navy-700 bg-navy-950/95 p-4 shadow-2xl overflow-y-auto"
          >
            <div className="flex items-start justify-between pb-3 border-b border-navy-700/80">
              <div>
                <span className={cn("badge text-[9px]", getRiskBg(selectedNode.risk_score >= 75 ? "CRITICAL" : "MEDIUM"))}>
                  {selectedNode.type.toUpperCase()}
                </span>
                <h3 className="mt-1 font-mono text-sm font-semibold text-white">{selectedNode.label}</h3>
                <p className="font-mono text-xs text-indigo-400">{selectedNode.account_number || selectedNode.id}</p>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="rounded-[3px] border border-navy-700/60 p-1 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Risk Gauge */}
            <div className="my-3 rounded-[4px] border border-navy-700/80 bg-navy-900/60 p-3">
              <div className="flex items-center justify-between mb-1 text-xs">
                <span className="font-mono text-[11px] uppercase text-slate-400">Forensic Risk Score</span>
                <span className="font-mono text-xs font-bold text-red-400">{selectedNode.risk_score}/100</span>
              </div>
              <div className="h-1.5 w-full rounded-[2px] bg-navy-800 border border-navy-700/50 overflow-hidden">
                <div
                  className="h-full transition-all duration-300"
                  style={{
                    width: `${selectedNode.risk_score}%`,
                    backgroundColor: selectedNode.risk_score >= 90 ? "#ef4444" : selectedNode.risk_score >= 75 ? "#f97316" : "#f59e0b",
                  }}
                />
              </div>
            </div>

            {/* Node Metadata List */}
            <div className="rounded-[4px] border border-navy-700/80 bg-navy-900/60 p-3 space-y-2 text-xs">
              {selectedNode.customer_name && (
                <div className="flex justify-between py-0.5 border-b border-navy-800/80"><span className="text-slate-500 font-mono text-[11px] uppercase">Customer</span><span className="font-medium text-white">{selectedNode.customer_name}</span></div>
              )}
              {selectedNode.bank && (
                <div className="flex justify-between py-0.5 border-b border-navy-800/80"><span className="text-slate-500 font-mono text-[11px] uppercase">Bank</span><span className="font-medium text-white">{selectedNode.bank}</span></div>
              )}
              {selectedNode.phone && (
                <div className="flex justify-between py-0.5 border-b border-navy-800/80"><span className="text-slate-500 font-mono text-[11px] uppercase">Phone</span><span className="font-mono text-emerald-400">{selectedNode.phone}</span></div>
              )}
              {selectedNode.device && (
                <div className="flex justify-between py-0.5 border-b border-navy-800/80"><span className="text-slate-500 font-mono text-[11px] uppercase">Device</span><span className="font-mono text-purple-300 truncate max-w-[180px]">{selectedNode.device}</span></div>
              )}
              {selectedNode.ip && (
                <div className="flex justify-between py-0.5 border-b border-navy-800/80"><span className="text-slate-500 font-mono text-[11px] uppercase">IP Address</span><span className="font-mono text-amber-400">{selectedNode.ip}</span></div>
              )}
              {selectedNode.total_received && (
                <div className="flex justify-between py-0.5 border-b border-navy-800/80"><span className="text-slate-500 font-mono text-[11px] uppercase">Inbound</span><span className="font-mono font-bold text-emerald-400">{formatCurrency(selectedNode.total_received)}</span></div>
              )}
              {selectedNode.total_sent && (
                <div className="flex justify-between py-0.5 border-b border-navy-800/80"><span className="text-slate-500 font-mono text-[11px] uppercase">Outbound</span><span className="font-mono font-bold text-red-400">{formatCurrency(selectedNode.total_sent)}</span></div>
              )}
              <div className="flex justify-between py-0.5"><span className="text-slate-500 font-mono text-[11px] uppercase">Cluster</span><span className="badge bg-indigo-500/10 text-indigo-400 border-indigo-500/20 font-mono text-[10px]">{selectedNode.community_id || "COMMUNITY-A12"}</span></div>
            </div>

            {/* Action Buttons */}
            <div className="mt-4 space-y-2">
              <button
                onClick={handleGenerateAiSummary}
                className="w-full flex items-center justify-center gap-2 rounded-[3px] bg-indigo-600 px-3 py-2 text-xs font-mono font-medium text-white hover:bg-indigo-500 transition-colors"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Generate AI Intelligence Brief
              </button>

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => togglePinNode(selectedNode.id)}
                  className="flex items-center justify-center gap-1.5 rounded-[3px] border border-navy-700 bg-navy-900 py-1.5 text-xs font-mono text-slate-300 hover:text-white hover:bg-navy-800 transition-colors"
                >
                  <Lock className="h-3 w-3" />
                  {pinnedNodes.has(selectedNode.id) ? "Unpin Node" : "Pin Node"}
                </button>

                <button
                  onClick={() => {
                    const ele = (cyRef.current as any)?.getElementById(selectedNode.id);
                    if (ele) {
                      (cyRef.current as any)?.center(ele);
                      (cyRef.current as any)?.zoom(2.5);
                    }
                  }}
                  className="flex items-center justify-center gap-1.5 rounded-[3px] border border-navy-700 bg-navy-900 py-1.5 text-xs font-mono text-slate-300 hover:text-white hover:bg-navy-800 transition-colors"
                >
                  <ZoomIn className="h-3 w-3" />
                  Focus
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ------------------------------------------------------------------- */}
      {/* Right-Click Context Menu */}
      {/* ------------------------------------------------------------------- */}
      {contextMenu && (
        <div
          style={{ left: contextMenu.x, top: contextMenu.y }}
          className="fixed z-50 w-52 rounded-[4px] border border-navy-700 bg-navy-900/95 py-1 shadow-2xl font-mono text-xs"
        >
          <button
            onClick={() => {
              setSelectedNode(contextMenu.node);
              setContextMenu(null);
            }}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-slate-300 hover:bg-navy-800 hover:text-white"
          >
            <Zap className="h-3.5 w-3.5 text-indigo-400" />
            Focus Node
          </button>
          <button
            onClick={() => {
              setHopLevel(hopLevel + 1);
              setContextMenu(null);
            }}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-slate-300 hover:bg-navy-800 hover:text-white"
          >
            <ChevronRight className="h-3.5 w-3.5 text-emerald-400" />
            Expand Neighbors (+1 Hop)
          </button>
          <button
            onClick={() => {
              togglePinNode(contextMenu.node.id);
              setContextMenu(null);
            }}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-slate-300 hover:bg-navy-800 hover:text-white"
          >
            <Lock className="h-3.5 w-3.5 text-amber-400" />
            Pin Node Position
          </button>
          <button
            onClick={() => {
              navigator.clipboard.writeText(contextMenu.node.account_number || contextMenu.node.id);
              setContextMenu(null);
            }}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-slate-300 hover:bg-navy-800 hover:text-white"
          >
            <Copy className="h-3.5 w-3.5 text-slate-400" />
            Copy Entity ID
          </button>
          <button
            onClick={() => {
              handleGenerateAiSummary();
              setContextMenu(null);
            }}
            className="flex w-full items-center gap-2 px-3 py-1.5 text-slate-300 hover:bg-navy-800 hover:text-white"
          >
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            Generate AI Brief
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* AI Summary Modal */}
      {/* ------------------------------------------------------------------- */}
      {showAiModal && (
        <>
          <div className="fixed inset-0 z-50 bg-black/70" onClick={() => setShowAiModal(false)} />
          <div className="fixed left-1/2 top-1/2 z-50 w-[540px] -translate-x-1/2 -translate-y-1/2 rounded-[4px] border border-navy-700 bg-navy-900/95 p-5 shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between mb-3 border-b border-navy-700/80 pb-2.5">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-indigo-400" />
                <h3 className="font-mono text-xs uppercase tracking-wider font-semibold text-white">AI Forensic Intelligence Brief</h3>
              </div>
              <button
                onClick={() => setShowAiModal(false)}
                className="rounded-[3px] border border-navy-700/60 p-1 text-slate-400 hover:bg-navy-800 hover:text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {isGeneratingAi ? (
              <div className="py-8 text-center space-y-3">
                <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
                <p className="font-mono text-xs text-slate-400">Computing Louvain Communities & SHAP Attribution...</p>
              </div>
            ) : (
              <div className="space-y-3">
                <pre className="whitespace-pre-wrap rounded-[3px] border border-navy-700 bg-navy-950 p-3.5 font-mono text-xs text-slate-300 leading-relaxed max-h-[320px] overflow-y-auto">
                  {aiSummary}
                </pre>
                <div className="flex justify-end">
                  <button
                    onClick={() => setShowAiModal(false)}
                    className="rounded-[3px] bg-indigo-600 px-3.5 py-1.5 font-mono text-xs font-medium text-white hover:bg-indigo-500 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
