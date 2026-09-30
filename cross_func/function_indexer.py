# [RESTRUCTURE_CHANGE]
class FunctionIndexer:
    def __init__(self, source_bytes):
        self.source_bytes = source_bytes

    def extract_text(self, node):
        if not node: return ""
        return self.source_bytes[node.start_byte:node.end_byte].decode('utf-8')

    def index(self, root_node):  # [CROSS_FUNC_CHANGE]
        functions = {}
        for child in root_node.named_children:
            if child.type == "function_definition":
                name_node = child.child_by_field_name("name")#lay ten function dang byte

                name = self.extract_text(name_node)# chuyen thanh dang ro
                
                params_node = child.child_by_field_name("parameters")#lay bien dang byte
                params = []
                if params_node:
                    for param in params_node.named_children:
                        if param.type == "simple_parameter":
                            var_node = param.child_by_field_name("name")
                            if var_node and var_node.type == "variable_name":
                                params.append(self.extract_text(var_node))
                            else:
                                params.append(self.extract_text(param))
                        else:
                            params.append(self.extract_text(param))
                
                body_node = child.child_by_field_name("body")
                functions[name] = {
                    "name": name,
                    "params": params,
                    "body_node": body_node,
                    "function_node": child
                }
        return functions
