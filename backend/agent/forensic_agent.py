"""
backend/agent/forensic_agent.py — Gemini-Powered Forensic AI Agent
Role: AI Analyst (Member 1)

Responsibilities:
- Accept RiskScore output from MLEngine + SignatureMatch from PSIEngine
- Construct a rich prompt for Gemini 3 Flash
- Return a structured ForensicReport for the frontend Sidebar
- Cache reports in Redis to avoid redundant API calls
"""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("sentinel.forensic_agent")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
REPORT_CACHE_TTL_S = 300  # 5-minute Redis TTL for cached reports

genai.configure(api_key=GEMINI_API_KEY)


@dataclass
class ForensicReport:
    """Structured output from the Gemini ForensicAgent."""
    wallet_address: str
    risk_level: str                            # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    executive_summary: str                     # 2-3 sentence TL;DR
    threat_narrative: str                      # Full investigative prose
    recommended_actions: list[str] = field(default_factory=list)
    confidence_assessment: str = ""
    data_sources: list[str] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)
    model_used: str = GEMINI_MODEL


# ── System Prompt ────────────────────────────────────────────
FORENSIC_SYSTEM_PROMPT = """You are SENTINEL — an elite blockchain forensic AI embedded in the 
Sentinel Galaxy On-Chain Immunity System. Your role is to analyze anomalous blockchain activity 
and produce investigative reports that a human analyst or DeFi protocol owner can immediately act on.

You write with the authority of a seasoned security researcher, the clarity of a technical writer, 
and the urgency of a threat intel analyst. You cite specific patterns, explain the mechanics of 
potential exploits, and always end with concrete, prioritized action items.

Output format (strict JSON):
{
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "executive_summary": "<2-3 sentence TL;DR>",
  "threat_narrative": "<full investigative report, 200-400 words>",
  "recommended_actions": ["<action 1>", "<action 2>", ...],
  "confidence_assessment": "<explanation of model confidence and data gaps>"
}"""


class ForensicAgent:
    """
    AI Forensic Analyst powered by Google Gemini.

    Pipeline:
        ML RiskScore + PSI SignatureMatches
              │
              ▼
        _build_prompt()
              │
              ▼
        Gemini 3 Flash API
              │
              ▼
        ForensicReport (cached in Redis)
    """

    def __init__(self, redis_client=None):
        """
        Args:
            redis_client: Optional Redis client for report caching.
                          If None, caching is disabled (dev mode).
        """
        self._model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=FORENSIC_SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=0.3,      # Low temp for factual, consistent analysis
                top_p=0.95,
                max_output_tokens=1024,
                response_mime_type="application/json",
            ),
        )
        self._redis = redis_client
        logger.info("ForensicAgent initialized with model: %s", GEMINI_MODEL)

    def _cache_key(self, wallet_address: str) -> str:
        return f"forensic_report:{wallet_address.lower()}"

    async def _get_cached(self, wallet_address: str) -> ForensicReport | None:
        """Retrieve a cached ForensicReport from Redis if available."""
        if not self._redis:
            return None
        try:
            raw = await self._redis.get(self._cache_key(wallet_address))
            if raw:
                logger.debug("Cache HIT for %s", wallet_address)
                return ForensicReport(**json.loads(raw))
        except Exception as exc:
            logger.warning("Redis cache read failed: %s", exc)
        return None

    async def _set_cached(self, report: ForensicReport):
        """Store a ForensicReport in Redis with TTL."""
        if not self._redis:
            return
        try:
            await self._redis.setex(
                self._cache_key(report.wallet_address),
                REPORT_CACHE_TTL_S,
                json.dumps(asdict(report)),
            )
        except Exception as exc:
            logger.warning("Redis cache write failed: %s", exc)

    def _build_prompt(
        self,
        wallet_address: str,
        risk_score: float,
        confidence: float,
        risk_hints: list[str],
        signature_matches: list[dict] | None = None,
        tx_summary: dict | None = None,
    ) -> str:
        """
        Construct the user-turn prompt for Gemini.
        Combines ML signals, PSI matches, and raw transaction context.
        """
        sig_block = ""
        if signature_matches:
            sigs = "\n".join(
                f"  - [{m.get('id')}] {m.get('name')}: {m.get('description')}"
                for m in signature_matches
            )
            sig_block = f"\nKNOWN EXPLOIT PATTERN MATCHES:\n{sigs}"

        tx_block = ""
        if tx_summary:
            tx_block = f"\nTRANSACTION CONTEXT:\n{json.dumps(tx_summary, indent=2)}"

        return f"""FORENSIC ANALYSIS REQUEST
========================
Wallet Address: {wallet_address}
ML Risk Score:  {risk_score:.3f} / 1.000
ML Confidence:  {confidence:.1%}

DETECTED RISK SIGNALS (from ML Engine):
{chr(10).join(f'  • {hint}' for hint in risk_hints)}
{sig_block}
{tx_block}

Provide a comprehensive forensic investigation report for this wallet.
Focus on: likely attack vector, affected protocols, estimated impact, 
and specific on-chain evidence that would confirm or refute the threat."""

    async def analyze(
        self,
        wallet_address: str,
        risk_score: float,
        confidence: float,
        risk_hints: list[str],
        signature_matches: list[dict] | None = None,
        tx_summary: dict | None = None,
    ) -> ForensicReport:
        """
        Primary interface — runs full forensic analysis on a wallet.

        Args:
            wallet_address:     0x... address to investigate
            risk_score:         Float 0-1 from MLEngine
            confidence:         Model confidence in risk_score
            risk_hints:         Human-readable signals from MLEngine
            signature_matches:  List of PSI SignatureMatch dicts (optional)
            tx_summary:         Raw transaction context dict (optional)

        Returns:
            ForensicReport — fully structured AI-generated investigation
        """
        # 1. Check cache
        cached = await self._get_cached(wallet_address)
        if cached:
            return cached

        # 2. Build prompt
        prompt = self._build_prompt(
            wallet_address, risk_score, confidence, risk_hints,
            signature_matches, tx_summary,
        )

        # 3. Call Gemini
        logger.info("Calling Gemini for forensic analysis of %s…", wallet_address)
        try:
            response = await self._model.generate_content_async(prompt)
            payload = json.loads(response.text)
        except json.JSONDecodeError as exc:
            logger.error("Gemini returned non-JSON response: %s", exc)
            payload = {
                "risk_level": "UNKNOWN",
                "executive_summary": "Analysis failed — model returned malformed output.",
                "threat_narrative": response.text if "response" in dir() else "No response.",
                "recommended_actions": ["Retry analysis", "Manual review required"],
                "confidence_assessment": "Low — JSON parsing failed",
            }
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise

        # 4. Construct report
        report = ForensicReport(
            wallet_address=wallet_address,
            data_sources=["MLEngine v2.1", "PSIEngine", "Neo4j Graph DB"],
            **payload,
        )

        # 5. Cache and return
        await self._set_cached(report)
        logger.info(
            "Forensic report generated: %s | risk=%s",
            wallet_address,
            report.risk_level,
        )
        return report
