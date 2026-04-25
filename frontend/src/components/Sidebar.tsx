/**
 * frontend/src/components/Sidebar.tsx — Forensic Intelligence Panel
 * Role: UI/Viz Designer (Member 4)
 *
 * Displays wallet risk details and triggers the Gemini AI forensic report
 * when a node is selected in the Galaxy3D visualization.
 * Also exposes the Guardian Shield button for on-chain blacklisting.
 */

import React, { useCallback, useState } from "react";
import type { GalaxyNode } from "./Galaxy3D";

const API_BASE = "";


// ── Risk color mapping ─────────────────────────────────────────
const RISK_COLORS: Record<string, string> = {
  CRITICAL: "#FF3B3B",
  HIGH:     "#FF8C00",
  MEDIUM:   "#FFD700",
  LOW:      "#4ADE80",
};

function scoreToColor(score: number): string {
  if (score > 0.85) return "#FF3B3B";
  if (score > 0.65) return "#FF8C00";
  if (score > 0.40) return "#FFD700";
  return "#4ADE80";
}

// ── Forensic Report Types ──────────────────────────────────────
interface ForensicReport {
  wallet_address: string;
  risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  risk_score: number;
  executive_summary: string;
  threat_narrative: string;
  recommended_actions: string[];
  exploit_categories: string[];
}

// ── Props ──────────────────────────────────────────────────────
interface SidebarProps {
  selectedNode: GalaxyNode | null;
  onClose: () => void;
}

