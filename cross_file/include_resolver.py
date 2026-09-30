# [CROSS_FILE_CHANGE]
import os#thu vien de lam viec voi duong dan va tap tin

class IncludeResolver:
    def __init__(self, source_bytes):
        self.source_bytes = source_bytes

    def extract_text(self, node):
        if not node: return ""
        return self.source_bytes[node.start_byte:node.end_byte].decode('utf-8')

    def find_string_content(self, node):
        if node.type == 'string_content':
            return [self.extract_text(node)]
        
        results = []
        for child in node.named_children:
            results.extend(self.find_string_content(child))#de quy de tim tat ca cac node string_content ben trong node hien tai va tra ve mot list chua noi dung cua cac node do
        return results

    def extract(self, root_node, file_path=None):
        # [CROSS_FILE_CHANGE]
        includes = []
        include_node_types = {
            "include_expression",
            "include_once_expression",
            "require_expression",
            "require_once_expression",
            
        }

        def traverse(node):
            if node.type in include_node_types:
                # Look for string_content inside this expression
                literals = self.find_string_content(node)
                for lit in literals:
                    if file_path:
                        dirname = os.path.dirname(file_path)
                        resolved = os.path.normpath(os.path.join(dirname, lit))
                        includes.append(resolved)
                    else:
                        includes.append(lit)
            
            for child in node.named_children:
                traverse(child)

        traverse(root_node)
        return includes
