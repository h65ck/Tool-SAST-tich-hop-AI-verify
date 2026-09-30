# [RESTRUCTURE_CHANGE]
class FunctionSummaryAnalyzer:
    def __init__(self, source_bytes, semgrep_data):
        self.source_bytes = source_bytes
        self.semgrep_data = semgrep_data
#return của function phụ thuộc param nào?
#sink bên trong function phụ thuộc param nào?
    def extract_text(self, node):
        if not node: return ""
        return self.source_bytes[node.start_byte:node.end_byte].decode('utf-8')

    def extract_all_variables(self, node):
        res = []
        if not node: return res
        if node.type == 'variable_name':
            res.append(self.extract_text(node))
        for c in node.named_children:
            res.extend(self.extract_all_variables(c))
        return res

    def analyze_all(self, functions):  # [CROSS_FUNC_CHANGE]
        summaries = {}
        for name, func_info in functions.items():
            summaries[name] = self.analyze_function(func_info)
        return summaries

    def analyze_function(self, func_info):  # [CROSS_FUNC_CHANGE]
        name = func_info["name"]
        params = func_info["params"]
        body_node = func_info["body_node"]
        
        summary = {
            "name": name,
            "params": params,
            "return_depends_on_params": [],#retủn phụ thuộc vào tham số nào
            "sink_depends_on_params": []#tham số nào phụ thuộc vào sink nào, loại sink và code của sink đó
        }
        
        if not body_node:
            return summary
            
        # Initial state maps variable names to a set of parameter indices
        state = {}
        for i, param in enumerate(params):
            state[param] = {i}
            
        processed_sink_lines = set()

        def traverse(node):
            if not node:
                return

            if node.type == 'return_statement':
                expr = node.named_children[0] if node.named_children else None
                if expr:
                    vars_in_return = self.extract_all_variables(expr)
                    for var_name in vars_in_return:
                        if var_name in state:
                            summary["return_depends_on_params"].extend(list(state[var_name]))
                                    
            elif node.type == 'assignment_expression':
                left = node.child_by_field_name('left')
                right = node.child_by_field_name('right')
                if left and left.type == 'variable_name':
                    var_name = self.extract_text(left)
                    deps = set()
                    vars_in_right = self.extract_all_variables(right)
                    for r_name in vars_in_right:
                        if r_name in state:
                            deps.update(state[r_name])
                    state[var_name] = deps

            # Check for sink across ANY node
            current_line = node.start_point[0] + 1
            if current_line in self.semgrep_data.get("sinks", []) and current_line not in processed_sink_lines:
                # To prevent matching multiple inner nodes on the same line, only match the outermost statement-like or call node
                if node.type in ['expression_statement', 'return_statement', 'function_call_expression', 'echo_statement', 'if_statement']:
                    processed_sink_lines.add(current_line)
                    sink_type = self.semgrep_data.get("sink_types", {}).get(current_line, "unknown")
                    vars_in_sink = self.extract_all_variables(node)
                    for a_name in vars_in_sink:
                        if a_name in state:
                            for p_idx in state[a_name]:
                                summary["sink_depends_on_params"].append({
                                    "param_index": p_idx,
                                    "sink_type": sink_type,
                                    "sink_code": self.extract_text(node),
                                    "sink_line": current_line
                                })

            for child in node.named_children:
                traverse(child)

        traverse(body_node)
        
        # Deduplicate
        summary["return_depends_on_params"] = list(set(summary["return_depends_on_params"]))
        
        unique_sinks = []
        seen_sinks = set()
        for s in summary["sink_depends_on_params"]:
            t = (s["param_index"], s["sink_type"], s["sink_line"])
            if t not in seen_sinks:
                seen_sinks.add(t)
                unique_sinks.append(s)
        summary["sink_depends_on_params"] = unique_sinks
        
        return summary
