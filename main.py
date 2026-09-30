import os
import sys#doc tham so tung lệnh
from tree_sitter import Parser, Language
import tree_sitter_php as tsphp

from semgrep_engine.semgrep_runner import run_semgrep  # [RESTRUCTURE_CHANGE]
from core.cfg_node import CFGNode  # [RESTRUCTURE_CHANGE]
from core.cfg_builder import CFGBuilder  # [RESTRUCTURE_CHANGE]
from core.hybrid_analyzer import HybridAnalyzer  # [RESTRUCTURE_CHANGE]
from core.reporter import Reporter  # [RESTRUCTURE_CHANGE]
from cross_func.function_indexer import FunctionIndexer  # [RESTRUCTURE_CHANGE]
from cross_func.function_summary import FunctionSummaryAnalyzer  # [RESTRUCTURE_CHANGE]
from cross_file.project_scanner import ProjectScanner  # [CROSS_FILE_CHANGE]
from cross_file.project_index import ProjectIndex  # [CROSS_FILE_CHANGE]

def main():
    target_path = sys.argv[1] if len(sys.argv) > 1 else "targets/test_target.php"  # [RESTRUCTURE_CHANGE]
    if not os.path.exists(target_path):
        print(f"Target path {target_path} not found.")
        return

    # [CROSS_FILE_CHANGE]
    scanner = ProjectScanner()
    php_files = scanner.collect_php_files(target_path)

    if not php_files:
        print("[WARN] No PHP files found.")
        return

    # Set up parser
    PHP_LANGUAGE = Language(tsphp.language_php())#trister parser
    parser = Parser(PHP_LANGUAGE)

    project_index = ProjectIndex()

    # Pass 1: Parse files, run Semgrep per file, and index functions
    for file_path in php_files:
        print(f"\n>>> Processing file: {file_path}")
        semgrep_data = run_semgrep(file_path)
        print(f"Semgrep found for {file_path}: {semgrep_data}")

        with open(file_path, "rb") as f:
            source_bytes = f.read()

        tree = parser.parse(source_bytes)
        project_index.add_file(file_path, source_bytes, tree, semgrep_data)

        # Index functions
        indexer = FunctionIndexer(source_bytes)
        functions = indexer.index(tree.root_node)
        project_index.add_functions(file_path, functions)

    # Pass 2: Create global summaries
    # [CROSS_FILE_CHANGE]
    # Cross-file MVP does not merge CFGs across files.
    # It builds a project-wide function summary table.
    # Each file is analyzed independently, but function calls can use summaries from other files.
    for func_name, func_info in project_index.functions.items():
        file_path = func_info["file_path"]
        file_info = project_index.files[file_path]

        summary_analyzer = FunctionSummaryAnalyzer(
            file_info["source_bytes"],
            file_info["semgrep_data"]
        )
        summary = summary_analyzer.analyze_function(func_info)
        summary["function_file"] = file_path

        # Tag each sink dependency with its originating file
        for dep in summary.get("sink_depends_on_params", []):
            dep["sink_file"] = file_path

        project_index.add_function_summary(func_name, summary)

    global_summaries = project_index.get_all_function_summaries()

    # Pass 3: Analyze each file using the global summaries
    print("\n>>> Starting Hybrid Analyzer (Tree-sitter CFG + Taint Tracking) on all files...")
    all_findings = []

    for file_path in php_files:
        print(f"\n=== Analyzing File: {file_path} ===")
        file_info = project_index.files[file_path]
        
        entry_node = CFGNode(0, "entry", "BẮT ĐẦU")
        builder = CFGBuilder(file_info["source_bytes"], file_info["semgrep_data"])
        builder.build_from_block(file_info["tree"].root_node, [entry_node])

        analyzer = HybridAnalyzer(
            file_info["source_bytes"],
            file_info["semgrep_data"],
            function_summaries=global_summaries,#analyz ở file này nhưng có thể dùng func ở file khác
            current_file=file_path
        )
        analyzer.analyze(entry_node, current_state={}, path_history=[])

        # Aggregate findings and assign file path
        for finding in analyzer.get_findings():
            finding["file"] = file_path
            all_findings.append(finding)

    print("\n=== ENGINE SAST HYBRID (SEMGREP + PATH-SENSITIVE) ===")
    reporter = Reporter(all_findings)
    reporter.print_findings()

    report_path = "reports/report.json"  # [RESTRUCTURE_CHANGE]
    os.makedirs(os.path.dirname(report_path), exist_ok=True)  # [RESTRUCTURE_CHANGE]
    reporter.export_json(report_path)  # [RESTRUCTURE_CHANGE]

    num_findings = len(all_findings)
    if num_findings > 0:
        print(f"\nCó {num_findings} lỗ hổng được phát hiện.")
        print(f"Báo cáo đã được lưu tại: {report_path}")
        print(f"Vui lòng chạy lệnh sau để mở giao diện TUI và dùng AI xác minh (bấm phím V):")
        print(f"  python -m View.app --report {report_path} --source {target_path}")

if __name__ == "__main__":
    main()
