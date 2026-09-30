import json

class Reporter:
    def __init__(self, findings):
        self.findings = findings

    def print_findings(self):
        for finding in self.findings:
            print(f"\n--- [ĐƯỜNG ĐI SỐ {finding['id']}] ---")
            # [CROSS_FILE_CHANGE]
            if finding.get("file"):
                print(f" File: {finding.get('file')}")
            if finding.get("vuln_type"):
                print(f" Loại lỗ hổng: {finding.get('vuln_type')}")
            if finding.get("interprocedural"):
                print(" Interprocedural: true")
            if finding.get("cross_file"):
                print(f" Cross-file: {finding.get('file')} -> {finding.get('function_file')}")
            
            # [REPORT_TRACE_CHANGE]
            path_to_print = finding.get("full_path", finding.get("path", []))
            print(" Lộ trình: " + " ➔ ".join(path_to_print))
            
            # [REPORT_TRACE_CHANGE]
            if finding.get("taint_trace"):
                print(" Taint trace:")
                for item in finding.get("taint_trace", []):
                    print(f"  - [{item.get('role')}] {item.get('file')}:{item.get('line')} {item.get('code')}")

            if finding.get('tainted_variables'):
                print(f" Biến mang mầm bệnh rơi vào Sink: {', '.join(finding['tainted_variables'])}")
            if finding.get("real_sink_code"):
                print(f" Sink thật: {finding.get('real_sink_code')}")
            color = "🔴 NGUY HIỂM" if finding.get('status') == "TAINTED" else "🟢 AN TOÀN"
            print(f" ==> KẾT LUẬN: {color} ({finding.get('status')})")

    def export_json(self, output_path=None):
        # [REPORT_TRACE_CHANGE]
        payload = {
            "summary": {
                "total_findings": len(self.findings),
                "tainted_findings": sum(1 for f in self.findings if f.get("status") == "TAINTED"),
                "safe_findings": sum(1 for f in self.findings if f.get("status") == "SAFE"),
                "unknown_findings": sum(1 for f in self.findings if f.get("status") == "UNKNOWN"),
                "high_findings": sum(1 for f in self.findings if f.get("severity") == "HIGH"),
                "info_findings": sum(1 for f in self.findings if f.get("severity") == "INFO")
            },
            "findings": self.findings
        }
        json_str = json.dumps(payload, ensure_ascii=False, indent=2)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str
