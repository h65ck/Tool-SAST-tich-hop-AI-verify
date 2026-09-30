import argparse
import sys
from pathlib import Path
from textual.app import App
from View.models.report_loader import ReportLoader
from View.screens.main_screen import MainScreen

class LazySastApp(App):
    # Specify the path relative to View/app.py
    CSS_PATH = "theme/lazy_sast.tcss"

    def __init__(self, report_path: str, source_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.report_path = report_path
        
        # Ensure source_dir is always a directory, even if passed directly to constructor
        p_source = Path(source_dir).resolve()
        if p_source.is_file():
            self.source_dir = str(p_source.parent)
        else:
            self.source_dir = str(p_source)
            
        self.loader = ReportLoader(report_path)

    def on_mount(self):
        # Push the main interface screen
        self.push_screen(MainScreen(self.loader, self.source_dir))

def main():
    parser = argparse.ArgumentParser(description="Lazy-SAST TUI Viewer")
    parser.add_argument(
        "--report",
        type=str,
        default="report.json",
        help="Path to report.json file"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=".",
        help="Path to target source code directory"
    )
    args = parser.parse_args()

    report_file = Path(args.report).resolve()
    if not report_file.exists():
        print(f"Error: Report file '{args.report}' does not exist.")
        sys.exit(1)

    source_dir = Path(args.source).resolve()
    if not source_dir.exists():
        print(f"Warning: Source directory '{args.source}' does not exist.")
    elif source_dir.is_file():
        # If user passed a specific file instead of a directory, use its parent directory
        source_dir = source_dir.parent

    # Launch app
    app = LazySastApp(report_path=str(report_file), source_dir=str(source_dir))
    app.run()

if __name__ == "__main__":
    main()
