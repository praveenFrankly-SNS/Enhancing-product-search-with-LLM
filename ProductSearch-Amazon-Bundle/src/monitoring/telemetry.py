# =====================================================================
# Product Search Amazon — Monitoring: Telemetry Reporter
# =====================================================================

from typing import Dict, Any


def print_telemetry_summary(telemetry_data: Dict[str, Any]):
    print("=" * 60)
    print("📊 AMAZON PRODUCT SEARCH PIPELINE TELEMETRY SUMMARY")
    print("=" * 60)
    for key, val in telemetry_data.items():
        print(f"  • {key}: {val}")
    print("=" * 60)
