#!/usr/bin/env python3
"""
scripts/seed_galaxy.py — Neo4j Galaxy Seeder
Role: Backend Architect (Member 3)

Populates the Neo4j database with 5,000 synthetic wallet nodes
and randomized transaction relationships to bootstrap the 3D Galaxy visualization.

Usage:
    python scripts/seed_galaxy.py [--nodes 5000] [--reset]

Node schema:
    (:Wallet {
        address:       "0x...",    # Ethereum-format hex address
        risk_score:    float,      # 0.0 → 1.0
        flagged:       bool,
        label:         str,        # "whale" | "defi_user" | "bot" | "exchange" | "attacker"
        tx_count:      int,
        first_seen:    datetime,
        last_seen:     datetime,
        balance_eth:   float,
    })

Relationship schema:
    (:Wallet)-[:SENT_TO {
        tx_hash:    "0x...",
        value_eth:  float,
        timestamp:  datetime,
        gas_used:   int,
    }]->(:Wallet)
"""

import argparse
import asyncio
import logging
import os
import random
import sys
import time
from pathlib import Path

# Add backend to path for database imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("seed_galaxy")

# ── Configuration ─────────────────────────────────────────────
TOTAL_NODES = 5_000
BATCH_SIZE = 250           # Nodes per Neo4j transaction
RELATIONSHIP_DENSITY = 3   # Avg relationships per node
ATTACKER_RATIO = 0.03      # 3% of nodes are simulated attackers
WHALE_RATIO = 0.05         # 5% are whales

WALLET_LABELS = ["defi_user", "bot", "exchange", "whale", "attacker", "unknown"]

HEX_CHARS = "0123456789abcdef"


def random_address() -> str:
    """Generate a realistic-looking Ethereum wallet address."""
    return "0x" + "".join(random.choices(HEX_CHARS, k=40))


def random_tx_hash() -> str:
    """Generate a realistic-looking transaction hash."""
    return "0x" + "".join(random.choices(HEX_CHARS, k=64))


def assign_label(risk_score: float) -> str:
    """Assign wallet label based on risk profile."""
    if risk_score > 0.85:
        return "attacker"
    elif risk_score > 0.7:
        return "bot"
    elif random.random() < WHALE_RATIO:
        return "whale"
    elif random.random() < 0.3:
        return "exchange"
    else:
        return "defi_user"


def generate_wallets(count: int) -> list[dict]:
    """
    Generate synthetic wallet data with realistic risk distributions.
    Uses a beta distribution to create a long tail of high-risk wallets.
    """
    wallets = []
    now = time.time()

    for i in range(count):
        # Beta distribution: most wallets are low-risk, few are high-risk
        risk_score = round(random.betavariate(0.8, 5.0), 4)
        label = assign_label(risk_score)

        wallet = {
            "address": random_address(),
            "risk_score": risk_score,
            "flagged": risk_score > 0.85,
            "label": label,
            "tx_count": random.randint(1, 10_000),
            "balance_eth": round(random.uniform(0.001, 500.0), 6),
            "first_seen": now - random.randint(86400, 86400 * 730),  # Up to 2 years ago
            "last_seen": now - random.randint(0, 86400 * 30),
            "x": random.uniform(-300, 300),   # 3D position hint for force graph
            "y": random.uniform(-300, 300),
            "z": random.uniform(-300, 300),
        }
        wallets.append(wallet)

        if (i + 1) % 500 == 0:
            logger.info("Generated %d / %d wallets…", i + 1, count)

    return wallets


def generate_relationships(wallets: list[dict], density: int) -> list[dict]:
    """
    Generate randomized SENT_TO edges between wallets.
    High-risk wallets have more connections (simulating attack propagation).
    """
    relationships = []
    addresses = [w["address"] for w in wallets]
    now = time.time()

    for wallet in wallets:
        # Attackers have higher connectivity
        n_rels = density + (3 if wallet["label"] == "attacker" else 0)
        for _ in range(random.randint(1, n_rels)):
            target = random.choice(addresses)
            if target == wallet["address"]:
                continue
            relationships.append({
                "from": wallet["address"],
                "to": target,
                "tx_hash": random_tx_hash(),
                "value_eth": round(random.uniform(0.001, 100.0), 6),
                "timestamp": now - random.randint(0, 86400 * 365),
                "gas_used": random.randint(21_000, 500_000),
            })

    logger.info("Generated %d relationships", len(relationships))
    return relationships


