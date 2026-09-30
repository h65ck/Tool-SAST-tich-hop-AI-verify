class HybridAnalyzer:
    def __init__(self, source_bytes, semgrep_data, function_summaries=None, current_file=None):  # [CROSS_FILE_CHANGE]
        self.source_bytes = source_bytes
        self.paths_found = 0
        self.semgrep_data = semgrep_data
        self.function_summaries = function_summaries or {}  # [CROSS_FUNC_CHANGE]
        self.current_file = current_file
        self.findings = []

    def extract_text(self, node):
        if not node: return ""
        return self.source_bytes[node.start_byte:node.end_byte].decode('utf-8')

    def extract_all_variables(self, node):
        vars_found = []
        if not node: return vars_found
        if node.type == 'variable_name':
            vars_found.append(self.extract_text(node))
        else:
            for child in node.named_children:
                vars_found.extend(self.extract_all_variables(child))
        return vars_found

    def find_function_calls(self, node):
        calls = []
        if not node: return calls
        if node.type == 'function_call_expression':
            calls.append(node)
        for child in node.named_children:
            calls.extend(self.find_function_calls(child))
        return calls

    # [REPORT_TRACE_CHANGE]
    def build_propagation_trace(self, traces, source_var, current_file, line, code, target_var):
        base = list(traces.get(source_var, []))
        base.append({
            "role": "propagation",
            "file": current_file,
            "line": line,
            "code": code,
            "var": target_var
        })
        return base

    def analyze(self, cfg_node, current_state, path_history, visited=None, trace_state=None):
        if visited is None:
            visited = set()
            
        if cfg_node.id in visited:
            return
            
        visited = visited.copy()
        visited.add(cfg_node.id)
        
        state = current_state.copy()
        # [REPORT_TRACE_CHANGE]
        if trace_state is None:
            trace_state = {}
        traces = {k: list(v) for k, v in trace_state.items()}
        
        path = path_history + [cfg_node.code_text]

        # --- [TÍCH HỢP SEMGREP]: Bơm độc từ thông tin Semgrep ---
        # Detect sources on ANY node type and explicitly taint the superglobal
        if cfg_node.ast_node:
            current_line = cfg_node.ast_node.start_point[0] + 1
            if current_line in self.semgrep_data.get("sources", []):
                vars_in_node = self.extract_all_variables(cfg_node.ast_node)
                for v in vars_in_node:
                    if v in ["$_GET", "$_POST", "$_COOKIE", "$_REQUEST", "$_SERVER", "$_FILES", "file_get_contents"]:
                        state[v] = "TAINTED"
                        if v not in traces:
                            traces[v] = [{
                                "role": "source",
                                "file": self.current_file,
                                "line": current_line,
                                "code": cfg_node.code_text,
                                "var": v
                            }]

        if cfg_node.type == "assign":
            left = cfg_node.ast_node.child_by_field_name('left')
            right = cfg_node.ast_node.child_by_field_name('right')
            
            if left and right:
                var_name = self.extract_text(left)
                current_line = cfg_node.ast_node.start_point[0] + 1
                
                is_source_line = current_line in self.semgrep_data.get("sources", [])
                
                is_tainted_from_right = False
                tainted_arg = None
                
                # --- PHẦN VIỆC CỦA ĐIỀU TRA VIÊN: Truy vết lây nhiễm chéo ---
                if right.type == "subscript_expression":
                    for c in right.named_children:
                        if c.type == "variable_name":
                            parent_var = self.extract_text(c)
                            if state.get(parent_var) == "TAINTED":
                                is_tainted_from_right = True
                                tainted_arg = parent_var
                                break 
                elif right.type == 'string' or right.type in ['integer', 'float']:
                    is_tainted_from_right = False
                elif right.type == 'variable_name':
                    right_text = self.extract_text(right)
                    if state.get(right_text) == "TAINTED":
                        is_tainted_from_right = True
                        tainted_arg = right_text
                elif right.type == 'function_call_expression':  # [CROSS_FUNC_CHANGE]
                    func_name_node = right.child_by_field_name('function')
                    func_name = self.extract_text(func_name_node)
                    summary = self.function_summaries.get(func_name)
                    args_node = right.child_by_field_name('arguments')
                    
                    if summary and args_node:
                        args_list = []
                        for arg in args_node.named_children:
                            vars_in_arg = self.extract_all_variables(arg)
                            if vars_in_arg:
                                args_list.append(vars_in_arg[0])
                            else:
                                args_list.append("unknown")
                        
                        for p_idx in summary.get("return_depends_on_params", []):
                            if p_idx < len(args_list):
                                arg_var = args_list[p_idx]
                                if state.get(arg_var) == "TAINTED":
                                    is_tainted_from_right = True
                                    tainted_arg = arg_var
                                    break
                                    
                        # Check sinks triggered by params inside the assignment (Interprocedural Sink Detection)
                        for s in summary.get("sink_depends_on_params", []):
                            p_idx = s["param_index"]
                            if p_idx < len(args_list):
                                arg_var = args_list[p_idx]
                                if state.get(arg_var) == "TAINTED":
                                    self.paths_found += 1
                                    vuln_type = s["sink_type"]
                                    
                                    taint_trace = list(traces.get(arg_var, []))
                                    taint_trace.append({
                                        "role": "call",
                                        "file": self.current_file,
                                        "line": current_line,
                                        "code": cfg_node.code_text,
                                        "var": arg_var,
                                        "function": func_name,
                                        "function_file": summary.get("function_file")
                                    })
                                    taint_trace.append({
                                        "role": "sink",
                                        "file": summary.get("function_file"),
                                        "line": s["sink_line"],
                                        "code": s["sink_code"],
                                        "var": summary["params"][p_idx] if p_idx < len(summary["params"]) else "unknown"
                                    })
                                    
                                    finding = {
                                        "id": self.paths_found,
                                        "status": "TAINTED",
                                        "severity": "HIGH",
                                        "vuln_type": vuln_type,
                                        "sink_code": s["sink_code"],
                                        "tainted_variables": [arg_var],
                                        "path": path,
                                        "full_path": path,
                                        "taint_trace": taint_trace,
                                        "sink_line": s["sink_line"],
                                        "sink_file": summary.get("function_file"),
                                        "cross_file": summary.get("function_file") != self.current_file,
                                        "interprocedural": True,
                                        "message": f"Found tainted sink at path {self.paths_found} via {func_name}()"
                                    }
                                    self.findings.append(finding)
                    else:
                        # [TAINT_FALLBACK_CHANGE]
                        vars_in_call = self.extract_all_variables(right)
                        for v in vars_in_call:
                            if state.get(v) == "TAINTED":
                                is_tainted_from_right = True
                                tainted_arg = v
                                break
                else:
                    var_in_right = self.extract_all_variables(right)
                    for v in var_in_right:
                        if state.get(v) == "TAINTED":
                            is_tainted_from_right = True
                            tainted_arg = v
                            break

                # Tổng hợp lại: biến bên trái sẽ TAINTED nếu nó nằm trên dòng Semgrep Source HOẶC nhận TAINTED từ bên phải
                if is_source_line:
                    state[var_name] = "TAINTED"
                    traces[var_name] = [{
                        "role": "source",
                        "file": self.current_file,
                        "line": current_line,
                        "code": cfg_node.code_text,
                        "var": var_name
                    }]
                elif is_tainted_from_right:
                    state[var_name] = "TAINTED"
                    if tainted_arg and tainted_arg in traces:
                        if right.type == 'function_call_expression' and summary:
                            func_name_node = right.child_by_field_name('function')
                            func_name = self.extract_text(func_name_node)
                            func_file = summary.get("function_file") if summary else None
                            
                            base = list(traces.get(tainted_arg, []))
                            base.append({
                                "role": "call",
                                "file": self.current_file,
                                "line": current_line,
                                "code": cfg_node.code_text,
                                "var": tainted_arg,
                                "function": func_name,
                                "function_file": func_file
                            })
                            base.append({
                                "role": "propagation",
                                "file": self.current_file,
                                "line": current_line,
                                "code": cfg_node.code_text,
                                "var": var_name
                            })
                            traces[var_name] = base
                        else:
                            traces[var_name] = self.build_propagation_trace(traces, tainted_arg, self.current_file, current_line, cfg_node.code_text, var_name)
                    else:
                        if var_name in traces: del traces[var_name]
                else:
                    state[var_name] = "SAFE" if right.type in ['string', 'integer', 'float'] else "UNKNOWN"
                    if right.type in ['string', 'integer', 'float']:
                        traces[var_name] = [{
                            "role": "safe_overwrite",
                            "file": self.current_file,
                            "line": current_line,
                            "code": cfg_node.code_text,
                            "var": var_name
                        }]
                    else:
                        if var_name in traces: del traces[var_name]

        # --- [TÍCH HỢP SEMGREP]: Đánh giá Sink cho mọi node ---
        if cfg_node.ast_node:
            current_line = cfg_node.ast_node.start_point[0] + 1
            if current_line in self.semgrep_data.get("sinks", []):
                self.paths_found += 1
                
                sink_line = current_line
                vuln_type = self.semgrep_data.get("sink_types", {}).get(sink_line, "unknown")
                
                # Quăng toàn bộ khối lệnh Sink vào máy xay, không cần quan tâm cấu trúc
                vars_in_sink = self.extract_all_variables(cfg_node.ast_node)
                
                final_status = "SAFE"
                infected_vars = []
                
                for v in vars_in_sink:
                    if state.get(v) == "TAINTED":
                        final_status = "TAINTED"
                        infected_vars.append(v)
                
                # [REPORT_TRACE_CHANGE]
                taint_trace = []
                if infected_vars:
                    first_infected = infected_vars[0]
                    taint_trace = list(traces.get(first_infected, []))
                    taint_trace.append({
                        "role": "sink",
                        "file": self.current_file,
                        "line": sink_line,
                        "code": cfg_node.code_text,
                        "var": first_infected
                    })

                finding = {
                    "id": self.paths_found,
                    "status": final_status,
                    "severity": "HIGH" if final_status == "TAINTED" else "INFO",
                    "vuln_type": vuln_type,
                    "sink_code": cfg_node.code_text,
                    "tainted_variables": infected_vars,
                    "path": path,
                    "full_path": path, # [REPORT_TRACE_CHANGE]
                    "taint_trace": taint_trace, # [REPORT_TRACE_CHANGE]
                    "sink_line": sink_line, # [REPORT_TRACE_CHANGE]
                    "sink_file": self.current_file, # [REPORT_TRACE_CHANGE]
                    "message": f"Found {'tainted' if final_status == 'TAINTED' else 'safe'} sink at path {self.paths_found}"
                }
                
                # Tránh duplicate finding cho cùng 1 dòng sink trên cùng path (nếu có nhiều node trên 1 dòng)
                is_duplicate = False
                for existing in self.findings:
                    if existing["sink_line"] == sink_line and existing["path"] == path:
                        is_duplicate = True
                        break
                        
                if not is_duplicate:
                    self.findings.append(finding)

        if cfg_node.type in ["normal", "if_cond", "while_cond"]:  # [CROSS_FUNC_CHANGE]
            calls = self.find_function_calls(cfg_node.ast_node)
            for call_node in calls:
                func_name_node = call_node.child_by_field_name('function')
                func_name = self.extract_text(func_name_node)
                summary = self.function_summaries.get(func_name)
                
                args_node = call_node.child_by_field_name('arguments')
                if summary and args_node:
                    args_list = [] # Lấy danh sách tham số thực tế từ AST
                    for arg in args_node.named_children:
                        vars_in_arg = self.extract_all_variables(arg)
                        if vars_in_arg:
                            args_list.append(vars_in_arg[0])
                        else:
                            args_list.append("unknown")
                        
                    for sink_dep in summary.get("sink_depends_on_params", []):
                        p_idx = sink_dep["param_index"]
                        if p_idx < len(args_list):
                            arg_var = args_list[p_idx]
                            if state.get(arg_var) == "TAINTED":
                                self.paths_found += 1
                                # [REPORT_TRACE_CHANGE]
                                call_line = call_node.start_point[0] + 1
                                taint_trace = list(traces.get(arg_var, []))
                                taint_trace.append({
                                    "role": "call",
                                    "file": self.current_file,
                                    "line": call_line,
                                    "code": cfg_node.code_text,
                                    "var": arg_var,
                                    "function": func_name,
                                    "function_file": summary.get("function_file")
                                })
                                taint_trace.append({
                                    "role": "sink",
                                    "file": sink_dep.get("sink_file", summary.get("function_file")),
                                    "line": sink_dep.get("sink_line"),
                                    "code": sink_dep.get("sink_code", ""),
                                    "var": arg_var
                                })

                                # [CROSS_FILE_CHANGE]
                                finding = {
                                    "id": self.paths_found,
                                    "status": "TAINTED",
                                    "severity": "HIGH",
                                    "vuln_type": sink_dep.get("sink_type", "unknown"),
                                    "sink_code": cfg_node.code_text,
                                    "real_sink_code": sink_dep.get("sink_code", ""),
                                    "tainted_variables": [arg_var],
                                    "interprocedural": True,
                                    "cross_file": summary.get("function_file") != self.current_file if self.current_file and summary.get("function_file") else False,
                                    "function": func_name,
                                    "function_file": summary.get("function_file"),
                                    "sink_file": sink_dep.get("sink_file", summary.get("function_file")),
                                    "sink_line": sink_dep.get("sink_line"), # [REPORT_TRACE_CHANGE]
                                    "path": path,
                                    "full_path": path, # [REPORT_TRACE_CHANGE]
                                    "taint_trace": taint_trace, # [REPORT_TRACE_CHANGE]
                                    "message": f"Found tainted interprocedural sink at path {self.paths_found}"
                                }
                                self.findings.append(finding)

        # [REPORT_TRACE_CHANGE]
        for next_node in cfg_node.next_nodes:
            self.analyze(next_node, state, path, visited, trace_state=traces)

    def get_findings(self):
        return self.findings
