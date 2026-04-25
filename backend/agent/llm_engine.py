def generate_report(wallet, risk_score, risk_hints):
    report = f"Wallet {wallet} is flagged as HIGH RISK.\n\n"

    report += f"Risk Score: {risk_score}\n\n"
    report += "Reasons:\n"

    for hint in risk_hints:
        report += f"- {hint}\n"

    report += "\nThis behavior indicates potential malicious activity."

    return report