async def seed(reset: bool = False, total_nodes: int = TOTAL_NODES):
    """Main seeding coroutine."""
    from database import apply_schema, get_driver, run_query

    driver = get_driver()

    if reset:
        logger.warning("⚠️  RESET flag set — deleting all existing nodes…")
        await run_query("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared.")

    # Apply schema constraints
    await apply_schema()

    # Generate data
    logger.info("Generating %d wallet nodes…", total_nodes)
    wallets = generate_wallets(total_nodes)
    relationships = generate_relationships(wallets, RELATIONSHIP_DENSITY)

    # ── Seed Wallet Nodes (batched) ──────────────────────────
    logger.info("Seeding %d wallet nodes in batches of %d…", len(wallets), BATCH_SIZE)
    t0 = time.time()

    async with driver.session() as session:
        for batch_start in range(0, len(wallets), BATCH_SIZE):
            batch = wallets[batch_start : batch_start + BATCH_SIZE]
            await session.run(
                """
                UNWIND $wallets AS w
                MERGE (wallet:Wallet {address: w.address})
                SET wallet += {
                    risk_score:  w.risk_score,
                    flagged:     w.flagged,
                    label:       w.label,
                    tx_count:    w.tx_count,
                    balance_eth: w.balance_eth,
                    first_seen:  datetime({epochSeconds: toInteger(w.first_seen)}),
                    last_seen:   datetime({epochSeconds: toInteger(w.last_seen)}),
                    x: w.x, y: w.y, z: w.z
                }
                """,
                wallets=batch,
            )
            logger.info(
                "Nodes seeded: %d / %d",
                min(batch_start + BATCH_SIZE, len(wallets)),
                len(wallets),
            )

    # ── Seed Relationships (batched) ─────────────────────────
    logger.info("Seeding %d SENT_TO relationships…", len(relationships))

    async with driver.session() as session:
        for batch_start in range(0, len(relationships), BATCH_SIZE):
            batch = relationships[batch_start : batch_start + BATCH_SIZE]
            await session.run(
                """
                UNWIND $rels AS r
                MATCH (from:Wallet {address: r.from})
                MATCH (to:Wallet {address: r.to})
                MERGE (from)-[tx:SENT_TO {tx_hash: r.tx_hash}]->(to)
                SET tx += {
                    value_eth: r.value_eth,
                    timestamp: datetime({epochSeconds: toInteger(r.timestamp)}),
                    gas_used:  r.gas_used
                }
                """,
                rels=batch,
            )
            logger.info(
                "Relationships seeded: %d / %d",
                min(batch_start + BATCH_SIZE, len(relationships)),
                len(relationships),
            )

    elapsed = time.time() - t0
    logger.info(
        "✅ Galaxy seeded: %d nodes, %d relationships in %.1fs",
        len(wallets),
        len(relationships),
        elapsed,
    )

    # ── Summary Stats ────────────────────────────────────────
    stats = await run_query(
        "MATCH (w:Wallet) RETURN w.label AS label, count(w) AS count ORDER BY count DESC"
    )
    logger.info("Label distribution:")
    for row in stats:
        logger.info("  %-15s %d", row["label"], row["count"])

    driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Sentinel Galaxy Neo4j database")
    parser.add_argument("--nodes", type=int, default=TOTAL_NODES, help="Number of wallet nodes")
    parser.add_argument("--reset", action="store_true", help="Delete all existing data first")
    args = parser.parse_args()

    asyncio.run(seed(reset=args.reset, total_nodes=args.nodes))
