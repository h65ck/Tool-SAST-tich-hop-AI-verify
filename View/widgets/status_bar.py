from textual.widgets import Static
from textual.reactive import reactive

class StatusBar(Static):
    project_name = reactive("N/A")
    file_count = reactive(0)
    total_findings = reactive(0)
    high_count = reactive(0)
    info_count = reactive(0)
    current_idx = reactive(0)  # 1-indexed, 0 means none
    trace_progress = reactive("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self) -> str:
        current_str = f"{self.current_idx}/{self.total_findings}" if self.current_idx > 0 else "-"
        trace_str = f"  |  👣 TRACE: [bold yellow]{self.trace_progress}[/bold yellow]" if self.trace_progress else ""
        return (
            f" 📂 Project: [bold cyan]{self.project_name}[/bold cyan]  |  "
            f"📄 Files: [bold white]{self.file_count}[/bold white]  |  "
            f"🔍 Findings: [bold white]{self.total_findings}[/bold white]  |  "
            f"🔴 HIGH: [bold red]{self.high_count}[/bold red]  |  "
            f"🔵 INFO: [bold blue]{self.info_count}[/bold blue]  |  "
            f"🎯 Current: [bold magenta]{current_str}[/bold magenta]"
            f"{trace_str}"
        )
