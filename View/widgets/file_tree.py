from pathlib import Path
from typing import Iterable
from textual.widgets import DirectoryTree

class FileTree(DirectoryTree):
    def __init__(self, path: str, **kwargs):
        super().__init__(path, **kwargs)
        self.border_title = " File Explorer "

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Filter paths to only show directories and .php files."""
        for path in paths:
            if path.is_dir() or path.suffix.lower() == ".php":
                yield path

    def select_file_path(self, file_path_str: str):
        """
        Attempts to expand the tree to the specified file and select it.
        """
        if not file_path_str:
            return

        try:
            target_path = Path(file_path_str).resolve()
            root_path = Path(self.path).resolve()
        except Exception:
            return

        # Check if file is within root path
        try:
            relative = target_path.relative_to(root_path)
        except ValueError:
            # Maybe path is relative to the root already but was passed as relative?
            # E.g. targets/cross_func_test.php. Try joining with root.
            try:
                target_path = (root_path / file_path_str).resolve()
                relative = target_path.relative_to(root_path)
            except Exception:
                return

        # Traverse from root node down to the target path
        current_node = self.root
        if not current_node:
            return

        # Force expand root if not expanded
        if not current_node.is_expanded:
            current_node.expand()

        for part in relative.parts:
            # Ensure children are loaded
            if not current_node.is_expanded:
                current_node.expand()

            found = False
            for child in current_node.children:
                if child.data and hasattr(child.data, 'path'):
                    child_path = Path(child.data.path)
                    if child_path.name == part:
                        current_node = child
                        found = True
                        break
            
            if not found:
                # If child wasn't found, it might be because the tree builds dynamically.
                # In DirectoryTree, nodes load children when expanded.
                break

        if current_node:
            # Expand the final node if it's a directory, or just highlight it
            current_node.expand()
            self.select_node(current_node)
