from textual.widgets import ListView, ListItem
from rich.text import Text

class TraceItem(ListItem):
    def __init__(self, step, index, is_last=False, mode="trace", **kwargs):
        super().__init__(**kwargs)
        self.step = step
        self.index = index
        self.is_last = is_last
        self.mode = mode
        self.is_active = False

    def set_active(self, active: bool):
        self.is_active = active
        self.refresh()

    def render(self) -> Text:
        if self.mode == "trace":
            role = self.step.get("role", "propagation").upper()
            
            # Map role to styles matching our lazy_sast.tcss rules
            role_style = {
                "SOURCE": "bold #a6e3a1",          # Green
                "PROPAGATION": "bold #f9e2af",      # Yellow
                "CALL": "bold #89b4fa",             # Blue
                "RETURN": "bold #89dceb",           # Cyan
                "SAFE_OVERWRITE": "bold #74c7ec",   # Bright Cyan
                "SINK": "bold #f38ba8"              # Red
            }.get(role, "bold #f9e2af")
            
            file_name = self.step.get("file", "unknown")
            line_num = self.step.get("line", 0)
            code = self.step.get("code", "")
            
            
            prefix = "► " if self.is_active else "  "
            if self.is_active:
                role_style += " reverse"
                
            text = Text()
            text.append(f"{prefix}[{role}]\n", style=role_style)
            text.append(f"    {file_name}:{line_num}\n", style="#a6adc8")
            text.append(f"  > {code}", style="#cdd6f4 italic")
            if not self.is_last:
                text.append("\n      ↓", style="bold #f5c2e7")
            return text
        else:
            # Full path mode
            text = Text()
            prefix = "► " if self.is_active else "  "
            style = "bold #f9e2af reverse" if self.is_active else "bold #f9e2af"
            text.append(f"{prefix}[STEP {self.index + 1}]\n", style=style)
            text.append(f"    {self.step}", style="#cdd6f4")
            if not self.is_last:
                text.append("\n      ↓", style="bold #f5c2e7")
            return text

class TraceViewer(ListView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = " Trace Viewer "
        self.finding = None
        self.mode = "trace"

    def update_finding(self, finding, mode="trace"):
        self.finding = finding
        self.mode = mode
        self.clear()
        
        if not finding:
            self.border_title = " Trace Viewer "
            return

        if self.mode == "trace":
            self.border_title = " Trace Viewer (Taint Trace Mode) "
            trace = finding.get("taint_trace", [])
            for i, step in enumerate(trace):
                is_last = (i == len(trace) - 1)
                self.append(TraceItem(step, i, is_last=is_last, mode="trace"))
        else:
            self.border_title = " Trace Viewer (Full Path Mode) "
            path = finding.get("full_path", [])
            for i, step in enumerate(path):
                is_last = (i == len(path) - 1)
                self.append(TraceItem(step, i, is_last=is_last, mode="path"))

    def update_active_step(self, active_index: int):
        self.index = active_index
        for i, child in enumerate(self.children):
            if isinstance(child, TraceItem):
                child.set_active(i == active_index)
