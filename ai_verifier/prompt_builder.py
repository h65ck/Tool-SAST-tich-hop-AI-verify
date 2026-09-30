import json
import os

def build_prompt(finding: dict) -> str:
    """
    Build prompt for Gemini SAST Verification.
    """
    vuln_type = finding.get("vuln_type", "Unknown")
    file_path = finding.get("file", "Unknown")
    sink_code = finding.get("sink_code", "")
    sink_line = finding.get("sink_line", "Unknown")
    source_code = finding.get("source_code", "")
    source_file = finding.get("source_file", "")
    source_line = finding.get("source_line", "Unknown")
    
    taint_trace = finding.get("taint_trace", [])
    
    trace_details = "===== REPORTED TAINT TRACE =====\n"
    for idx, step in enumerate(taint_trace):
        trace_details += f"Step {idx+1}: Role: {step.get('role')}, File: {step.get('file')}, Line: {step.get('line')}, Code: {step.get('code')}\n"

    # Context gathering (Snippets instead of full files to avoid OOM)
    context_text = "===== SOURCE CODE CONTEXT =====\n"
    file_lines = {} # file -> list of lines
    
    def add_line(f, l):
        if f and f != "Unknown" and l and l != "Unknown":
            try:
                line_int = int(l)
                if f not in file_lines:
                    file_lines[f] = set()
                file_lines[f].add(line_int)
            except:
                pass

    add_line(source_file, source_line)
    add_line(file_path, sink_line)
    for step in taint_trace:
        add_line(step.get("file"), step.get("line"))
        
    for f, lines in file_lines.items():
        context_text += f"\n--- File: {f} ---\n"
        try:
            with open(f, "r", encoding="utf-8") as file_obj:
                all_lines = file_obj.readlines()
                # Nếu file nhỏ dưới 200 dòng, đính kèm nguyên file
                if len(all_lines) < 200:
                    context_text += "".join(all_lines)
                else:
                    # Nếu file lớn, chỉ lấy snippet quanh vùng có code liên quan
                    for l in sorted(list(lines)):
                        start = max(0, l - 15 - 1)
                        end = min(len(all_lines), l + 15)
                        context_text += f"// Snippet around line {l}:\n"
                        context_text += "".join(all_lines[start:end]) + "\n"
        except Exception as e:
            context_text += f"(Error reading file: {e})\n"

    prompt = f"""
You are a Senior AppSec Expert in SAST and Taint Analysis.
Task: Determine if a taint path is practically exploitable, not just if data reaches a sink.

Analyze the following input code and trace:
1. Source: Identify user-controlled input origin.
2. Propagation: Trace data flow. Note if taint is preserved.
3. Validation: Identify checks (e.g., is_numeric, regex, whitelists). Reason semantically. Example: Splitting an IP and checking each octet with is_numeric neutralizes shell injection, even if reassembled data reaches the sink.
4. Sanitization: Identify context-aware sanitizers (e.g., escapeshellarg). Do not count generic string functions (trim, strtolower) unless they neutralize the specific attack.
5. Sink: Check if exploitable data reaches the sink.
6. Exploitability: Classify as:
   - Confirmed True Positive: Payload reaches sink unmitigated.
   - False Positive: Logic/validation prevents malicious payload construction.
   - Needs Manual Review: Insufficient context.

Specific Vulnerability Guidelines:
* SQL Injection (SQLi): Dynamic SQL is vulnerable unless parameterized queries are used. If SQL is built by concatenation into a numeric context without quotes, escaping is useless.
* Unrestricted File Upload: Safe if extension is strictly whitelisted and filename is safely generated (e.g., uniqid).
* Path Traversal: Using basename() or strict whitelist makes it safe.
* Command Injection: User input must be strictly escaped using escapeshellarg() or escapeshellcmd().

---
# INPUT DATA
Vulnerability Type: {vuln_type}
{trace_details}

{context_text}

---
# Expected Output

You MUST output ONLY a valid JSON object matching the exact schema below. Do not omit ANY fields. Use "N/A" or [] if a field is not applicable. Do not wrap it in markdown blocks (no ```json). Do not output anything else before or after the JSON.

SCHEMA:
{{
  "status": "Confirmed True Positive|False Positive|Needs Manual Review",
  "confidence": <integer from 0 to 100>,
  "severity": "Info|Low|Medium|High|Critical",
  "reason": "<Brief conclusion>",
  "source": "<Origin variable/input>",
  "sink": "<Target function/sink>",
  "validation": ["<identified checks>"],
  "sanitization": ["<identified sanitizers>"],
  "taint_trace": ["<trace steps>"],
  "exploitability": "<Detailed explanation of exploitability>",
  "recommendation": "<Remediation advice>"
}}
"""
    return prompt
