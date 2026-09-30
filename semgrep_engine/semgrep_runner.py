import subprocess
import json
import sys

SINK_TYPE_MAP = {
    "detect-command-sink": "command_injection",
    "detect-sql-sink": "sql_injection",
    "detect-xss-sink": "xss",
    "detect-file-inclusion-sink": "file_inclusion",
    "detect-path-traversal-sink": "path_traversal",
    "detect-file-upload-sink": "unrestricted_file_upload",
}

def run_semgrep(target_file):
    cmd = ["semgrep", "--config", "rules/rules.yaml", target_file, "--json"]  # [RESTRUCTURE_CHANGE]
    print(">>> Running Semgrep as Scout...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print("Error: Semgrep is not installed or not in PATH.")
        sys.exit(1)

    semgrep_data = {
        "sources": [],
        "sinks": [],
        "sink_types": {}
    }

    try:
        output_json = json.loads(result.stdout)
        results = output_json.get("results", [])

        for res in results:
            rule_id = res.get("check_id", "").split(".")[-1]
            line_no = res.get("start", {}).get("line")

            if rule_id == "detect-source":
                if line_no not in semgrep_data["sources"]:
                    semgrep_data["sources"].append(line_no)

            elif rule_id in SINK_TYPE_MAP:
                if line_no not in semgrep_data["sinks"]:
                    semgrep_data["sinks"].append(line_no)
                semgrep_data["sink_types"][line_no] = SINK_TYPE_MAP[rule_id]

    except json.JSONDecodeError:
        print("Error parsing Semgrep JSON output.")
        print(f"Stdout was: {result.stdout}")
        print(f"Stderr was: {result.stderr}")
        sys.exit(1)

    return semgrep_data