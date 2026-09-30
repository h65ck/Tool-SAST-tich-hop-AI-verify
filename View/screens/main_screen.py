import os
import threading
from pathlib import Path
from textual.screen import Screen, ModalScreen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Label, Button, Input, ListView, ListItem, DataTable, DirectoryTree
from textual.binding import Binding
from rich.text import Text
from rich.panel import Panel

from View.widgets.findings_table import FindingsTable
from View.widgets.file_tree import FileTree
from View.widgets.source_viewer import SourceViewer
from View.widgets.trace_viewer import TraceViewer
from View.widgets.summary_panel import SummaryPanel
from View.widgets.status_bar import StatusBar

# ----------------- MODAL SCREENS -----------------

class HelpModal(ModalScreen):
    """A pop-up modal showing available keyboard shortcuts and instructions."""
    def compose(self):
        help_text = (
            "[bold #89b4fa]Keyboard Shortcuts[/bold #89b4fa]\n\n"
            "  [bold #f9e2af]F1[/bold #f9e2af]       Help Screen\n"
            "  [bold #f9e2af]F2[/bold #f9e2af]       Filter Severity (Toggle: ALL -> HIGH -> INFO)\n"
            "  [bold #f9e2af]F3[/bold #f9e2af]       Filter Vulnerability Type\n"
            "  [bold #f9e2af]/[/bold #f9e2af]        Search text in findings\n"
            "  [bold #f9e2af]F4[/bold #f9e2af]       Toggle Trace (Switch focus between Findings & Trace Viewer)\n"
            "  [bold #f9e2af]F5[/bold #f9e2af]       Reload Report\n"
            "  [bold #f9e2af]F6[/bold #f9e2af]       Full Path Mode\n"
            "  [bold #f9e2af]F7[/bold #f9e2af]       Taint Trace Mode (Default)\n"
            "  [bold #f9e2af]F8[/bold #f9e2af]       AI Verdict detail popup\n"
            "  [bold #f9e2af]TAB[/bold #f9e2af]      Next Panel\n"
            "  [bold #f9e2af]SHIFT+TAB[/bold #f9e2af] Previous Panel\n"
            "  [bold #f9e2af]ENTER[/bold #f9e2af]    Open selected file in editor / Confirm\n"
            "  [bold #f9e2af]ESC[/bold #f9e2af]      Go Back / Close Dialog / Clear filters\n"
            "  [bold #f9e2af]Q[/bold #f9e2af]        Quit\n\n"
            "[bold #a6e3a1]Triage System (Press while inside Findings Table)[/bold #a6e3a1]\n\n"
            "  [bold green]T[/bold green]        Confirmed True Positive (TP)\n"
            "  [bold red]M[/bold red]        False Positive (FP)\n"
            "  [bold yellow]R[/bold yellow]        Need Review (REV)\n\n"
            "Press any key or click Close to return."
        )
        yield Vertical(
            Static(Text.from_markup(help_text), id="help-text"),
            Button("Close", variant="primary", id="close-btn"),
            id="modal-content"
        )

    def on_mount(self):
        self.query_one("#close-btn").focus()

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss()

    def on_key(self, event):
        # Dismiss on any key press for quick close
        if event.key != "tab":
            self.dismiss()


class SearchModal(ModalScreen):
    """Modal screen for text search input."""
    def compose(self):
        yield Vertical(
            Label("[bold #89b4fa]Search Findings[/bold #89b4fa] (File, Type, or Code)"),
            Input(placeholder="Type query and press Enter...", id="search-input"),
            Horizontal(
                Button("Apply", variant="primary", id="search-apply"),
                Button("Cancel", id="search-cancel"),
                id="modal-buttons"
            ),
            id="search-content"
        )

    def on_mount(self):
        self.query_one("#search-input").focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "search-apply":
            val = self.query_one("#search-input").value
            self.dismiss(val)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted):
        self.dismiss(event.value)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)


