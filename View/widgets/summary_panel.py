from textual.widgets import Static
from rich.table import Table
from rich.text import Text
from rich.console import Group

class SummaryPanel(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = " Summary "
        self.finding = None
        self.triage_display = "Untriaged"
        self.current_trace = []
        self.current_trace_index = 0

    def update_finding(self, finding, triage_display):
        self.finding = finding
        self.triage_display = triage_display
        self.current_trace = []
        self.current_trace_index = 0
        self.refresh()

    def update_trace_step(self, trace, index):
        self.current_trace = trace
        self.current_trace_index = index
        self.refresh()

    def render(self):
        if not self.finding:
            return Text("Select a finding to view details.", style="dim italic")

        content = []

        # Metadata Table
        table = Table(show_header=False, expand=True)
        table.add_column("Key", style="bold cyan", width=18)
        table.add_column("Value", style="white")

        table.add_row("ID", str(self.finding.get("id", "N/A")))
        
        severity = self.finding.get("severity", "INFO")
        severity_style = "bold red" if severity.upper() == "HIGH" else "bold blue"
        table.add_row("Severity", f"[{severity_style}]{severity}[/{severity_style}]")
        
        status = self.finding.get("status", "N/A")
        table.add_row("Status", status)
        
        vuln_type = self.finding.get("vuln_type", "N/A")
        table.add_row("Vuln Type", vuln_type)
        
        table.add_row("File", self.finding.get("file", "N/A"))
        table.add_row("Sink Line", str(self.finding.get("sink_line", "N/A")))
        table.add_row("Sink Code", f"`{self.finding.get('sink_code', 'N/A')}`")
        table.add_row("Cross File", "Yes" if self.finding.get("cross_file") else "No")
        table.add_row("Interprocedural", "Yes" if self.finding.get("interprocedural") else "No")
        
        triage_style = "triage-none"
        if self.triage_display == "Confirmed True Positive":
            triage_style = "green"
        elif self.triage_display == "False Positive":
            triage_style = "red"
        elif self.triage_display == "Need Review":
            triage_style = "yellow"
            
        table.add_row("Triage Status", f"[{triage_style}]{self.triage_display}[/{triage_style}]")

        content.append(table)

        # Trace Mini Map
        if self.current_trace and len(self.current_trace) > 0:
            content.append(Text("\n🗺️ Trace Mini Map", style="bold underline #a6e3a1"))
            total = len(self.current_trace)
            idx = self.current_trace_index
            step = self.current_trace[idx]
            
            role = step.get("role", "PROPAGATION").upper()
            file_name = step.get("file", "unknown")
            line = step.get("line", "0")
            
            info_table = Table(show_header=False, expand=True)
            info_table.add_column("Key", style="bold magenta", width=18)
            info_table.add_column("Value", style="white")
            info_table.add_row("Trace Step", f"{idx + 1} / {total}")
            info_table.add_row("Role", role)
            info_table.add_row("Location", f"{file_name}:{line}")
            content.append(info_table)
            
            map_text = Text("\n")
            for i, tr_step in enumerate(self.current_trace):
                r = tr_step.get("role", "PROPAGATION").upper()
                prefix = "> " if i == idx else "  "
                
                # Role colors for mini map
                color = {
                    "SOURCE": "#a6e3a1",
                    "PROPAGATION": "#f9e2af",
                    "CALL": "#89b4fa",
                    "RETURN": "#89dceb",
                    "SAFE_OVERWRITE": "#74c7ec",
                    "SINK": "#f38ba8"
                }.get(r, "#f9e2af")
                
                style = f"bold {color} reverse" if i == idx else f"dim {color}"
                map_text.append(f"{prefix}[{i+1}] {r}\n", style=style)
            content.append(map_text)

        # Endpoint panel (if data exists)
        endpoint = self.finding.get("endpoint")
        method = self.finding.get("method")
        parameter = self.finding.get("parameter")
        if endpoint or method:
            ep_table = Table(show_header=False, expand=True)
            ep_table.add_column("Key", style="bold yellow", width=18)
            ep_table.add_column("Value", style="white")
            ep_table.add_row("Method", str(method or "ANY"))
            ep_table.add_row("Endpoint", str(endpoint or "/"))
            if parameter:
                ep_table.add_row("Parameter", str(parameter))
            
            content.append(Text("\n🌐 Endpoint Details", style="bold underline yellow"))
            content.append(ep_table)

        # AI Verification panel
        ai_review = self.finding.get("ai_review")
        if ai_review:
            content.append(Text("\n🤖 AI Verification", style="bold underline purple"))
            
            ai_table = Table(show_header=False, expand=True)
            ai_table.add_column("Key", style="bold purple", width=18)
            ai_table.add_column("Value", style="white")
            
            result = ai_review.get("status", "")
            if result == "verified":
                status_text = "[bold #a6e3a1]✓ AI Verified[/bold #a6e3a1]"
            elif result == "likely_false_positive":
                status_text = "[bold #f38ba8]Likely False Positive[/bold #f38ba8]"
            else:
                status_text = "[bold #f9e2af]Need More Context[/bold #f9e2af]"
                
            ai_table.add_row("Status", status_text)
            ai_table.add_row("Confidence", f"{ai_review.get('confidence', 0)}%")
            ai_table.add_row("Severity", str(ai_review.get('severity', 'N/A')))
            ai_table.add_row("Reason", str(ai_review.get('reason', 'N/A')))
            ai_table.add_row("Recommendation", str(ai_review.get('recommendation', 'N/A')))
            
            content.append(ai_table)
        else:
            # Fallback for old AI Verdict if needed
            ai_verdict = self.finding.get("ai_verdict") or self.finding.get("ai_analysis") or self.finding.get("ai_explanation")
            if ai_verdict:
                content.append(Text("\n🤖 AI Verdict", style="bold underline purple"))
                content.append(Text(str(ai_verdict), style="italic color(246)"))

        return Group(*content)