// ── Component ──────────────────────────────────────────────────
export default function Sidebar({ selectedNode, onClose }: SidebarProps) {
  const [report, setReport] = useState<ForensicReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [txStatus, setTxStatus] = useState<"idle" | "pending" | "success" | "error">("idle");
  const [txHash, setTxHash] = useState<string | null>(null);

  const fetchReport = useCallback(async () => {
    if (!selectedNode) return;
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const res = await fetch(`${API_BASE}/api/forensic/report/${selectedNode.address}`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setReport(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to fetch forensic report");
    } finally {
      setLoading(false);
    }
  }, [selectedNode]);

  const handleShield = useCallback(async () => {
    if (!selectedNode) return;
    setTxStatus("pending");
    setTxHash(null);
    try {
      const res = await fetch(`${API_BASE}/api/graph/flag`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          wallet_address: selectedNode.address,
          risk_score: selectedNode.riskScore,
        }),
      });
      if (!res.ok) throw new Error(`Shield failed: ${res.status}`);
      const data = await res.json();
      setTxHash(data?.tx_hash ?? null);
      setTxStatus("success");
    } catch (err: any) {
      setTxStatus("error");
    }
  }, [selectedNode]);

  if (!selectedNode) {
    return (
      <aside style={styles.sidebar}>
        <div style={styles.emptyState}>
          <div style={{ fontSize: 40 }}>🌌</div>
          <p style={styles.emptyText}>
            Click any node in the galaxy to begin forensic analysis.
          </p>
        </div>
      </aside>
    );
  }

  const riskColor = scoreToColor(selectedNode.riskScore);

  return (
    <aside style={styles.sidebar}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <div
            style={{
              ...styles.riskBadge,
              background: riskColor + "20",
              color: riskColor,
              border: `1px solid ${riskColor}60`,
            }}
          >
            {selectedNode.riskScore > 0.85
              ? "⚠ CRITICAL"
              : selectedNode.riskScore > 0.65
              ? "⚠ HIGH"
              : selectedNode.riskScore > 0.40
              ? "● MEDIUM"
              : "✓ LOW"}{" "}
            RISK &nbsp;·&nbsp; {(selectedNode.riskScore * 100).toFixed(1)}%
          </div>
          <div style={styles.walletAddress}>
            {selectedNode.address.slice(0, 10)}…{selectedNode.address.slice(-6)}
          </div>
          <div style={styles.labelBadge}>
            {selectedNode.label.toUpperCase()} &nbsp;|&nbsp;{" "}
            {selectedNode.flagged ? "🚩 FLAGGED" : "◎ ACTIVE"}
          </div>
        </div>
        <button onClick={onClose} style={styles.closeBtn}>✕</button>
      </div>

      {/* Stats Row */}
      <div style={styles.statsRow}>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{selectedNode.txCount.toLocaleString()}</div>
          <div style={styles.statLabel}>TRANSACTIONS</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{selectedNode.balanceEth.toFixed(3)}</div>
          <div style={styles.statLabel}>BALANCE ETH</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: riskColor }}>
            {(selectedNode.riskScore * 100).toFixed(0)}%
          </div>
          <div style={styles.statLabel}>RISK SCORE</div>
        </div>
      </div>

      {/* Forensic Intelligence Section */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <span>🔍 FORENSIC INTELLIGENCE</span>
          <button onClick={fetchReport} disabled={loading} style={styles.analyzeBtn}>
            {loading ? "Analyzing…" : "Run AI Analysis"}
          </button>
        </div>

        {error && <div style={styles.errorBox}>{error}</div>}

        {report ? (
          <div>
            <div
              style={{
                ...styles.riskLevelBanner,
                background: (RISK_COLORS[report.risk_level] ?? "#94A3B8") + "18",
                borderColor: RISK_COLORS[report.risk_level] ?? "#94A3B8",
                color: RISK_COLORS[report.risk_level] ?? "#94A3B8",
              }}
            >
              ⚠ {report.risk_level} RISK
            </div>
            <p style={styles.summaryText}>{report.executive_summary}</p>
            <div style={styles.narrativeBox}>
              <p style={styles.narrativeText}>{report.threat_narrative}</p>
            </div>
            {report.recommended_actions.length > 0 && (
              <div style={styles.actionsSection}>
                <div style={styles.actionsTitle}>Recommended Actions</div>
                <ul style={styles.actionsList}>
                  {report.recommended_actions.map((action, i) => (
                    <li key={i} style={styles.actionItem}>→ {action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          !loading && (
            <p style={styles.hintText}>
              Click "Run AI Analysis" to generate a Gemini-powered forensic report for this wallet.
            </p>
          )
        )}
      </div>

      {/* Shield Action */}
      <div style={styles.shieldSection}>
        <button
          onClick={handleShield}
          disabled={txStatus === "pending"}
          style={{
            ...styles.shieldBtn,
            opacity: txStatus === "pending" ? 0.6 : 1,
          }}
        >
          {txStatus === "pending"   && "⏳ Sending…"}
          {txStatus === "success"   && "✅ Shield Active"}
          {txStatus === "error"     && "❌ Failed — Retry"}
          {txStatus === "idle"      && "🛡 Activate Guardian Shield"}
        </button>
        {txHash && (
          <a
            href={`https://sepolia.basescan.org/tx/${txHash}`}
            target="_blank"
            rel="noopener noreferrer"
            style={styles.txLink}
          >
            View on BaseScan ↗
          </a>
        )}
      </div>
    </aside>
  );
}

// ── Inline Styles ──────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: 380,
    minWidth: 320,
    height: "100%",
    background: "linear-gradient(180deg, #0D0D1A 0%, #06060F 100%)",
    borderLeft: "1px solid rgba(0, 212, 255, 0.15)",
    display: "flex",
    flexDirection: "column",
    overflowY: "auto",
    fontFamily: "'Inter', sans-serif",
    color: "#E2E8F0",
  },
  emptyState: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: 40,
    gap: 16,
  },
  emptyText: { color: "#475569", textAlign: "center", fontSize: 14, lineHeight: 1.6 },
  header: {
    padding: "20px 20px 12px",
    borderBottom: "1px solid rgba(0,212,255,0.1)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 12,
  },
  riskBadge: {
    display: "inline-block",
    padding: "3px 10px",
    borderRadius: 6,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: "0.08em",
    marginBottom: 6,
  },
  walletAddress: {
    fontSize: 14,
    fontFamily: "'JetBrains Mono', monospace",
    color: "#CBD5E1",
    margin: "4px 0",
  },
  labelBadge: { fontSize: 10, color: "#64748B", letterSpacing: "0.1em" },
  closeBtn: {
    background: "transparent",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: 6,
    color: "#94A3B8",
    cursor: "pointer",
    padding: "4px 8px",
    fontSize: 14,
  },
  statsRow: {
    display: "flex",
    gap: 8,
    padding: "12px 16px",
    borderBottom: "1px solid rgba(0,212,255,0.08)",
  },
  statCard: {
    flex: 1,
    background: "rgba(255,255,255,0.03)",
    border: "1px solid rgba(255,255,255,0.06)",
    borderRadius: 8,
    padding: "8px 10px",
    textAlign: "center",
  },
  statValue: { fontSize: 13, fontWeight: 700, color: "#E2E8F0", marginBottom: 2 },
  statLabel: { fontSize: 10, color: "#64748B", letterSpacing: "0.06em" },
  section: { padding: "16px 16px 8px", flex: 1 },
  sectionHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
    fontSize: 11,
    fontWeight: 700,
    letterSpacing: "0.1em",
    color: "#00D4FF",
  },
  analyzeBtn: {
    background: "rgba(0,212,255,0.1)",
    border: "1px solid rgba(0,212,255,0.4)",
    borderRadius: 6,
    color: "#00D4FF",
    cursor: "pointer",
    padding: "5px 12px",
    fontSize: 11,
    fontWeight: 600,
  },
  errorBox: {
    background: "rgba(255,59,59,0.1)",
    border: "1px solid rgba(255,59,59,0.3)",
    borderRadius: 6,
    padding: "8px 12px",
    fontSize: 12,
    color: "#FF3B3B",
    marginBottom: 8,
  },
  riskLevelBanner: {
    border: "1px solid",
    borderRadius: 6,
    padding: "6px 12px",
    fontSize: 12,
    fontWeight: 700,
    letterSpacing: "0.08em",
    marginBottom: 10,
  },
  summaryText: { fontSize: 13, color: "#CBD5E1", lineHeight: 1.6, marginBottom: 10 },
  narrativeBox: {
    background: "rgba(255,255,255,0.02)",
    border: "1px solid rgba(255,255,255,0.06)",
    borderRadius: 8,
    padding: 12,
    marginBottom: 10,
    maxHeight: 180,
    overflowY: "auto",
  },
  narrativeText: { fontSize: 12, color: "#94A3B8", lineHeight: 1.7, margin: 0 },
  actionsSection: { marginTop: 10 },
  actionsTitle: { fontSize: 10, fontWeight: 700, color: "#64748B", letterSpacing: "0.1em", marginBottom: 6 },
  actionsList: { margin: 0, padding: 0, listStyle: "none" },
  actionItem: { fontSize: 12, color: "#94A3B8", padding: "3px 0", lineHeight: 1.5 },
  hintText: { fontSize: 12, color: "#475569", lineHeight: 1.6 },
  shieldSection: {
    padding: "12px 16px 20px",
    borderTop: "1px solid rgba(255,59,59,0.15)",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  shieldBtn: {
    background: "linear-gradient(135deg, #FF3B3B22, #FF8C0022)",
    border: "1px solid #FF3B3B",
    borderRadius: 8,
    color: "#FF3B3B",
    cursor: "pointer",
    padding: "12px 16px",
    fontSize: 14,
    fontWeight: 700,
    letterSpacing: "0.05em",
    transition: "all 0.2s ease",
  },
  txLink: { fontSize: 11, color: "#00D4FF", textDecoration: "none", textAlign: "center" },
};
