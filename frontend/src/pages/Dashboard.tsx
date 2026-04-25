/**
 * frontend/src/pages/Dashboard.tsx — Main Layout
 * Role: UI/Viz Designer (Member 4)
 */

import { useCallback, useEffect, useState } from "react";
import { usePrivy } from "@privy-io/react-auth";
import Galaxy3D, { type GalaxyNode, type GraphData } from "../components/Galaxy3D";
import Sidebar from "../components/Sidebar";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const EMPTY_GRAPH: GraphData = { nodes: [], links: [] };

export default function Dashboard() {
  const { login, logout, authenticated, user } = usePrivy();

  const [graphData, setGraphData] = useState<GraphData>(EMPTY_GRAPH);
  const [selectedNode, setSelectedNode] = useState<GalaxyNode | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [alertMode, setAlertMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  // Fetch graph data from backend
  const fetchGraph = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/graph/nodes?limit=500`);
      if (!res.ok) throw new Error("Graph fetch failed");
      const data = await res.json();
      setGraphData(data);
      // Alert mode if any flagged nodes exist
      setAlertMode(data.nodes?.some((n: GalaxyNode) => n.flagged) ?? false);
      setLastRefresh(new Date());
    } catch {
      // In dev, use mock data so UI is still renderable
      setGraphData(MOCK_GRAPH_DATA);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGraph();
    const interval = setInterval(fetchGraph, 30_000); // Poll every 30s
    return () => clearInterval(interval);
  }, [fetchGraph]);

  const handleNodeSelect = (node: GalaxyNode) => {
    setSelectedNode(node);
    setSidebarOpen(true);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
    setSelectedNode(null);
  };

  return (
    <div style={styles.root}>
      {/* Top Navigation Bar */}
      <nav style={styles.nav}>
        <div style={styles.navBrand}>
          <span style={styles.navLogo}>🛡</span>
          <span style={styles.navTitle}>SENTINEL GALAXY</span>
          {alertMode && (
            <span style={styles.alertPill}>⚠ THREATS ACTIVE</span>
          )}
        </div>

        <div style={styles.navStats}>
          <span style={styles.statChip}>
            ⬡ {graphData.nodes.length.toLocaleString()} Nodes
          </span>
          <span style={styles.statChip}>
            🔗 {graphData.links.length.toLocaleString()} Edges
          </span>
          <span style={{ ...styles.statChip, color: "#FF3B3B" }}>
            🚨 {graphData.nodes.filter((n) => n.flagged).length} Flagged
          </span>
          {lastRefresh && (
            <span style={{ ...styles.statChip, color: "#64748B" }}>
              ↻ {lastRefresh.toLocaleTimeString()}
            </span>
          )}
        </div>

        <div style={styles.navActions}>
          <button onClick={fetchGraph} style={styles.refreshBtn}>⟳ Refresh</button>
          {authenticated ? (
            <div style={styles.userMenu}>
              <span style={styles.userAddress}>
                {user?.wallet?.address
                  ? `${user.wallet.address.slice(0, 6)}…${user.wallet.address.slice(-4)}`
                  : user?.email?.address ?? "Connected"}
              </span>
              <button onClick={logout} style={styles.logoutBtn}>Disconnect</button>
            </div>
          ) : (
            <button onClick={login} style={styles.connectBtn}>
              Connect Wallet
            </button>
          )}
        </div>
      </nav>

      {/* Main Content Area */}
      <div style={styles.content}>
        {/* 3D Galaxy */}
        <div style={{ flex: 1, position: "relative" }}>
          {loading ? (
            <div style={styles.loadingScreen}>
              <div style={styles.loadingSpinner} />
              <p style={styles.loadingText}>Initializing Sentinel Galaxy…</p>
            </div>
          ) : (
            <Galaxy3D
              graphData={graphData}
              onNodeSelect={handleNodeSelect}
              selectedNode={selectedNode}
              alertMode={alertMode}
            />
          )}
        </div>

        {/* Sidebar — Forensic Intelligence Panel */}
        {sidebarOpen && (
          <Sidebar selectedNode={selectedNode} onClose={handleSidebarClose} />
        )}
      </div>

      {/* CSS Animations */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #000; overflow: hidden; }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

// ── Inline Styles ──────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  root: {
    width: "100vw",
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    background: "#000008",
    overflow: "hidden",
    fontFamily: "'Inter', sans-serif",
  },
  nav: {
    height: 56,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 20px",
    background: "rgba(6, 6, 15, 0.95)",
    borderBottom: "1px solid rgba(0, 212, 255, 0.15)",
    backdropFilter: "blur(12px)",
    zIndex: 100,
    gap: 16,
  },
  navBrand: { display: "flex", alignItems: "center", gap: 10 },
  navLogo: { fontSize: 22 },
  navTitle: {
    fontSize: 15,
    fontWeight: 800,
    letterSpacing: "0.18em",
    color: "#00D4FF",
    fontFamily: "'JetBrains Mono', monospace",
  },
  alertPill: {
    background: "rgba(255,59,59,0.15)",
    border: "1px solid #FF3B3B",
    borderRadius: 6,
    padding: "2px 8px",
    fontSize: 10,
    fontWeight: 700,
    color: "#FF3B3B",
    letterSpacing: "0.08em",
    animation: "pulse 1.5s ease-in-out infinite",
  },
  navStats: { display: "flex", gap: 8, flex: 1, justifyContent: "center" },
  statChip: {
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 6,
    padding: "3px 10px",
    fontSize: 11,
    color: "#94A3B8",
    fontFamily: "'JetBrains Mono', monospace",
  },
  navActions: { display: "flex", alignItems: "center", gap: 10 },
  refreshBtn: {
    background: "transparent",
    border: "1px solid rgba(0,212,255,0.3)",
    borderRadius: 6,
    color: "#00D4FF",
    cursor: "pointer",
    padding: "5px 12px",
    fontSize: 12,
  },
  connectBtn: {
    background: "linear-gradient(135deg, #4F46E5, #7C3AED)",
    border: "none",
    borderRadius: 8,
    color: "#fff",
    cursor: "pointer",
    padding: "7px 16px",
    fontSize: 12,
    fontWeight: 700,
  },
  userMenu: { display: "flex", alignItems: "center", gap: 8 },
  userAddress: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 12,
    color: "#94A3B8",
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 6,
    padding: "4px 10px",
  },
  logoutBtn: {
    background: "transparent",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 6,
    color: "#64748B",
    cursor: "pointer",
    padding: "4px 10px",
    fontSize: 11,
  },
  content: { flex: 1, display: "flex", overflow: "hidden" },
  loadingScreen: {
    position: "absolute",
    inset: 0,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 20,
    background: "#000008",
  },
  loadingSpinner: {
    width: 48,
    height: 48,
    border: "3px solid rgba(0,212,255,0.15)",
    borderTop: "3px solid #00D4FF",
    borderRadius: "50%",
    animation: "spin 1s linear infinite",
  },
  loadingText: {
    color: "#00D4FF",
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: 13,
    letterSpacing: "0.1em",
  },
};

// ── Mock data (dev fallback when backend is offline) ───────────
const MOCK_GRAPH_DATA: GraphData = {
  nodes: Array.from({ length: 80 }, (_, i) => ({
    id: `0x${i.toString(16).padStart(40, "0")}`,
    address: `0x${i.toString(16).padStart(40, "0")}`,
    label: (["defi_user", "bot", "whale", "exchange", "attacker"] as const)[i % 5],
    riskScore: Math.random(),
    flagged: Math.random() > 0.9,
    txCount: Math.floor(Math.random() * 5000),
    balanceEth: Math.random() * 100,
  })),
  links: Array.from({ length: 120 }, (_, i) => ({
    source: `0x${(i % 80).toString(16).padStart(40, "0")}`,
    target: `0x${((i + 7) % 80).toString(16).padStart(40, "0")}`,
    txHash: `0x${"a".repeat(64)}`,
    valueEth: Math.random() * 20,
  })),
};
