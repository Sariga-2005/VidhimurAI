import json

data = json.load(open("app/data/kanoon_raw.json"))
print(f"Total cases: {len(data)}")

# Check for sexual harassment cases
sexual = [
    c for c in data
    if any(
        "sexual" in str(v).lower() or "posh" in str(v).lower() or "vishaka" in str(v).lower()
        for v in [
            c.get("keywords", []),
            c.get("legal_issues", []),
            c.get("summary", ""),
            c.get("case_name", ""),
            c.get("statutes_referenced", []),
        ]
    )
]
print(f"\nSexual harassment-related cases: {len(sexual)}")
for c in sexual[:5]:
    print(f"  - {c['case_name'][:60]} | {c.get('court','?')[:30]}")

# Sample 3 cases to see their structure
print("\nSample case keys:", list(data[0].keys()))
print("Sample case_name:", data[0].get("case_name"))
print("Sample keywords:", data[0].get("keywords", [])[:5])
print("Sample legal_issues:", data[0].get("legal_issues", [])[:3])
print("Sample statutes:", data[0].get("statutes_referenced", [])[:3])
