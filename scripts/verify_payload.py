"""Verify payload accuracy: SQL key_findings vs manual max/min from monthly_trend."""
from src.analytics.metrics import generate_metrics_payload, JSONEncoder
import json

payload = generate_metrics_payload()

kf = payload["key_findings"]
print("=== KEY FINDINGS (Python-computed) ===")
for k, v in kf.items():
    print(f"  {k}: {json.dumps(v, cls=JSONEncoder)}")

print()
print("=== OVERALL ===")
print(json.dumps(payload["overall"], cls=JSONEncoder, indent=2))

print()
mt = payload["monthly_trend"]
print(f"Monthly trend entries: {len(mt)}")

if mt:
    max_m = max(mt, key=lambda x: float(x["no_show_rate_pct"]))
    min_m = min(mt, key=lambda x: float(x["no_show_rate_pct"]))
    print(f"Max month (verified): {max_m['year']}-{max_m['month']:02d} ({max_m['month_name']}) = {float(max_m['no_show_rate_pct']):.2f}%")
    print(f"Min month (verified): {min_m['year']}-{min_m['month']:02d} ({min_m['month_name']}) = {float(min_m['no_show_rate_pct']):.2f}%")
    print()
    kf_max = float(kf["highest_no_show_month"]["no_show_rate_pct"])
    kf_min = float(kf["lowest_no_show_month"]["no_show_rate_pct"])
    print(f"key_findings.highest matches: {kf_max == float(max_m['no_show_rate_pct'])}")
    print(f"key_findings.lowest matches:  {kf_min == float(min_m['no_show_rate_pct'])}")

# Save updated payload
from src.analytics.metrics import save_metrics_payload
save_metrics_payload()
print()
print("Payload saved to data/processed/metrics_payload.json")
