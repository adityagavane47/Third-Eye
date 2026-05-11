# 🛡️ Third Eye — On-Chain Immunity System

> *"The blockchain doesn't lie. But attackers do. We watch both."*

[![Built on Base](https://img.shields.io/badge/Built%20on-Base%20Sepolia-0052FF?style=flat-square&logo=coinbase)](https://base.org)
[![Powered by Gemini](https://img.shields.io/badge/AI-Gemini%203%20Flash-4285F4?style=flat-square&logo=google)](https://deepmind.google/technologies/gemini/)
[![Graph: Neo4j](https://img.shields.io/badge/Graph-Neo4j-008CC1?style=flat-square&logo=neo4j)](https://neo4j.com)
[![Auth: Privy](https://img.shields.io/badge/Auth-Privy-6C47FF?style=flat-square)](https://privy.io)

---

## 🌌 Vision

**Third Eye** is a real-time, AI-powered **On-Chain Immunity System** built on Base Sepolia. It visualizes the entire blockchain transaction graph as an interactive 3D galaxy, detects anomalies using ML-driven engines, and autonomously shields vulnerable contracts via smart contract enforcement — all explained in plain English by a Gemini-powered forensic AI agent.

Think of it as an **immune system for Web3**: constantly monitoring, learning from threats, and deploying antibodies (blacklists & shields) before exploits can propagate.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Third Eye                          │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  UI / Viz    │  Web3 Layer  │  AI Analyst  │  Data Layer   │
│  (React+3D)  │  (Privy+Sol) │  (Gemini)    │  (Neo4j+Fast) │
├──────────────┼──────────────┼──────────────┼───────────────┤
│ Galaxy3D.tsx │ useShield.ts │ forensic_    │ main.py       │
│ Sidebar.tsx  │ Guardian.sol │ agent.py     │ database.py   │
│ Dashboard    │ Base Sepolia │ tasks.py     │ seed_galaxy   │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

### Data Flow
```
Blockchain Events
      │
      ▼
FastAPI Ingestor ──► Neo4j Graph DB ──► 3D Force Graph (UI)
      │                    │
      ▼                    ▼
Celery + Redis      ML/PSI Engines
      │                    │
      ▼                    ▼
Gemini Agent ──────► Forensic Report (Sidebar)
      │
      ▼
ThirdEyeGuardian.sol ──► On-Chain Shield/Blacklist
```

---

## 📁 Directory Structure

```
Third Eye-galaxy/
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
│
├── backend/
│   ├── main.py                    # FastAPI entry point + HMAC middleware
│   ├── database.py                # Neo4j async driver
│   ├── tasks.py                   # Celery background tasks
│   ├── agent/
│   │   └── forensic_agent.py      # Gemini-powered forensic analysis
│   └── core/
│       ├── ml_engine.py           # ML anomaly detection (ThirdEye legacy)
│       ├── psi_engine.py          # Pattern-Signature Intelligence
│       └── audit.py               # On-chain audit trail logger
│
├── contracts/
│   ├── ThirdEyeGuardian.sol       # Shield + Blacklist contract
│   ├── package.json               # Solidity dependencies (OpenZeppelin)
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── components/
│       │   ├── Galaxy3D.tsx       # 3D force graph visualization
│       │   └── Sidebar.tsx        # Forensic Intelligence panel
│       └── pages/
│           └── Dashboard.tsx      # Main layout
│
└── scripts/
    └── seed_galaxy.py             # Populate Neo4j with 5,000 nodes
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, Node 20+, Docker
- Neo4j 5.x (local or AuraDB), Redis

### 1. Clone & Environment Setup
```bash
git clone https://github.com/your-org/Third Eye-galaxy.git
cd Third Eye-galaxy
cp .env.example .env

```

### 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Celery Worker
```bash
celery -A tasks worker --loglevel=info
```

### 4. Seed the Galaxy
```bash
python scripts/seed_galaxy.py
```

### 5. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 6. Deploy Contract (Base Sepolia)
```bash
cd backend
python deploy_contract.py
```

---

## 👥 Team Roles

| Role | Member | Ownership |
|------|--------|-----------|
| Root & Infrastructure | Aditya Gavane | `.gitignore`, `.env.example`, `README.md`, `docker-compose.yml` |
| Backend Architect | Aditya Gavane | `backend/main.py`, `backend/database.py`, `backend/core/`, `scripts/` |
| AI Analyst | Aayan Tamboli | `backend/agent/forensic_agent.py`, `backend/tasks.py` |
| Web3 Enforcer | Aditya Gavane | `contracts/ThirdEyeGuardian.sol`, `frontend/src/hooks/useShield.ts` |
| UI/Viz Designer | Aayan Tamboli | `frontend/src/components/`, `frontend/src/pages/Dashboard.tsx` |

---

## 🔐 Security Model

- **HMAC Validation**: All internal service-to-service calls validated via HMAC-SHA256
- **On-Chain Blacklist**: Malicious addresses flagged on-chain via `ThirdEyeGuardian.sol`
- **Privy Auth**: Gasless, email/social Web3 onboarding — no seed phrase exposure
- **Environment Isolation**: Zero secrets in source; all via `.env`

---

## 📜 License

MIT © 2026 Third Eye Team
