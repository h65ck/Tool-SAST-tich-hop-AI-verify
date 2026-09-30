import os
from pathlib import Path
from textual.widgets import Static
from rich.text import Text

class SourceViewer(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = " Source Code Viewer "
        self.current_file_path = None
        self.source_dir = None
        self.lines = []
        self.file_cache = {}  # LRU cache mapping Path -> list of lines

    def set_source_dir(self, source_dir: str):
        self.source_dir = Path(source_dir) if source_dir else None

    def resolve_file(self, file_path_str: str) -> Path:
        if not self.source_dir:
            path = Path(file_path_str)
            return path if path.exists() else None
            
        file_path = Path(file_path_str.replace('\\', '/'))
        
        # 1. Try direct path under source_dir
        path = self.source_dir / file_path
        if path.exists():
            return path
            
        # 2. Try stripping components from the left one by one (handles overlapping paths)
        parts = file_path.parts
        for i in range(len(parts)):
            path = self.source_dir / Path(*parts[i:])
            if path.exists():
                return path
                
        # 3. Try matching by basename directly in source_dir
        path = self.source_dir / file_path.name
        if path.exists():
            return path
            
        # 4. Try absolute path
        abs_path = Path(file_path_str)
        if abs_path.is_absolute() and abs_path.exists():
            return abs_path
            
        return None

    def show_file(self, file_path_str: str, highlight_line: int, trace: list = None):
        """
        Loads the file and displays it, highlighting taint trace lines.
        Centers the scroll on highlight_line.
        """
        resolved = self.resolve_file(file_path_str)
        if not resolved:
            self.update(Text(f"File not found: {file_path_str}\n(Searched under source directory: {self.source_dir})", style="bold red"))
            self.border_title = f" Source Code Viewer [File Not Found] "
            return

        self.current_file_path = resolved
        self.border_title = f" Source Code Viewer - {resolved.name} "

        # Load lines from cache or disk
        if resolved in self.file_cache:
            self.lines = self.file_cache[resolved]
            # Move to end (mark as recently used)
            self.file_cache.pop(resolved)
            self.file_cache[resolved] = self.lines
        else:
            try:
                with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                    self.lines = f.read().splitlines()
                self.file_cache[resolved] = self.lines
                # Evict oldest if > 2
                if len(self.file_cache) > 2:
                    self.file_cache.pop(next(iter(self.file_cache)))
            except Exception as e:
                self.update(Text(f"Error reading file {resolved}: {e}", style="bold red"))
                return

        # Prepare trace line mapping
        # Map: line_number -> role
        trace_map = {}
        if trace:
            # We want to find steps in the trace that match the resolved filename
            for step in trace:
                step_file_resolved = self.resolve_file(step.get("file", ""))
                if step_file_resolved and step_file_resolved.resolve() == resolved.resolve():
                    line = step.get("line")
                    if line:
                        # Precedence: sink/source beats propagation
                        role = step.get("role", "propagation").lower()
                        existing_role = trace_map.get(line)
                        if not existing_role or role in ["sink", "source"]:
                            trace_map[line] = role

        # Define styles for trace roles (foreground on background)
        role_styles = {
            "source": ("#000000 on #a6e3a1", "SOURCE"),          # Black on Green
            "propagation": ("#000000 on #f9e2af", "PROPAGATION"),  # Black on Yellow
            "call": ("#ffffff on #89b4fa", "CALL"),             # White on Blue
            "return": ("#000000 on #89dceb", "RETURN"),           # Black on Cyan
            "safe_overwrite": ("#000000 on #74c7ec", "SAFE_OVERWRITE"), # Black on Bright Cyan
            "sink": ("#ffffff on #f38ba8", "SINK")               # White on Red
        }

        # Calculate locked viewport (Manual Slicing)
        # To guarantee the active line is centered and user cannot drag/scroll manually
        container_height = (self.size.height or 15) - 2  # -2 for borders
        half = container_height // 2
        
        start_idx = max(0, highlight_line - 1 - half)
        end_idx = min(len(self.lines), start_idx + container_height)
        
        # Adjust start if we hit the bottom so we always show a full page if possible
        if end_idx - start_idx < container_height and start_idx > 0:
            start_idx = max(0, end_idx - container_height)

        # Build Rich text
        text = Text()
        num_width = len(str(len(self.lines))) + 1
        
        for i in range(start_idx, end_idx):
            line_content = self.lines[i]
            line_num = i + 1
            line_role = trace_map.get(line_num)
            
            # Format line number with Active Marker
            padding = " " * max(1, num_width - len(str(line_num)))
            if line_num == highlight_line:
                num_str = f"▶{padding}{line_num} │ "
            else:
                num_str = f" {padding}{line_num} │ "
            
            if line_num == highlight_line:
                # This is the focused/active line from selection
                if line_role and line_role in role_styles:
                    color_style, role_name = role_styles[line_role]
                    text.append(num_str, style=f"bold {color_style}")
                    text.append(f"{line_content}   <-- {role_name} [ACTIVE]\n", style=f"bold {color_style}")
                else:
                    text.append(num_str, style="bold #000000 on #cdd6f4")
                    text.append(f"{line_content}   <-- [ACTIVE]\n", style="bold #000000 on #cdd6f4")
            elif line_role and line_role in role_styles:
                color_style, role_name = role_styles[line_role]
                text.append(num_str, style=f"bold {color_style}")
                text.append(f"{line_content}   <-- {role_name}\n", style=color_style)
            else:
                text.append(num_str, style="#585b70")
                text.append(f"{line_content}\n", style="#cdd6f4")

        self.update(text)
