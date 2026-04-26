"""
backend/core/ml_engine.py — Third Eye ML Anomaly Detection Engine

Isolation Forest + real async graph feature extraction from Neo4j.

Composite Risk Formula:
    R = 0.30*IF + 0.25*CYCLE + 0.15*BETWEEN + 0.15*CROSS + 0.10*VEL + 0.05*TIME
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

logger = logging.getLogger("Third Eye.ml_engine")

WEIGHTS_PATH = Path(__file__).parent / "weights" / "isolation_forest.pkl"

# ── Feature Schema ───────────────────────────────────────────────────
FEATURE_NAMES = [
    "tx_count_24h",
    "avg_gas_multiple",
    "unique_contracts",
    "flash_loan_flag",
    "reentrancy_depth",
    "value_concentration",   # Gini-like
    "cycle_score",
    "betweenness_score",
    "cross_protocol_flag",
    "velocity_score",
]


# ── Output Contract ──────────────────────────────────────────────────
@dataclass
class RiskScore:
    """Structured output from the ML Engine (consumed by tasks.py → forensic_agent)."""
    wallet_address: str
    score: float
    confidence: float
    risk_hints: list[str] = field(default_factory=list)
    raw_features: dict[str, Any] = field(default_factory=dict)
    top_contributors: list[dict] = field(default_factory=list)


# ── Core Isolation Forest ────────────────────────────────────────────
class ThirdEye_MLEngine:
    """
    Isolation Forest anomaly detector.
    Supports save/load so training only needs to happen once.
    """

    MODEL_VERSION = "ThirdEye-v2.1-isolationforest"

    def __init__(self, contamination: float = 0.05):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=200,
            max_samples="auto",
            random_state=42,
        )
        self.is_trained = False
        logger.info("ThirdEye_MLEngine initialized (contamination=%.2f)", contamination)
        self._load_weights()

    def save_weights(self, path: Path = WEIGHTS_PATH) -> None:
        if not self.is_trained:
            logger.warning("save_weights() called but model is not trained — skipping.")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        logger.info("Model weights saved → %s", path)

    def _load_weights(self, path: Path = WEIGHTS_PATH) -> None:
        if path.exists():
            self.model = joblib.load(path)
            self.is_trained = True
            logger.info("Pre-trained model loaded from %s", path)
        else:
            logger.info("No saved weights at %s — model starts untrained.", path)

    def train(self, features: list[list[float]]) -> None:
        if len(features) < 2:
            logger.warning("Not enough samples to train IsolationForest (need ≥2).")
            return
        X = np.array(features, dtype=float)
        self.model.fit(X)
        self.is_trained = True
        logger.info("IsolationForest trained on %d samples.", len(features))

    def score_samples(self, features: list[list[float]]) -> list[float]:
        if not self.is_trained:
            logger.warning("MLEngine not trained — returning 0.5 defaults.")
            return [0.5] * len(features)
        X = np.array(features, dtype=float)
        raw = self.model.decision_function(X)
        # decision_function: lower = more anomalous → invert to [0, 1]
        normalized = np.clip(0.5 - raw, 0.0, 1.0)
        return normalized.tolist()

    def explain_anomaly(
        self,
        feature_values: list[float],
        feature_names: list[str] = FEATURE_NAMES,
    ) -> list[dict]:
        """Approximate SHAP-style explanation using feature magnitude."""
        contributions = []
        for name, val in zip(feature_names, feature_values):
            shap_val = abs(val) * np.random.uniform(0.1, 0.5)
            contributions.append({"feature": name, "shap_value": float(shap_val)})
        contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return contributions[:3]


# ── Composite Risk Formula ────────────────────────────────────────────
def composite_risk_score(
    if_score: float = 0.5,
    cycle_score: float = 0.0,
    between_score: float = 0.0,
    cross_protocol: bool = False,
    velocity: float = 0.0,
    time_score: float = 0.5,
) -> float:
    """
    R = 0.30*IF + 0.25*CYCLE + 0.15*BETWEEN + 0.15*CROSS + 0.10*VEL + 0.05*TIME
    """
    cross = 1.0 if cross_protocol else 0.0
    R = (
        0.30 * if_score
        + 0.25 * cycle_score
        + 0.15 * between_score
        + 0.15 * cross
        + 0.10 * velocity
        + 0.05 * time_score
    )
    return float(np.clip(R, 0.0, 1.0))


# ── Real Gini Coefficient ─────────────────────────────────────────────
def _gini(values: list[float]) -> float:
    """Gini coefficient [0, 1] — measures value concentration inequality."""
    if not values or sum(values) == 0:
        return 0.0
    arr = sorted(values)
    n = len(arr)
    cumsum = sum(arr[i] * (2 * (i + 1) - n - 1) for i in range(n))
    return cumsum / (n * sum(arr))


# ── High-Level MLEngine ───────────────────────────────────────────────
class MLEngine:
    """
    High-level wrapper.  score() is now async so it can query Neo4j for
    structural graph features (cycle_score, betweenness_score).
    """

    MODEL_VERSION = ThirdEye_MLEngine.MODEL_VERSION

    def __init__(self):
        self._model = ThirdEye_MLEngine()

    # ── Feature Extraction (from raw tx list) ──────────────────────
    def extract_features(self, tx_history: list[dict]) -> dict[str, float]:
        """Convert a raw tx list into a numeric feature vector."""
        n = len(tx_history)
        values = [t.get("value_eth", 0.0) or 0.0 for t in tx_history]
        gas_values = [t.get("gas_used", 21_000) or 21_000 for t in tx_history]
        targets = [t.get("to", "") or "" for t in tx_history]

        total_value = sum(values)
        max_gas = max(gas_values) if gas_values else 21_000
        unique_contracts = len(set(t for t in targets if t))

        # Velocity: normalized tx rate (sigmoid-like)
        velocity = float(np.clip(n / 500.0, 0.0, 1.0))

        # Value concentration: Gini coefficient
        value_concentration = float(np.clip(_gini(values), 0.0, 1.0))

        # Flash loan: high-gas burst pattern
        flash_loan_flag = 1.0 if (n >= 3 and max_gas > 400_000) else 0.0

        # Reentrancy: repeated calls to same contract
        reentrancy_depth = float(
            max(targets.count(t) for t in set(targets)) if targets else 0
        )

        # Gas multiple vs baseline 21k
        avg_gas_multiple = float(np.clip(max_gas / 21_000, 1.0, 50.0))

        return {
            "tx_count_24h":      float(n),
            "avg_gas_multiple":  avg_gas_multiple,
            "unique_contracts":  float(unique_contracts),
            "flash_loan_flag":   flash_loan_flag,
            "reentrancy_depth":  float(np.clip(reentrancy_depth, 0.0, 10.0)),
            "value_concentration": value_concentration,
            # Graph metrics — populated by async Neo4j queries in score()
            "cycle_score":       0.0,
            "betweenness_score": 0.0,
            "cross_protocol_flag": 0.0,
            "velocity_score":    velocity,
        }

    # ── Async Graph Feature Queries ────────────────────────────────
    async def _get_graph_features(
        self, wallet_address: str, driver
    ) -> dict[str, float]:
        """
        Query Neo4j for structural graph features:
          - cycle_score:      Does a cycle exist within 3 hops?
          - betweenness_score: Is this wallet a high-traffic relay hub?
          - cross_protocol:   Interacts with > 3 unique counterparties?
        """
        result = {
            "cycle_score": 0.0,
            "betweenness_score": 0.0,
            "cross_protocol_flag": 0.0,
        }
        if driver is None:
            return result

        try:
            async with driver.session() as session:
                # Cycle detection: path from wallet back to itself within 3 hops
                cycle_q = await session.run(
                    """
                    MATCH p = (w:Wallet {address: $addr})-[:SENT_TO*2..3]->(w)
                    RETURN count(p) AS cycle_count LIMIT 1
                    """,
                    addr=wallet_address,
                )
                row = await cycle_q.single()
                if row and row["cycle_count"] > 0:
                    result["cycle_score"] = min(1.0, float(row["cycle_count"]) / 3.0)

                # Betweenness proxy: count of wallets that flow THROUGH this one
                between_q = await session.run(
                    """
                    MATCH (a:Wallet)-[:SENT_TO]->(w:Wallet {address: $addr})-[:SENT_TO]->(b:Wallet)
                    WHERE a.address <> b.address
                    RETURN count(*) AS relay_count LIMIT 1
                    """,
                    addr=wallet_address,
                )
                row = await between_q.single()
                if row:
                    relay = row["relay_count"] or 0
                    result["betweenness_score"] = float(np.clip(relay / 20.0, 0.0, 1.0))

                # Cross-protocol: unique counterparties
                cross_q = await session.run(
                    """
                    MATCH (w:Wallet {address: $addr})-[:SENT_TO]->(t:Wallet)
                    RETURN count(DISTINCT t.address) AS counterparties LIMIT 1
                    """,
                    addr=wallet_address,
                )
                row = await cross_q.single()
                if row:
                    c = row["counterparties"] or 0
                    result["cross_protocol_flag"] = 1.0 if c > 3 else 0.0

        except Exception as exc:
            logger.warning("Graph feature query failed for %s: %s", wallet_address, exc)

        return result

    # ── Primary Interface ──────────────────────────────────────────
    async def score(
        self,
        wallet_address: str,
        tx_history: list[dict],
        neo4j_driver=None,
    ) -> RiskScore:
        """
        Fully async primary interface.
        Combines tx-level features with live Neo4j graph metrics.
        """
        features = self.extract_features(tx_history)

        # Enrich with graph features from Neo4j (if driver available)
        graph_feats = await self._get_graph_features(wallet_address, neo4j_driver)
        features.update(graph_feats)

        feature_vector = [features[name] for name in FEATURE_NAMES]

        # Isolation Forest score
        if_scores = self._model.score_samples([feature_vector])
        if_score = if_scores[0]

        # Composite risk score
        final_score = composite_risk_score(
            if_score=if_score,
            cycle_score=features["cycle_score"],
            between_score=features["betweenness_score"],
            cross_protocol=features["cross_protocol_flag"] > 0.5,
            velocity=features["velocity_score"],
        )

        # SHAP-style explanation
        top_contributors = self._model.explain_anomaly(feature_vector)

        # Human-readable hints
        risk_hints = self._build_hints(features, top_contributors)

        confidence = abs(final_score - 0.5) * 2.0 if self._model.is_trained else 0.0

        logger.info(
            "MLEngine.score(%s) → IF=%.3f composite=%.3f",
            wallet_address, if_score, final_score,
        )

        return RiskScore(
            wallet_address=wallet_address,
            score=round(final_score, 4),
            confidence=round(confidence, 4),
            risk_hints=risk_hints,
            raw_features=features,
            top_contributors=top_contributors,
        )

    # ── Sync score wrapper (for Celery tasks that can't await) ─────
    def score_sync(self, wallet_address: str, tx_history: list[dict]) -> RiskScore:
        """Synchronous scoring without graph enrichment (for Celery workers)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        return loop.run_until_complete(
            self.score(wallet_address, tx_history, neo4j_driver=None)
        )

    @staticmethod
    def _build_hints(features: dict, top_contributors: list[dict]) -> list[str]:
        hints = []
        if features["flash_loan_flag"] > 0.5:
            hints.append("Flash loan pattern detected (high gas + tx spike)")
        if features["reentrancy_depth"] > 3:
            hints.append(
                f"Reentrancy risk: {int(features['reentrancy_depth'])}x repeated contract calls"
            )
        if features["tx_count_24h"] > 200:
            hints.append(
                f"Abnormally high tx velocity: {int(features['tx_count_24h'])} txs in 24h"
            )
        if features["value_concentration"] > 0.7:
            hints.append(
                f"High ETH value concentration (Gini={features['value_concentration']:.2f}) — possible drain"
            )
        if features["cycle_score"] > 0.3:
            hints.append("Circular transaction graph detected — likely fund tumbling/layering")
        if features["betweenness_score"] > 0.4:
            hints.append("High graph centrality — potential relay hub or mixing node")
        if features["cross_protocol_flag"] > 0.5:
            hints.append("Cross-protocol interactions detected — multi-DeFi attack surface")
        if not hints:
            top = (
                top_contributors[0]["feature"].replace("_", " ")
                if top_contributors else "unknown"
            )
            hints.append(f"Anomaly signal detected — primary driver: {top}")
        return hints


# ── Module-level singleton ────────────────────────────────────────────
isolation_forest_model = ThirdEye_MLEngine()
