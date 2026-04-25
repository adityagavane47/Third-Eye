"""
backend/core/psi_engine.py — Pattern-Signature Intelligence Engine
Ported from Satark PSIEngine (Simulated Homomorphic Encryption + Pattern Matching)

Two-layer threat detection:
  Layer 1: PSI (Private Set Intersection) — checks wallet/contract addresses
            against known malicious sets using salted SHA-256 ciphertexts.
  Layer 2: Signature matching — detects known exploit patterns in tx graph structure.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("sentinel.psi_engine")


# ── Exploit Categories ────────────────────────────────────────────
class ExploitCategory(str, Enum):
    REENTRANCY = "reentrancy"
    FLASH_LOAN = "flash_loan"
    PRICE_MANIPULATION = "price_manipulation"
    SANDWICH_ATTACK = "sandwich_attack"
    GOVERNANCE_ATTACK = "governance_attack"
    BRIDGE_EXPLOIT = "bridge_exploit"
    PSI_ADDRESS_HIT = "psi_address_hit"    # Direct address match via PSI
    UNKNOWN = "unknown"


@dataclass
class SignatureMatch:
    """A confirmed pattern match against the exploit signature database."""
    signature_id: str
    category: ExploitCategory
    confidence: float                       # 0.0 → 1.0
    matched_addresses: list[str] = field(default_factory=list)
    description: str = ""
    cve_reference: str | None = None        # e.g., "SWC-107" for reentrancy


# ── Known Exploit Signatures ──────────────────────────────────────
SIGNATURE_DATABASE: list[dict] = [
    {
        "id": "PSI-001",
        "name": "Classic Reentrancy",
        "category": ExploitCategory.REENTRANCY,
        "pattern": "CALL → balance_check_missing → recursive_CALL",
        "swc": "SWC-107",
        "description": "Contract calls external address before updating internal state",
        # Heuristic thresholds used by match()
        "min_reentrancy_depth": 3,
    },
    {
        "id": "PSI-002",
        "name": "Flash Loan Price Oracle Manipulation",
        "category": ExploitCategory.FLASH_LOAN,
        "pattern": "flash_borrow → spot_price_query → swap → repay",
        "description": "Uses flash loan to temporarily distort DEX price oracle",
        "min_gas": 400_000,
        "min_tx_burst": 3,
    },
    {
        "id": "PSI-003",
        "name": "Governance Vote Manipulation",
        "category": ExploitCategory.GOVERNANCE_ATTACK,
        "pattern": "token_accumulation → proposal_creation → instant_vote → execute",
        "description": "Rapid token acquisition to pass malicious governance proposal",
        "min_unique_contracts": 4,
    },
    {
        "id": "PSI-004",
        "name": "Sandwich MEV Attack",
        "category": ExploitCategory.SANDWICH_ATTACK,
        "pattern": "frontrun_tx → victim_tx → backrun_tx",
        "description": "MEV bot sandwiches user transaction for guaranteed profit",
        "min_tx_burst": 5,
        "max_time_window_s": 30,
    },
    {
        "id": "PSI-005",
        "name": "Bridge Double-Spend Exploit",
        "category": ExploitCategory.BRIDGE_EXPLOIT,
        "pattern": "deposit → fake_relay → double_withdraw",
        "description": "Cross-chain bridge manipulated to withdraw more than deposited",
        "min_value_eth": 10.0,
    },
]


# ── Layer 1: Private Set Intersection (Satark Port) ───────────────
class SatarkPSI:
    """
    Simulated Private Set Intersection using salted SHA-256 hashes.

    In a production system this would use Paillier or ElGamal homomorphic
    encryption. For Sentinel Galaxy, we use SHA-256 to represent 'ciphertexts'
    so that plaintext addresses are never directly compared — preserving the
    PSI privacy model while being computationally feasible.

    Ported directly from Satark PSIEngine (Satark.sec/psi_engine.py).
    """

    SALT = "SATARK_PSI_SALT_2026"

    def __init__(self, salt: str = SALT):
        self.salt = salt
        # Known-malicious address ciphertexts (populated by load_blacklist)
        self._encrypted_blacklist: set[str] = set()
        logger.info("SatarkPSI initialized with salt prefix: %s…", salt[:10])

    def encrypt_set(self, tokens: list[str]) -> list[str]:
        """
        Simulates encrypting a set of tokens (addresses, tx hashes) into ciphertexts.
        Identical tokens always produce identical ciphertexts (deterministic).

        Args:
            tokens: List of plaintext addresses or identifiers

        Returns:
            List of SHA-256 hex ciphertexts
        """
        return [
            hashlib.sha256((self.salt + str(t).lower()).encode()).hexdigest()
            for t in tokens
        ]

    def intersect(self, set_a: list[str], set_b: list[str]) -> list[str]:
        """
        Calculates PSI intersection on 'encrypted' ciphertext sets.
        Returns the intersecting ciphertexts (cannot be reversed to plaintext).

        Args:
            set_a: First encrypted set
            set_b: Second encrypted set

        Returns:
            List of ciphertexts present in both sets
        """
        return list(set(set_a).intersection(set(set_b)))

    def load_blacklist(self, known_bad_addresses: list[str]) -> int:
        """
        Pre-encrypt a list of known malicious addresses into the internal blacklist.
        Call this once at startup with addresses from Neo4j or an external threat feed.

        Args:
            known_bad_addresses: List of plaintext 0x... addresses

        Returns:
            Number of addresses loaded
        """
        self._encrypted_blacklist = set(self.encrypt_set(known_bad_addresses))
        logger.info("PSI blacklist loaded: %d addresses encrypted", len(self._encrypted_blacklist))
        return len(self._encrypted_blacklist)

    def check_addresses(self, addresses: list[str]) -> list[str]:
        """
        Check a list of plaintext addresses against the encrypted blacklist via PSI.

        Args:
            addresses: List of plaintext 0x... addresses to check

        Returns:
            List of addresses that matched the blacklist (plaintext, recoverable from
            input since we hold both sides in this simulation)
        """
        if not self._encrypted_blacklist:
            return []

        encrypted_query = self.encrypt_set(addresses)
        hit_ciphertexts = set(self.intersect(encrypted_query, list(self._encrypted_blacklist)))

        # Map ciphertexts back to original addresses (we hold the plaintext side)
        hits = []
        for addr, cipher in zip(addresses, encrypted_query):
            if cipher in hit_ciphertexts:
                hits.append(addr)
        return hits


# ── Layer 2: Pattern-Signature Matching ───────────────────────────
def _extract_tx_features(tx_graph: list[dict]) -> dict:
    """Summarize a transaction graph into heuristic features for pattern matching."""
    if not tx_graph:
        return {}

    targets = [t.get("to", "") for t in tx_graph]
    gas_values = [t.get("gas_used", 21_000) for t in tx_graph]
    values = [t.get("value_eth", 0.0) for t in tx_graph]
    timestamps = sorted([t.get("timestamp", 0) for t in tx_graph if t.get("timestamp")])

    time_window_s = (timestamps[-1] - timestamps[0]) if len(timestamps) >= 2 else 9999

    return {
        "tx_count": len(tx_graph),
        "unique_contracts": len(set(targets)),
        "max_gas": max(gas_values),
        "max_value_eth": max(values) if values else 0.0,
        "reentrancy_depth": max(targets.count(t) for t in set(targets)) if targets else 0,
        "time_window_s": time_window_s,
    }


def _match_signature(sig: dict, features: dict) -> float:
    """
    Heuristic confidence score for a single signature against extracted features.
    Returns 0.0 if the pattern clearly doesn't match, >0 if it does.
    """
    sid = sig["id"]

    if sid == "PSI-001":  # Reentrancy
        depth = features.get("reentrancy_depth", 0)
        if depth >= sig.get("min_reentrancy_depth", 3):
            return min(0.5 + (depth - 3) * 0.1, 0.95)

    elif sid == "PSI-002":  # Flash loan
        if (features.get("max_gas", 0) >= sig.get("min_gas", 400_000) and
                features.get("tx_count", 0) >= sig.get("min_tx_burst", 3)):
            return 0.80

    elif sid == "PSI-003":  # Governance attack
        if features.get("unique_contracts", 0) >= sig.get("min_unique_contracts", 4):
            return 0.65

    elif sid == "PSI-004":  # Sandwich MEV
        if (features.get("tx_count", 0) >= sig.get("min_tx_burst", 5) and
                features.get("time_window_s", 9999) <= sig.get("max_time_window_s", 30)):
            return 0.75

    elif sid == "PSI-005":  # Bridge exploit
        if features.get("max_value_eth", 0) >= sig.get("min_value_eth", 10.0):
            return 0.60

    return 0.0


# ── Unified PSI Engine ────────────────────────────────────────────
class PSIEngine:
    """
    Sentinel Galaxy Pattern-Signature Intelligence Engine.

    Combines:
      - SatarkPSI (Layer 1): address-level PSI blacklist matching
      - Signature DB (Layer 2): heuristic exploit pattern matching on tx graph

    Interface contract with MLEngine:
        PSIEngine results augment MLEngine.risk_hints before Gemini analysis.
        tasks.py calls: psi_engine.match(wallet_address, tx_graph) → [SignatureMatch]
    """

    def __init__(self):
        self.psi = SatarkPSI()
        self.signatures = SIGNATURE_DATABASE
        logger.info(
            "PSIEngine initialized — %d signatures, PSI blacklist empty (call load_blacklist())",
            len(self.signatures),
        )

    def load_blacklist(self, known_bad_addresses: list[str]) -> int:
        """Populate the PSI blacklist. Call at startup with Neo4j flagged addresses."""
        return self.psi.load_blacklist(known_bad_addresses)

    def match(
        self,
        wallet_address: str,
        tx_graph: list[dict],
        related_addresses: list[str] | None = None,
    ) -> list[SignatureMatch]:
        """
        Full two-layer scan for a wallet.

        Layer 1: PSI check — is the wallet or any counterparty in the blacklist?
        Layer 2: Signature check — does the tx graph match known exploit patterns?

        Args:
            wallet_address:     Target wallet (0x...)
            tx_graph:           List of tx edge dicts from Neo4j
            related_addresses:  Additional addresses to PSI-check (counterparties)

        Returns:
            List of SignatureMatch objects sorted by confidence (highest first)
        """
        matches: list[SignatureMatch] = []

        # ── Layer 1: PSI Address Check ────────────────────────────
        all_addresses = [wallet_address] + (related_addresses or [])
        psi_hits = self.psi.check_addresses(all_addresses)
        if psi_hits:
            matches.append(SignatureMatch(
                signature_id="PSI-000",
                category=ExploitCategory.PSI_ADDRESS_HIT,
                confidence=0.95,
                matched_addresses=psi_hits,
                description=f"Address matched Sentinel Galaxy blacklist via PSI: {psi_hits}",
            ))
            logger.warning("PSI hit for %s — %d blacklisted address(es)", wallet_address, len(psi_hits))

        # ── Layer 2: Signature Pattern Matching ───────────────────
        if not tx_graph:
            logger.debug("PSIEngine.match(%s) — no tx_graph provided, skipping pattern check", wallet_address)
            return matches

        features = _extract_tx_features(tx_graph)

        for sig in self.signatures:
            confidence = _match_signature(sig, features)
            if confidence > 0.0:
                matches.append(SignatureMatch(
                    signature_id=sig["id"],
                    category=sig["category"],
                    confidence=confidence,
                    matched_addresses=[wallet_address],
                    description=sig["description"],
                    cve_reference=sig.get("swc"),
                ))
                logger.info(
                    "Signature match: %s [%s] confidence=%.2f for %s",
                    sig["id"], sig["name"], confidence, wallet_address,
                )

        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def get_signature_by_id(self, sig_id: str) -> dict | None:
        """Look up a signature definition by its PSI ID."""
        return next((s for s in self.signatures if s["id"] == sig_id), None)


# ── Module-level singleton (Satark backward compat) ───────────────
psi_service = SatarkPSI()
