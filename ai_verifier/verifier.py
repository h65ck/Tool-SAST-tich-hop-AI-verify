import json
import os
import logging
from ai_verifier.prompt_builder import build_prompt
from ai_verifier.config import review
from ai_verifier.json_writer import write_verified_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def run_verification(input_report_path: str = "reports/report.json", output_report_path: str = "reports/report_verified.json"):
    """
    Reads the report, runs AI verification on each finding, and saves a new verified report.
    """
    if not os.path.exists(input_report_path):
        logger.error(f"Input report not found: {input_report_path}")
        return False
        
    try:
        with open(input_report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure it's the expected dict structure
            if isinstance(data, list):
                # Fallback if somehow it's a list
                findings = data
                full_data = data
            else:
                findings = data.get("findings", [])
                full_data = data
    except Exception as e:
        logger.error(f"Failed to load {input_report_path}: {e}")
        return False
        
    if not findings:
        logger.info("No findings in the report to verify.")
        return True

    findings_to_verify = [f for f in findings if f.get("severity", "").upper() != "INFO"]
    logger.info(f"Starting AI Verification for {len(findings_to_verify)} finding(s) (skipped INFO severities)...")
    
    for i, finding in enumerate(findings):
        severity = finding.get("severity", "").upper()
        if severity == "INFO":
            logger.info(f"Skipping finding {i+1}/{len(findings)} (ID: {finding.get('id', 'Unknown')}) due to INFO severity.")
            continue

        logger.info(f"Verifying finding {i+1}/{len(findings)} (ID: {finding.get('id', 'Unknown')})")
        prompt = build_prompt(finding)
        ai_review = review(prompt)
        finding["ai_review"] = ai_review
        
    write_verified_report(full_data, output_report_path)
    logger.info("AI Verification completed successfully.")
    return True
