"""
hwiStock KIS market-data collector service wrapper.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from lib.kis_market_data_runtime import (
    ALLOWED_SIGNAL_INPUTS,
    buildKisSignalEndpointAudit,
    buildCompiledWatchFromKisSnapshot,
    collectKisMarketDataOnce,
    loadKisSignalCollectorConfig,
    main,
    validateKisSignalInputScope,
    writeCompiledWatchEvidence,
    writeKisMarketDataEvidence,
)

__all__ = (
    "ALLOWED_SIGNAL_INPUTS",
    "buildKisSignalEndpointAudit",
    "buildCompiledWatchFromKisSnapshot",
    "collectKisMarketDataOnce",
    "loadKisSignalCollectorConfig",
    "main",
    "validateKisSignalInputScope",
    "writeCompiledWatchEvidence",
    "writeKisMarketDataEvidence",
)


if __name__ == "__main__":
    raise SystemExit(main())
