"""
backend/core/audit.py — On-Chain Audit Trail Logger
Role: Backend Architect (Member 3) — Satark Legacy Placeholder

Maintains an immutable audit log of all Sentinel Galaxy detection events,
shield activations, and forensic reports for compliance and forensics.

Member 3 TODO:
- Integrate with Neo4j AuditEvent nodes
- Add webhook emission for real-time dashboard updates
- Optionally submit audit hashes to Base Sepolia for tamper-evidence
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger("sentinel.audit")

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "logs/audit.jsonl"))


class EventType(str, Enum):
    ANOMALY_DETECTED = "anomaly_detected"
    FORENSIC_REPORT_GENERATED = "forensic_report_generated"
    SHIELD_ACTIVATED = "shield_activated"
    WALLET_BLACKLISTED = "wallet_blacklisted"
    WALLET_WHITELISTED = "wallet_whitelisted"
    SYSTEM_STARTUP = "system_startup"


@dataclass
class AuditEvent:
    """Immutable record of a Sentinel Galaxy detection or action."""
    event_type: EventType
    wallet_address: str
    timestamp: float = field(default_factory=time.time)
    risk_score: float | None = None
    details: dict = field(default_factory=dict)
    triggered_by: str = "system"           # "system" | "analyst" | "contract"
    tx_hash: str | None = None             # On-chain tx if shield was activated
    checksum: str = ""                     # SHA-256 of event payload (set on save)

    def compute_checksum(self) -> str:
        """SHA-256 fingerprint of the event payload (excludes checksum field)."""
        payload = {k: v for k, v in asdict(self).items() if k != "checksum"}
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()


class AuditLogger:
    """
    Append-only audit event logger.

    Events are written as JSON lines to disk and (TODO) stored as
    Neo4j :AuditEvent nodes linked to :Wallet nodes.
    """

    def __init__(self, log_path: Path = AUDIT_LOG_PATH):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: AuditEvent) -> AuditEvent:
        """
        Persist an audit event to the JSONL log file.

        Computes checksum before writing so the record is tamper-detectable.
        Returns the event with checksum populated.
        """
        event.checksum = event.compute_checksum()

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), default=str) + "\n")

        logger.info(
            "AUDIT | %s | %s | risk=%.2f",
            event.event_type,
            event.wallet_address,
            event.risk_score or 0.0,
        )

        # TODO (Member 3): Also write to Neo4j
        # await run_query(
        #     "CREATE (e:AuditEvent $props)-[:CONCERNS]->(w:Wallet {address: $addr})",
        #     {"props": asdict(event), "addr": event.wallet_address}
        # )

        return event

    def log_anomaly(self, wallet: str, risk_score: float, hints: list[str]) -> AuditEvent:
        event = AuditEvent(
            event_type=EventType.ANOMALY_DETECTED,
            wallet_address=wallet,
            risk_score=risk_score,
            details={"risk_hints": hints},
        )
        return self.record(event)

    def log_shield(self, wallet: str, tx_hash: str, triggered_by: str = "system") -> AuditEvent:
        event = AuditEvent(
            event_type=EventType.SHIELD_ACTIVATED,
            wallet_address=wallet,
            triggered_by=triggered_by,
            tx_hash=tx_hash,
        )
        return self.record(event)

    def log_forensic_report(self, wallet: str, report_summary: str) -> AuditEvent:
        event = AuditEvent(
            event_type=EventType.FORENSIC_REPORT_GENERATED,
            wallet_address=wallet,
            details={"summary": report_summary[:500]},
        )
        return self.record(event)


# Module-level singleton for convenience imports
audit_logger = AuditLogger()
