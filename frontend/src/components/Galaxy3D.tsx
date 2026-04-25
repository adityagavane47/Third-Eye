/**
 * frontend/src/components/Galaxy3D.tsx — 3D Force Graph Visualization
 * Role: UI/Viz Designer (Member 4)
 *
 * Renders the blockchain transaction graph as an interactive 3D galaxy
 * using react-force-graph-3d. Node color encodes risk level.
 * Clicking a node triggers forensic analysis via the Sidebar.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import ForceGraph3D from "react-force-graph-3d";
import * as THREE from "three";

// ── Types ──────────────────────────────────────────────────────
export interface GalaxyNode {
  id: string;             // wallet address (0x...)
  address: string;
  label: "defi_user" | "bot" | "exchange" | "whale" | "attacker" | "unknown";
  riskScore: number;      // 0.0 → 1.0
  flagged: boolean;
  txCount: number;
  balanceEth: number;
  x?: number;
  y?: number;
  z?: number;
  __threeObj?: THREE.Object3D;
}

export interface GalaxyLink {
  source: string;         // from wallet address
  target: string;         // to wallet address
  txHash: string;
  valueEth: number;
}

export interface GraphData {
  nodes: GalaxyNode[];
  links: GalaxyLink[];
}

interface Galaxy3DProps {
  /** Data fetched from /api/graph/nodes */
  graphData: GraphData;
  /** Callback when a node is clicked — triggers Sidebar update */
  onNodeSelect: (node: GalaxyNode) => void;
  /** Currently selected node (highlighted in galaxy) */
  selectedNode: GalaxyNode | null;
  /** Whether the galaxy is in "alert mode" (flashing red) */
  alertMode?: boolean;
}

// ── Risk Color Mapping ─────────────────────────────────────────
function riskToColor(riskScore: number, flagged: boolean): string {
  if (flagged || riskScore > 0.85) return "#FF3B3B";   // Critical — deep red
  if (riskScore > 0.65) return "#FF8C00";              // High — amber
  if (riskScore > 0.40) return "#FFD700";              // Medium — gold
  if (riskScore > 0.20) return "#00D4FF";              // Low — cyan
  return "#4ADE80";                                    // Safe — green
}

function labelToSize(label: GalaxyNode["label"], riskScore: number): number {
  const base = label === "whale" ? 6 : label === "exchange" ? 5 : 3;
  return base + riskScore * 4; // Higher risk = larger node
}

