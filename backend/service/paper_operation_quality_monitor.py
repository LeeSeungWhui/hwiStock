"""
hwiStock paper-operation quality monitor service wrapper.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from lib.paper_operation_quality_monitor import (  # noqa: E402
    SCHEMA_VERSION,
    evaluatePaperOperationQuality,
    main,
    parseKst,
    writePaperOperationQualityEvidence,
)

__all__ = (
    "SCHEMA_VERSION",
    "evaluatePaperOperationQuality",
    "main",
    "parseKst",
    "writePaperOperationQualityEvidence",
)


if __name__ == "__main__":
    raise SystemExit(main())
