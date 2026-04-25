import requests

def generate_report(wallet, risk_score, risk_hints):
    prompt = f"""
    You are a blockchain forensic analyst.

    Wallet: {wallet}
    Risk Score: {risk_score}

    Observations:
    {risk_hints}

    Explain clearly why this wallet is risky.
    """

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=5
        )

        return response.json()["response"]

    except:
        # Fallback (VERY IMPORTANT)
        report = f"Wallet {wallet} is flagged as HIGH RISK.\n\n"
        report += f"Risk Score: {risk_score}\n\nReasons:\n"

        for hint in risk_hints:
            report += f"- {hint}\n"

        return report