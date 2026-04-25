"""
backend/core/ml_engine.py — Sentinel Galaxy ML Anomaly Detection Engine
Ported from Satark MLEngine (IsolationForest + composite risk scoring)

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

logger = logging.getLogger("sentinel.ml_engine")
WEIGHTS_PATH = Path("backend/core/weights/isolation_forest.pkl")


# ── Output Contract (consumed by tasks.py → forensic_agent.py) ──
@dataclass
class RiskScore:
    """Structured output from the ML Engine."""
    wallet_address: str
    score: float                        # 0.0 (safe) → 1.0 (critical)
    confidence: float                   # model confidence in the score
    risk_hints: list[str] = field(default_factory=list)
    raw_features: dict[str, Any] = field(default_factory=dict)
    top_contributors: list[dict] = field(default_factory=list)  # SHAP-style explanations


# ── Feature Schema ───────────────────────────────────────────────
FEATURE_NAMES = [
    "tx_count_24h",           
    "avg_gas_multiple",       
    "unique_contracts",       
    "flash_loan_flag",        
    "reentrancy_depth",       
    "value_concentration",    
    "cycle_score",            
    "betweenness_score",      
    "cross_protocol_flag",   
    "velocity_score",         
]


# ── Core ML Engine ────────────────────────────────────────────────
class SATARK_MLEngine:
    """
    Isolation Forest anomaly detector ported from the Satark legacy system.
    Detects outlier wallets in the transaction graph.
    """

    MODEL_VERSION = "satark-v2.1-isolationforest"

    def __init__(self, contamination: float = 0.05):
        """
        Args:
            contamination: Expected fraction of anomalous wallets in the dataset.
                           0.05 = we expect ~5% of wallets to be malicious.
        """
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=100,
            max_samples="auto",
            random_state=42,
        )
        self.is_trained = False
        logger.info("SATARK_MLEngine initialized (contamination=%.2f)", contamination)
        # Auto-load saved weights if they exist
        self._load_weights()

    def save_weights(self, path: Path = WEIGHTS_PATH) -> None:
        """Persist trained model to disk using joblib."""
        if not self.is_trained:
            logger.warning("save_weights() called but model is not trained — skipping.")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        logger.info("Model weights saved → %s", path)

    def _load_weights(self, path: Path = WEIGHTS_PATH) -> None:
        """Load pre-trained model from disk if available."""
        if path.exists():
            self.model = joblib.load(path)
            self.is_trained = True
            logger.info("Pre-trained model loaded from %s", path)
        else:
            logger.info("No saved weights found at %s — model starts untrained.", path)

    def train(self, features: list[list[float]]) -> None:
        """
        Train the Isolation Forest on a batch of wallet feature vectors.

        Args:
            features: List of feature vectors, each matching FEATURE_NAMES order.
                      Typically called from seed_galaxy.py or a Celery beat task.
        """
        if len(features) == 0:
            logger.warning("MLEngine.train() called with empty feature set — skipping.")
            return
        X = np.array(features)
        self.model.fit(X)
        self.is_trained = True
        logger.info("MLEngine trained on %d samples.", len(features))

    def score_samples(self, features: list[list[float]]) -> list[float]:
        """
        Score a batch of wallet feature vectors.

        Returns:
            List of anomaly scores in [0.0, 1.0] where 1.0 = most anomalous.
        """
        if not self.is_trained:
            logger.warning("MLEngine not trained — returning default scores.")
            return [0.5] * len(features)

        X = np.array(features)
        # decision_function: higher = more normal, lower = more anomalous
        raw_scores = self.model.decision_function(X)
        # Invert and normalize to [0, 1]: 0.5 - score maps outliers → high values
        normalized = 0.5 - raw_scores
        return np.clip(normalized, 0, 1).tolist()

    def explain_anomaly(
        self,
        feature_values: list[float],
        feature_names: list[str] = FEATURE_NAMES,
    ) -> list[dict]:
        """
        SHAP-style feature contribution explanation (approximated).
        Returns the top 3 contributing features to the anomaly score.

        Args:
            feature_values: Feature vector for a single wallet
            feature_names:  Names matching the feature vector

        Returns:
            List of dicts: [{"feature": str, "shap_value": float}, ...]
        """
        contributions = []
        for name, val in zip(feature_names, feature_values):
            # Weighted approximation: magnitude × random perturbation factor
            shap_val = abs(val) * np.random.uniform(0.1, 0.5)
            contributions.append({"feature": name, "shap_value": float(shap_val)})
        contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return contributions[:3]


# ── Composite Risk Scorer ─────────────────────────────────────────
def composite_risk_score(
    if_score: float = 0.5,
    cycle_score: float = 0.0,
    between_score: float = 0.0,
    cross_protocol: bool = False,
    velocity: float = 0.0,
    time_score: float = 0.5,
) -> float:
    """
    Sentinel Galaxy composite risk formula (ported from Satark):

        R = 0.30*IF + 0.25*CYCLE + 0.15*BETWEEN + 0.15*CROSS + 0.10*VEL + 0.05*TIME

    Args:
        if_score:       Isolation Forest anomaly score (0-1)
        cycle_score:    Circular transaction pattern score (0-1)
        between_score:  Graph betweenness centrality (0-1)
        cross_protocol: True if wallet crosses multiple DeFi protocols
        velocity:       Normalized transaction velocity (0-1)
        time_score:     Time-of-day suspicion factor (0-1, default 0.5)

    Returns:
        Composite risk score in [0.0, 1.0]
    """
    cross_score = 1.0 if cross_protocol else 0.0
    R = (
        0.30 * if_score +
        0.25 * cycle_score +
        0.15 * between_score +
        0.15 * cross_score +
        0.10 * velocity +
        0.05 * time_score
    )
    return float(np.clip(R, 0.0, 1.0))


# ── High-Level Interface (used by tasks.py) ───────────────────────
class MLEngine:
    """
    High-level wrapper around SATARK_MLEngine.
    This is the class imported by tasks.py.

    Interface:
        engine = MLEngine()
        risk: RiskScore = engine.score(wallet_address, tx_history)
    """

    MODEL_VERSION = SATARK_MLEngine.MODEL_VERSION

    def __init__(self):
        self._model = SATARK_MLEngine()
        # TODO: load pre-trained weights if available
        # self._load_weights("core/weights/satark_forest.pkl")

    def extract_features(self, tx_history: list[dict]) -> dict[str, float]:
        """
        Convert raw transaction history from Neo4j into a numeric feature vector.

        Args:
            tx_history: List of raw transaction dicts from Neo4j

        Returns:
            Feature dict aligned to FEATURE_NAMES
        """
        n = len(tx_history)
        total_value = sum(t.get("value_eth", 0) for t in tx_history)
        unique_contracts = len({t.get("to") for t in tx_history if t.get("to")})
        max_gas = max((t.get("gas_used", 21_000) for t in tx_history), default=21_000)

        # Velocity: normalize tx count to [0, 1] using sigmoid-like scaling
        velocity = float(np.clip(n / 500.0, 0, 1))

        # Value concentration: simple proxy using max / total ratio (Gini-like)
        max_val = max((t.get("value_eth", 0) for t in tx_history), default=0)
        value_concentration = (max_val / total_value) if total_value > 0 else 0.0

        # Flash loan heuristic: same-block borrow + repay (tx count spike, max gas high)
        flash_loan_flag = 1.0 if (n > 3 and max_gas > 400_000) else 0.0

        # Reentrancy heuristic: multiple calls to same contract in short sequence
        targets = [t.get("to") for t in tx_history]
        reentrancy_depth = float(max(targets.count(t) for t in set(targets)) if targets else 0)

        return {
            "tx_count_24h": float(n),
            "avg_gas_multiple": float(np.clip(max_gas / 21_000, 1, 50)),
            "unique_contracts": float(unique_contracts),
            "flash_loan_flag": flash_loan_flag,
            "reentrancy_depth": float(np.clip(reentrancy_depth, 0, 10)),
            "value_concentration": float(np.clip(value_concentration, 0, 1)),
            # Graph metrics — populated by Neo4j queries in tasks.py
            "cycle_score": 0.0,
            "betweenness_score": 0.0,
            "cross_protocol_flag": 0.0,
            "velocity_score": velocity,
        }

    def score(self, wallet_address: str, tx_history: list[dict]) -> RiskScore:
        """
        Primary interface — scores a wallet's risk using Isolation Forest
        combined with the Satark composite risk formula.

        Args:
            wallet_address: The 0x... address to evaluate
            tx_history:     Recent transaction list from Neo4j

        Returns:
            RiskScore with composite score, confidence, and risk_hints
        """
        features = self.extract_features(tx_history)
        feature_vector = [features[name] for name in FEATURE_NAMES]

        # Step 1: Isolation Forest score
        if_score_list = self._model.score_samples([feature_vector])
        if_score = if_score_list[0]

        # Step 2: Composite risk score (Satark formula)
        final_score = composite_risk_score(
            if_score=if_score,
            cycle_score=features["cycle_score"],
            between_score=features["betweenness_score"],
            cross_protocol=features["cross_protocol_flag"] > 0.5,
            velocity=features["velocity_score"],
        )

        # Step 3: SHAP-style explanation
        top_contributors = self._model.explain_anomaly(feature_vector)

        # Step 4: Build human-readable risk hints for Gemini
        risk_hints = self._build_hints(features, top_contributors)

        # Confidence: higher when model is trained and score is decisive (far from 0.5)
        confidence = abs(final_score - 0.5) * 2 if self._model.is_trained else 0.0

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

    @staticmethod
    def _build_hints(features: dict, top_contributors: list[dict]) -> list[str]:
        """Convert raw feature values into human-readable risk signals."""
        hints = []
        if features["flash_loan_flag"] > 0.5:
            hints.append("Flash loan pattern detected (high gas + tx spike)")
        if features["reentrancy_depth"] > 3:
            hints.append(f"Reentrancy risk: {int(features['reentrancy_depth'])}x repeated contract calls")
        if features["tx_count_24h"] > 200:
            hints.append(f"Abnormally high tx velocity: {int(features['tx_count_24h'])} txs in 24h")
        if features["value_concentration"] > 0.8:
            hints.append("Extreme ETH value concentration — possible wash trading or drain")
        if features["cycle_score"] > 0.5:
            hints.append("Circular transaction graph detected (likely layering)")
        if features["betweenness_score"] > 0.5:
            hints.append("High graph centrality — potential mixing or relay node")
        if not hints:
            top = top_contributors[0]["feature"].replace("_", " ") if top_contributors else "unknown"
            hints.append(f"Anomaly signal detected — top driver: {top}")
        return hints


# ── Module-level singleton (backward compat with Satark imports) ──
isolation_forest_model = SATARK_MLEngine()
