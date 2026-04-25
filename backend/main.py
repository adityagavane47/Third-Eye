"""
backend/main.py — Sentinel Galaxy FastAPI Entry Point
Role: Backend Architect (Member 3)

Responsibilities:
- CORS configuration for frontend
- HMAC-SHA256 middleware for internal service authentication
- Route registration for graph, anomaly, and forensic endpoints
- Health check endpoint
"""

import hashlib
import hmac
import logging
import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("sentinel.main")

HMAC_SECRET = os.getenv("HMAC_SECRET_KEY", "").encode()
CORS_ORIGINS = os.getenv("API_CORS_ORIGINS", "http://localhost:5173").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize connections on startup; clean up on shutdown."""
    from database import get_driver
    logger.info("🛡️  Sentinel Galaxy API starting up…")
    app.state.neo4j = get_driver()
    yield
    logger.info("🔴  Sentinel Galaxy API shutting down…")
    app.state.neo4j.close()


app = FastAPI(
    title="Sentinel Galaxy API",
    description="On-Chain Immunity System — Backend Data & AI Layer",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HMACValidationMiddleware:
    """
    Validates X-Sentinel-Signature header on internal service routes (/internal/*).
    Signature format: HMAC-SHA256(secret, f"{method}:{path}:{timestamp}:{body_hex}")
    Header format:    "t=<unix_ts>,v1=<hex_signature>"
    Replay window:    300 seconds
    """

    INTERNAL_PREFIX = "/internal"
    REPLAY_WINDOW_S = 300

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path

        if path.startswith(self.INTERNAL_PREFIX):
            error = await self._validate(request)
            if error:
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": error},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)

    async def _validate(self, request: Request) -> str | None:
        header = request.headers.get("X-Sentinel-Signature", "")
        if not header:
            return "Missing X-Sentinel-Signature header"

        try:
            parts = dict(p.split("=", 1) for p in header.split(","))
            timestamp = int(parts["t"])
            provided_sig = parts["v1"]
        except (KeyError, ValueError):
            return "Malformed X-Sentinel-Signature header"

        # Replay attack prevention
        if abs(time.time() - timestamp) > self.REPLAY_WINDOW_S:
            return "Signature timestamp outside replay window"

        body = await request.body()
        payload = f"{request.method}:{request.url.path}:{timestamp}:{body.hex()}"
        expected_sig = hmac.new(HMAC_SECRET, payload.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, provided_sig):
            return "Invalid HMAC signature"

        return None


app.add_middleware(HMACValidationMiddleware)



@app.get("/api/health", tags=["System"])
async def health_check():
    """Liveness probe for load balancers and CI pipelines."""
    return {"status": "ok", "service": "sentinel-galaxy-api", "version": "1.0.0"}


@app.get("/api/graph/nodes", tags=["Graph"])
async def get_graph_nodes(limit: int = 500, request: Request = None):
    """
    Fetch wallet nodes and their relationships from Neo4j.
    Returns data formatted for react-force-graph-3d.
    """
    driver = request.app.state.neo4j
    async with driver.session() as session:
        # 1. Fetch nodes up to the limit
        nodes_result = await session.run(
            "MATCH (w:Wallet) RETURN w LIMIT $limit", limit=limit
        )
        nodes_data = await nodes_result.data()
        
        # Format nodes for the frontend
        nodes = []
        addresses = []
        for record in nodes_data:
            w = record["w"]
            address = w.get("address")
            addresses.append(address)
            nodes.append({
                "id": address,
                "address": address,
                "label": w.get("label", "unknown"),
                "riskScore": w.get("risk_score", 0.0),
                "flagged": w.get("flagged", False),
                "txCount": w.get("tx_count", 0),
                "balanceEth": w.get("balance_eth", 0.0)
            })

        # 2. Fetch edges (links) only between the nodes we just loaded
        links_result = await session.run(
            "MATCH (s:Wallet)-[r:SENT_TO]->(t:Wallet) "
            "WHERE s.address IN $addresses AND t.address IN $addresses "
            "RETURN s.address AS source, t.address AS target, "
            "r.tx_hash AS txHash, r.value_eth AS valueEth",
            addresses=addresses
        )
        links_data = await links_result.data()

    return {"nodes": nodes, "links": links_data}


@app.post("/api/graph/flag", tags=["Graph"])
async def flag_wallet(wallet_address: str, risk_score: float, request: Request = None):
    """
    Mark a wallet node as malicious in Neo4j.
    TODO (Member 3): Write risk_score property and FLAGGED relationship.
    """
    return {"flagged": wallet_address, "risk_score": risk_score, "status": "TODO"}


@app.get("/api/forensic/report/{wallet_address}", tags=["AI Forensics"])
async def get_forensic_report(wallet_address: str):
    """
    Trigger AI forensic analysis for a wallet.
    Calls the Gemini-powered ForensicAgent.
    TODO (Member 1): Wire up ForensicAgent.analyze().
    """
    # from agent.forensic_agent import ForensicAgent
    # agent = ForensicAgent()
    # report = await agent.analyze(wallet_address)
    return {"address": wallet_address, "report": "TODO: AI analysis pending"}


@app.get("/api/anomalies", tags=["Detection"])
async def list_anomalies(min_risk: float = 0.7):
    """
    Return wallets with risk score above threshold.
    TODO (Member 1): Query Neo4j and return Celery task status.
    """
    return {"anomalies": [], "threshold": min_risk}
