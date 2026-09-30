from textual.widgets import DataTable
from rich.text import Text

class FindingsTable(DataTable):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = " Findings "
        self.cursor_type = "row"
        
        # Define columns
        self.add_column("ID", key="id")
        self.add_column("Severity", key="severity")
        self.add_column("Tool Verdict", key="tool_verdict")
        self.add_column("Type", key="type")
        self.add_column("File", key="file")
        self.add_column("Line", key="line")
        self.add_column("Cross File", key="cross_file")
        self.add_column("Interprocedural", key="interprocedural")
        self.add_column("Manual Triage", key="manual_triage")
        self.add_column("AI Verdict", key="ai_verdict")
        self.add_column("AI Reason", key="ai_reason")

        # Keep track of sort state
        self.sort_column = "id"
        self.sort_desc = False
        self.raw_findings = []
        self.reviews = {}
        
        # Current active filters
        self.severity_filter = None
        self.type_filter = None
        self.search_query = None

    def update_data(self, findings: list, reviews: dict, severity_filter=None, type_filter=None, search_query=None):
        self.raw_findings = findings
        self.reviews = reviews
        self.severity_filter = severity_filter
        self.type_filter = type_filter
        self.search_query = search_query
        self.refresh_table()

    def refresh_table(self):
        # 1. Filter findings
        filtered = []
        for original_idx, f in enumerate(self.raw_findings):
            # Severity filter
            if self.severity_filter and f.get("severity", "").upper() != self.severity_filter.upper():
                continue
            # Type filter
            if self.type_filter and f.get("vuln_type", "").lower() != self.type_filter.lower():
                continue
            # Search query (matches file, vuln_type, or sink_code)
            if self.search_query:
                q = self.search_query.lower()
                matches = (
                    q in f.get("file", "").lower() or
                    q in f.get("vuln_type", "").lower() or
                    q in f.get("sink_code", "").lower()
                )
                if not matches:
                    continue
            filtered.append((original_idx, f))

        # 2. Sort findings
        def sort_key(item):
            original_idx, f = item
            col = self.sort_column
            if col == "id":
                return f.get("id", 0)
            elif col == "severity":
                # High > Info
                sev = f.get("severity", "").upper()
                return 0 if sev == "HIGH" else 1
            elif col == "type":
                return f.get("vuln_type", "")
            elif col == "file":
                return f.get("file", "")
            elif col == "line":
                return f.get("sink_line", 0)
            elif col == "cross_file":
                return 1 if f.get("cross_file") else 0
            elif col == "interprocedural":
                return 1 if f.get("interprocedural") else 0
            elif col == "tool_verdict":
                return f.get("status", "")
            elif col == "manual_triage":
                return self.reviews.get(f.get("id"), "Untriaged")
            elif col == "ai_verdict":
                return f.get("ai_review", {}).get("status", "")
            return 0

        filtered.sort(key=sort_key, reverse=self.sort_desc)

        # 3. Populate rows
        self.clear()
        
        # Color mapping for triage
        triage_styles = {
            "TP": "[bold #a6e3a1]TP[/bold #a6e3a1]",
            "FP": "[bold #f38ba8]FP[/bold #f38ba8]",
            "REV": "[bold #f9e2af]REV[/bold #f9e2af]",
            "Untriaged": "[dim #9399b2]Untriaged[/dim #9399b2]"
        }

        for original_idx, f in filtered:
            f_id = f.get("id")
            severity = f.get("severity", "INFO")
            severity_style = "bold #f38ba8" if severity.upper() == "HIGH" else "bold #89b4fa"
            
            tool_status = f.get("status", "UNKNOWN")
            if tool_status.upper() == "TAINTED":
                tool_verdict_style = "bold #f38ba8"
                tool_verdict_text = "🔴 TAINTED"
            elif tool_status.upper() == "SAFE":
                tool_verdict_style = "bold #a6e3a1"
                tool_verdict_text = "🟢 SAFE"
            else:
                tool_verdict_style = "bold #89b4fa"
                tool_verdict_text = tool_status
            
            triage_val = self.reviews.get(f_id, "Untriaged")
            manual_triage_display = triage_styles.get(triage_val, triage_val)

            ai_reason = "N/A"
            ai_verdict_display = "[dim #9399b2]Waiting AI Verification[/dim #9399b2]"
            ai_review = f.get("ai_review")
            
            if ai_review:
                result = ai_review.get("status")
                ai_reason = str(ai_review.get("reason", "N/A"))
                if result == "verified" or result == "Confirmed True Positive":
                    ai_verdict_display = "[bold #a6e3a1]✓ AI Verified (TP)[/bold #a6e3a1]"
                elif result == "likely_false_positive" or result == "False Positive":
                    ai_verdict_display = "[bold #f38ba8]Likely False Positive (FP)[/bold #f38ba8]"
                elif result == "Needs Manual Review":
                    ai_verdict_display = "[bold #f9e2af]Needs Manual Review[/bold #f9e2af]"
                else:
                    ai_verdict_display = f"[bold #f9e2af]{result}[/bold #f9e2af]"

            self.add_row(
                str(f_id),
                Text.from_markup(f"[{severity_style}]{severity}[/{severity_style}]"),
                Text.from_markup(f"[{tool_verdict_style}]{tool_verdict_text}[/{tool_verdict_style}]"),
                f.get("vuln_type", "N/A"),
                f.get("file", "N/A"),
                str(f.get("sink_line", "N/A")),
                "Yes" if f.get("cross_file") else "No",
                "Yes" if f.get("interprocedural") else "No",
                Text.from_markup(manual_triage_display),
                Text.from_markup(ai_verdict_display),
                ai_reason,
                key=str(original_idx)
            )

        # Update border title with findings count
        total = len(self.raw_findings)
        curr = len(filtered)
        if self.severity_filter or self.type_filter or self.search_query:
            self.border_title = f" Findings ({curr}/{total} filtered) "
        else:
            self.border_title = f" Findings ({total}) "

    @property
    def selected_finding_index(self) -> int | None:
        try:
            row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
            return int(row_key.value)
        except Exception:
            return None