class TypeFilterModal(ModalScreen):
    """Modal screen displaying available Vulnerability Types to filter."""
    def __init__(self, vuln_types: list, **kwargs):
        super().__init__(**kwargs)
        self.vuln_types = vuln_types

    def compose(self):
        items = [ListItem(Label("[bold magenta][ALL][/bold magenta]"), id="all_types")]
        for t in self.vuln_types:
            items.append(ListItem(Label(t), id=f"type_{t}"))

        yield Vertical(
            Label("[bold #89b4fa]Select Vulnerability Type Filter[/bold #89b4fa]"),
            ListView(*items, id="type-list"),
            id="type-content"
        )

    def on_mount(self):
        self.query_one("#type-list").focus()

    def on_list_view_selected(self, event: ListView.Selected):
        item_id = event.item.id
        if item_id == "all_types":
            self.dismiss("ALL")
        else:
            # strip "type_" prefix
            self.dismiss(item_id[5:])

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)


class AIVerdictModal(ModalScreen):
    """Modal popup to display AI Verdict in full detail."""
    def __init__(self, ai_verdict: str, **kwargs):
        super().__init__(**kwargs)
        self.ai_verdict = ai_verdict

    def compose(self):
        yield Vertical(
            Label("[bold #89dceb]🤖 Full AI Verdict Analysis[/bold #89dceb]\n"),
            Static(self.ai_verdict, id="ai-verdict-body"),
            Button("Close", variant="primary", id="ai-close"),
            id="ai-content"
        )

    def on_mount(self):
        self.query_one("#ai-close").focus()

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss()

    def on_key(self, event):
        if event.key != "tab":
            self.dismiss()


# ----------------- MAIN SCREEN -----------------

