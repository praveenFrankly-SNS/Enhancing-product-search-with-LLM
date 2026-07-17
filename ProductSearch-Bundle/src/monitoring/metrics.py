# =====================================================================
# Product Search — Monitoring: Metric Constants & Helpers
# =====================================================================

from typing import Dict, Any

def format_metric(
    pipeline_stage: str,
    metric_name: str,
    metric_value: float,
    unit: str,
    status: str = "SUCCESS"
) -> Dict[str, Any]:
    """
    Validates and formats a single operational metric fact.
    """
    return {
        "pipeline_stage": str(pipeline_stage),
        "metric_name": str(metric_name),
        "metric_value": float(metric_value),
        "unit": str(unit),
        "status": str(status)
    }
