# =====================================================================
# Product Search Amazon — Monitoring: Alert Manager
# =====================================================================

from typing import Dict, Any


def evaluate_latency_alerts(latency_ms: float, thresholds: Dict[str, float] = None) -> Dict[str, Any]:
    thresholds = thresholds or {"warning": 1500, "critical": 3000}
    if latency_ms >= thresholds["critical"]:
        return {"level": "CRITICAL", "message": f"Search latency ({latency_ms:.1f}ms) exceeds critical threshold ({thresholds['critical']}ms)"}
    elif latency_ms >= thresholds["warning"]:
        return {"level": "WARNING", "message": f"Search latency ({latency_ms:.1f}ms) exceeds warning threshold ({thresholds['warning']}ms)"}
    return {"level": "OK", "message": "Search latency is within healthy operating bounds."}