class MainScreen(Screen):
    # Register core keyboard shortcuts
    BINDINGS = [
        Binding("f1", "help", "Help", show=True),
        Binding("f2", "toggle_severity", "Filter Severity", show=True),
        Binding("f3", "filter_type", "Filter Type", show=True),
        Binding("slash", "search_findings", "Search", show=False),
        Binding("f4", "toggle_trace", "Toggle Trace Focus", show=True),
        Binding("f5", "reload_report", "Reload", show=True),
        Binding("f6", "full_path_mode", "Full Path Mode", show=True),
        Binding("f7", "taint_trace_mode", "Taint Trace Mode", show=True),
        Binding("r", "ai_verdict", "View Full Reason", show=True),
        Binding("R", "ai_verdict", "View Full Reason", show=False),
        Binding("q", "quit_app", "Quit", show=True),
        Binding("escape", "clear_filters", "Clear Filters", show=False),
        
        # Triage system bindings
        Binding("t", "triage_tp", "Triage TP", show=False),
        Binding("m", "triage_fp", "Triage FP", show=False),

        Binding("v", "verify_finding", "Verify with AI", show=True),
        Binding("V", "verify_finding", "Verify with AI", show=False),
        
        # Trace Navigator bindings
        Binding("n", "next_trace_step", "Next Trace Step", show=False),
        Binding("right", "next_trace_step", "Next Trace Step", show=False),
        Binding("p", "prev_trace_step", "Prev Trace Step", show=False),
        Binding("left", "prev_trace_step", "Prev Trace Step", show=False),
        Binding("home", "jump_trace_source", "Jump to Source", show=False),
        Binding("end", "jump_trace_sink", "Jump to Sink", show=False),
        Binding("s", "jump_trace_sink", "Jump to Sink", show=False),
    ]

    def __init__(self, loader, source_dir: str):
        super().__init__()
        self.loader = loader
        self.source_dir = source_dir
        self.file_count = 0
        self.severity_filter = None  # None, "HIGH", "INFO"
        self.type_filter = None      # None, or vuln_type name
        self.search_query = None
        self.trace_mode = "trace"    # "trace" or "path"
        
        self.current_trace = []
        self.current_trace_index = 0

    def compose(self):
        # 1. Findings table
        self.findings_table = FindingsTable(id="findings-table")
        
        # 2. File tree
        self.file_tree = FileTree(self.source_dir, id="file-tree")
        
        # 3. Source viewer
        self.source_viewer = SourceViewer(id="source-viewer")
        self.source_viewer.set_source_dir(self.source_dir)

        # 4. Trace viewer
        self.trace_viewer = TraceViewer(id="trace-viewer")
        
        # 5. Summary panel
        self.summary_panel = SummaryPanel(id="summary-panel")
        
        # 6. Status bar
        self.status_bar = StatusBar(id="status-bar")

        # Layout composition
        yield self.findings_table
        with Container(id="middle-container"):
            yield self.file_tree
            yield self.source_viewer
        with Container(id="bottom-container"):
            yield self.trace_viewer
            yield self.summary_panel
        yield self.status_bar

    def on_mount(self):
        self.findings_table.focus()
        self.load_data_into_views()
        self.count_files_async()

    def load_data_into_views(self):
        findings = self.loader.get_findings()
        reviews = self.loader.reviews
        self.findings_table.update_data(
            findings, 
            reviews,
            severity_filter=self.severity_filter,
            type_filter=self.type_filter,
            search_query=self.search_query
        )
        self.update_status_bar()
        # Highlight first finding if available
        if findings:
            self.call_after_refresh(self.select_first_finding)

    def select_first_finding(self):
        if len(self.findings_table.rows) > 0:
            self.findings_table.move_cursor(row=0)
            self.sync_active_finding()

    def count_files_async(self):
        def worker():
            count = 0
            try:
                if self.source_dir and os.path.exists(self.source_dir):
                    for _, _, files in os.walk(self.source_dir):
                        count += len(files)
            except Exception:
                pass
            self.app.call_from_thread(self.set_file_count, count)
        threading.Thread(target=worker, daemon=True).start()

    def set_file_count(self, count):
        self.file_count = count
        self.update_status_bar()

    def update_status_bar(self):
        findings = self.loader.get_findings()
        
        # Extract counts
        high_count = sum(1 for f in findings if f.get("severity", "").upper() == "HIGH")
        info_count = sum(1 for f in findings if f.get("severity", "").upper() == "INFO")

        # Project name
        proj_name = Path(self.source_dir).name if self.source_dir else "unknown"

        # Current finding index
        current_idx_val = self.findings_table.selected_finding_index
        current_idx = 0
        if current_idx_val is not None:
            # find index in the DataTable rows
            row_keys = list(self.findings_table.rows.keys())
            for idx, rk in enumerate(row_keys, 1):
                if rk.value == str(current_idx_val):
                    current_idx = idx
                    break

        self.status_bar.project_name = proj_name
        self.status_bar.file_count = self.file_count
        self.status_bar.total_findings = len(self.findings_table.rows)
        self.status_bar.high_count = high_count
        self.status_bar.info_count = info_count
        self.status_bar.current_idx = current_idx

    # Synchronize all details when finding is highlighted
    def sync_active_finding(self):
        finding_idx = self.findings_table.selected_finding_index
        if finding_idx is None:
            self.summary_panel.update_finding(None, "")
            self.trace_viewer.update_finding(None, self.trace_mode)
            self.update_status_bar()
            return

        finding = self.loader.get_findings()[finding_idx]
        if finding:
            finding_id = finding.get("id")
            # 1. Update summary panel
            triage_display = self.loader.get_review_display(finding_id)
            self.summary_panel.update_finding(finding, triage_display)

            # 2. Update trace viewer
            self.trace_viewer.update_finding(finding, self.trace_mode)

            # 3. Initialize trace navigator state
            trace = finding.get("taint_trace", []) if self.trace_mode == "trace" else finding.get("full_path", [])
            self.current_trace = trace
            self.current_trace_index = 0
            
            # 4. Sync trace step (handles SourceViewer, FileTree, SummaryPanel, and active indicator)
            self.sync_trace_step()

            self.update_status_bar()

    def sync_trace_step(self):
        self._is_syncing_trace = True
        try:
            if not self.current_trace or self.current_trace_index >= len(self.current_trace):
                self.status_bar.trace_progress = "No Trace Available"
                # Fallback to sink file/line if trace is empty
                finding_idx = self.findings_table.selected_finding_index
                if finding_idx is not None:
                    finding = self.loader.get_findings()[finding_idx]
                    fallback_file = finding.get("file") or finding.get("sink_file")
                    fallback_line = finding.get("sink_line", 1)
                    if fallback_file:
                        self.source_viewer.show_file(fallback_file, fallback_line)
                        self.file_tree.select_file_path(fallback_file)
                return
                
            step = self.current_trace[self.current_trace_index]
            
            if type(step) is dict:
                step_file = step.get("file")
                step_line = step.get("line", 1)
            else:
                # Full path string
                step_file = self.findings_table.selected_finding_id # fallback
                step_line = 1
                
            # 1. Update trace viewer cursor (►)
            self.trace_viewer.update_active_step(self.current_trace_index)
            
            # 2. Update source viewer
            if step_file and type(step) is dict:
                self.source_viewer.show_file(step_file, step_line, trace=self.current_trace)
                
            # 3. Auto Expand Cross-file in File Explorer
            if step_file and type(step) is dict:
                self.file_tree.select_file_path(step_file)
                
            # 4. Update summary panel with Mini Map
            self.summary_panel.update_trace_step(self.current_trace, self.current_trace_index)
            
            # 5. Update status bar
            role = step.get("role", "PROPAGATION").upper() if type(step) is dict else "PATH"
            self.status_bar.trace_progress = f"{self.current_trace_index + 1}/{len(self.current_trace)} {role} @ {step_file}:{step_line}"
        finally:
            self._is_syncing_trace = False

    # ----------------- EVENTS -----------------

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        self.sync_active_finding()

    def on_list_view_highlighted(self, event: ListView.Highlighted):
        # Trace step highlighted via arrow keys up/down
        if event.list_view == self.trace_viewer:
            item = event.item
            if item and hasattr(item, 'index'):
                self.current_trace_index = item.index
                self.sync_trace_step()

    def on_list_view_selected(self, event: ListView.Selected):
        # Trace step clicked / ENTER pressed to follow
        if event.list_view == self.trace_viewer:
            item = event.item
            if item and hasattr(item, 'index'):
                self.current_trace_index = item.index
                self.sync_trace_step()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        # Prevent async event loop override:
        # If the file is already loaded in the SourceViewer (e.g. by trace navigator),
        # do not reload it and reset the cursor to line 1.
        if self.source_viewer.current_file_path:
            try:
                if self.source_viewer.current_file_path.samefile(event.path):
                    return
            except Exception:
                if str(self.source_viewer.current_file_path).lower() == str(event.path).lower():
                    return
            
        # When a new file is selected manually in the tree, open it
        self.source_viewer.show_file(str(event.path), 1)

    # ----------------- ACTIONS -----------------

    def action_help(self):
        self.app.push_screen(HelpModal())

    def action_toggle_severity(self):
        # ALL -> HIGH -> INFO -> ALL
        if self.severity_filter is None:
            self.severity_filter = "HIGH"
        elif self.severity_filter == "HIGH":
            self.severity_filter = "INFO"
        else:
            self.severity_filter = None
        self.load_data_into_views()

    def action_filter_type(self):
        # Extract unique types
        findings = self.loader.get_findings()
        types = sorted(list(set(f.get("vuln_type", "unknown") for f in findings)))
        
        def handle_dismiss(selected_type):
            if selected_type == "ALL":
                self.type_filter = None
            elif selected_type is not None:
                self.type_filter = selected_type
            self.load_data_into_views()

        self.app.push_screen(TypeFilterModal(types), handle_dismiss)

    def action_search_findings(self):
        def handle_dismiss(query):
            if query is not None:
                self.search_query = query if query.strip() != "" else None
                self.load_data_into_views()

        self.app.push_screen(SearchModal(), handle_dismiss)

    def action_toggle_trace(self):
        # Focus toggle between table and trace viewer
        if self.app.focused == self.trace_viewer:
            self.findings_table.focus()
        else:
            self.trace_viewer.focus()

    def action_reload_report(self):
        self.loader.load_report()
        self.loader.load_reviews()
        self.load_data_into_views()

    def action_full_path_mode(self):
        self.trace_mode = "path"
        self.sync_active_finding()

    def action_taint_trace_mode(self):
        self.trace_mode = "trace"
        self.sync_active_finding()

    def action_ai_verdict(self):
        finding_idx = self.findings_table.selected_finding_index
        if finding_idx is None:
            return
        finding = self.loader.get_findings()[finding_idx]
        if finding:
            ai_verdict = finding.get("ai_review") or finding.get("ai_verdict") or finding.get("ai_analysis") or finding.get("ai_explanation")
            if type(ai_verdict) is dict:
                formatted_text = ""
                fields_order = ["status", "confidence", "severity", "reason", "source", "sink", "validation", "sanitization", "taint_trace", "exploitability", "recommendation"]
                
                for key in fields_order:
                    if key in ai_verdict:
                        val = ai_verdict[key]
                        if isinstance(val, list):
                            if not val:
                                val_str = "None"
                            else:
                                val_str = "\n  - " + "\n  - ".join(str(v) for v in val)
                        else:
                            val_str = str(val)
                        formatted_text += f"[bold cyan]{key.capitalize().replace('_', ' ')}:[/bold cyan] {val_str}\n\n"
                
                for key, val in ai_verdict.items():
                    if key not in fields_order:
                        formatted_text += f"[bold cyan]{key.capitalize().replace('_', ' ')}:[/bold cyan] {val}\n\n"
                
                ai_verdict = formatted_text.strip()
                
            if ai_verdict:
                self.app.push_screen(AIVerdictModal(str(ai_verdict)))
            else:
                self.app.bell() # Play terminal bell indicating no AI Verdict

    def action_verify_finding(self):
        self.app.notify("Bat dau Verify...", title="Debug")
        finding_idx = self.findings_table.selected_finding_index
        if finding_idx is None:
            self.app.notify("Khong co finding nao duoc chon!", severity="error")
            return
        finding = self.loader.get_findings()[finding_idx]
        
        # UI Feedback
        self.status_bar.trace_progress = "🤖 AI is verifying finding... Please wait."
        self.app.notify("Dang gui request cho Ollama 14B...", title="AI Verifier")
        
        # Spawn worker thread
        def _verify_worker(app, finding, finding_idx):
            try:
                from ai_verifier.prompt_builder import build_prompt
                from ai_verifier.config import review
                
                prompt = build_prompt(finding)
                ai_review = review(prompt)
                
                # Callback to main thread
                app.call_from_thread(self._verify_completed, finding_idx, ai_review)
            except Exception as e:
                app.call_from_thread(self._verify_completed, finding_idx, {"error": str(e)})
                
        threading.Thread(target=_verify_worker, args=(self.app, finding, finding_idx), daemon=True).start()

    def _verify_completed(self, finding_idx: int, ai_review: dict):
        findings = self.loader.get_findings()
        if 0 <= finding_idx < len(findings):
            findings[finding_idx]["ai_review"] = ai_review
            # Automatically triage based on AI status
            if ai_review.get("status") == "verified":
                self.loader.save_review(findings[finding_idx].get("id"), "TP")
            elif ai_review.get("status") == "likely_false_positive":
                self.loader.save_review(findings[finding_idx].get("id"), "FP")
            
            # Save the report to persist ai_review
            self.loader.save_report_data()
            
            # Update UI
            self.load_data_into_views()
            
            # Restore selection (find row key and move cursor there)
            row_keys = list(self.findings_table.rows.keys())
            for idx, rk in enumerate(row_keys):
                if rk.value == str(finding_idx):
                    self.findings_table.move_cursor(row=idx)
                    break
            self.sync_active_finding()
            
            self.status_bar.trace_progress = "✅ AI Verification completed!"
            
            # Auto-open the verdict popup
            self.action_ai_verdict()

    def action_quit_app(self):
        self.app.exit()

    def action_clear_filters(self):
        self.severity_filter = None
        self.type_filter = None
        self.search_query = None
        self.load_data_into_views()

    # Triage functions
    def apply_triage(self, status):
        finding_idx = self.findings_table.selected_finding_index
        if finding_idx is not None:
            finding = self.loader.get_findings()[finding_idx]
            finding_id = finding.get("id")
            self.loader.save_review(finding_id, status)
            # Update findings table row and summary panel
            self.load_data_into_views()
            # Restore selection (find row key and move cursor there)
            row_keys = list(self.findings_table.rows.keys())
            for idx, rk in enumerate(row_keys):
                if rk.value == str(finding_idx):
                    self.findings_table.move_cursor(row=idx)
                    break
            self.sync_active_finding()

    def action_triage_tp(self):
        self.apply_triage("TP")

    def action_triage_fp(self):
        self.apply_triage("FP")

    def action_triage_rev(self):
        self.apply_triage("REV")

    # Trace Navigator actions
    def action_next_trace_step(self):
        if self.current_trace and self.current_trace_index < len(self.current_trace) - 1:
            self.current_trace_index += 1
            self.sync_trace_step()

    def action_prev_trace_step(self):
        if self.current_trace and self.current_trace_index > 0:
            self.current_trace_index -= 1
            self.sync_trace_step()

    def action_jump_trace_source(self):
        if self.current_trace:
            self.current_trace_index = 0
            self.sync_trace_step()

    def action_jump_trace_sink(self):
        if self.current_trace:
            self.current_trace_index = len(self.current_trace) - 1
            self.sync_trace_step()