// ── Component ──────────────────────────────────────────────────
export default function Galaxy3D({
  graphData,
  onNodeSelect,
  selectedNode,
  alertMode = false,
}: Galaxy3DProps) {
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  // Responsive resize
  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Auto-zoom to selected node
  useEffect(() => {
    if (selectedNode && graphRef.current) {
      graphRef.current.cameraPosition(
        { x: (selectedNode.x ?? 0) + 80, y: selectedNode.y ?? 0, z: selectedNode.z ?? 0 },
        { x: selectedNode.x ?? 0, y: selectedNode.y ?? 0, z: selectedNode.z ?? 0 },
        1200,
      );
    }
  }, [selectedNode]);

  // Rotating camera animation (slow, cinematic)
  useEffect(() => {
    if (!graphRef.current) return;
    let angle = 0;
    const distance = 600;
    const interval = setInterval(() => {
      if (!selectedNode) {
        angle += 0.002;
        graphRef.current?.cameraPosition({
          x: distance * Math.sin(angle),
          z: distance * Math.cos(angle),
          y: 80,
        });
      }
    }, 30);
    return () => clearInterval(interval);
  }, [selectedNode]);

  // Custom 3D node renderer using Three.js spheres
  const nodeThreeObject = useCallback(
    (node: GalaxyNode) => {
      const color = riskToColor(node.riskScore, node.flagged);
      const size = labelToSize(node.label, node.riskScore);
      const isSelected = selectedNode?.id === node.id;

      const group = new THREE.Group();

      // Core sphere
      const geometry = new THREE.SphereGeometry(isSelected ? size * 1.5 : size, 16, 16);
      const material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        emissive: new THREE.Color(color),
        emissiveIntensity: isSelected ? 1.5 : node.flagged ? 0.8 : 0.3,
        roughness: 0.2,
        metalness: 0.6,
      });
      group.add(new THREE.Mesh(geometry, material));

      // Glow halo for flagged nodes
      if (node.flagged || isSelected) {
        const haloGeo = new THREE.SphereGeometry(size * 2.5, 16, 16);
        const haloMat = new THREE.MeshBasicMaterial({
          color: new THREE.Color(color),
          transparent: true,
          opacity: 0.12,
          side: THREE.BackSide,
        });
        group.add(new THREE.Mesh(haloGeo, haloMat));
      }

      return group;
    },
    [selectedNode]
  );

  // Link color based on transaction value
  const linkColor = useCallback((link: GalaxyLink) => {
    if (link.valueEth > 10) return "#FF3B3B";
    if (link.valueEth > 1) return "#FF8C00";
    return "rgba(100, 200, 255, 0.3)";
  }, []);

  const linkWidth = useCallback((link: GalaxyLink) => {
    return Math.min(0.5 + link.valueEth * 0.1, 3);
  }, []);

  return (
    <div
      ref={containerRef}
      className="galaxy-container"
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        background: alertMode
          ? "radial-gradient(ellipse at center, #1a0000 0%, #0a0010 100%)"
          : "radial-gradient(ellipse at center, #0a0020 0%, #000008 100%)",
        transition: "background 0.5s ease",
      }}
    >
      {/* Ambient overlay — star field effect */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "radial-gradient(1px 1px at 20px 30px, rgba(255,255,255,0.15), transparent), " +
            "radial-gradient(1px 1px at 80px 60px, rgba(255,255,255,0.1), transparent), " +
            "radial-gradient(1px 1px at 140px 100px, rgba(255,255,255,0.12), transparent)",
          backgroundSize: "200px 200px",
          pointerEvents: "none",
          zIndex: 1,
        }}
      />

      {/* Node count badge */}
      <div
        style={{
          position: "absolute",
          top: 16,
          left: 16,
          zIndex: 10,
          background: "rgba(0,0,0,0.6)",
          border: "1px solid rgba(0, 212, 255, 0.3)",
          borderRadius: 8,
          padding: "6px 12px",
          color: "#00D4FF",
          fontSize: 12,
          fontFamily: "'JetBrains Mono', monospace",
          backdropFilter: "blur(8px)",
        }}
      >
        ⬡ {graphData.nodes.length.toLocaleString()} nodes · {graphData.links.length.toLocaleString()} edges
      </div>

      {/* Alert mode banner */}
      {alertMode && (
        <div
          style={{
            position: "absolute",
            top: 16,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 10,
            background: "rgba(255,59,59,0.15)",
            border: "1px solid #FF3B3B",
            borderRadius: 8,
            padding: "6px 20px",
            color: "#FF3B3B",
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: "0.1em",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        >
          🚨 THREAT DETECTED — SENTINEL ACTIVE
        </div>
      )}

      <ForceGraph3D
        ref={graphRef}
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="rgba(0,0,0,0)"
        nodeThreeObject={nodeThreeObject}
        nodeThreeObjectExtend={false}
        nodeLabel={(node: GalaxyNode) =>
          `${node.address.slice(0, 8)}…${node.address.slice(-4)} | Risk: ${(node.riskScore * 100).toFixed(1)}%`
        }
        onNodeClick={(node: GalaxyNode) => onNodeSelect(node)}
        linkColor={linkColor}
        linkWidth={linkWidth}
        linkOpacity={0.4}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={(link: GalaxyLink) => (link.valueEth > 5 ? 2 : 0.5)}
        linkDirectionalParticleSpeed={0.005}
        linkDirectionalParticleColor={linkColor}
        enableNodeDrag={true}
        enableNavigationControls={true}
        showNavInfo={false}
        d3AlphaDecay={0.01}
        d3VelocityDecay={0.3}
      />
    </div>
  );
}
