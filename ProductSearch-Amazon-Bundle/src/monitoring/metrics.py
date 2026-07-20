# =====================================================================
# Product Search Amazon — Monitoring: Metrics
# =====================================================================

from typing import Dict, Any


def collect_dataset_telemetry(raw_count: int, clean_count: int, gold_count: int) -> Dict[str, Any]:
    drop_rate = 0.0
    if raw_count > 0:
        drop_rate = (raw_count - clean_count) / float(raw_count)
    return {
        "raw_records": raw_count,
        "clean_records": clean_count,
        "gold_records": gold_count,
        "drop_rate": round(drop_rate, 4)
    }
