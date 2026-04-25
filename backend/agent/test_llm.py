from risk_engine import calculate_risk
from llm_engine import generate_report
from audit import log_decision
from psi_engine import mock_psi

# Simulated transaction data (later comes from backend/DB)
transaction_data = {
    "wallet": "0xABC123",
    "tx_count": 50,
    "cycle_detected": True,
    "connected_to_bad_wallet": True
}

# Step 1: Calculate risk
risk_score, risk_hints = calculate_risk(transaction_data)

# Step 2: Generate report
report = generate_report(transaction_data["wallet"], risk_score, risk_hints)

print(report)

log_decision(transaction_data["wallet"], risk_score, risk_hints)

# Mock PSI test
local_blacklist = ["0xABC123", "0xDEF456", "0xXYZ999"]
external_blacklist = ["0x111111", "0xABC123", "0x222222"]

common = mock_psi(local_blacklist, external_blacklist)

print("\nCommon Blacklisted Wallets (PSI):", common)