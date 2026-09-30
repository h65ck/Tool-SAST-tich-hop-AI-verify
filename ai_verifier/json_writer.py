import json
import os
import logging

logger = logging.getLogger(__name__)

def write_verified_report(findings: list, output_path: str):
    """
    Writes the verified findings to a new JSON report file.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=4, ensure_ascii=False)
        logger.info(f"Verified report saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write verified report to {output_path}: {e}")
