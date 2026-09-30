from core.cfg_node import CFGNode  # [RESTRUCTURE_CHANGE]

class CFGBuilder:
    def __init__(self, source_bytes, semgrep_data):
        self.source_bytes = source_bytes
        self.node_counter = 0
        self.semgrep_data = semgrep_data

    def extract_text(self, node):
        if not node: return ""
        return self.source_bytes[node.start_byte:node.end_byte].decode('utf-8')

    def create_node(self, stmt_type, code_text, ast_node=None):
        self.node_counter += 1
        return CFGNode(self.node_counter, stmt_type, code_text, ast_node)

    def build_from_block(self, block_node, previous_exits):
        if not block_node: return previous_exits
        current_exits = previous_exits

        if block_node.type in ['program', 'compound_statement']:
            statements = block_node.named_children
        else:
            statements = [block_node]

        for child in statements:
            if child.type == "function_definition":  # [CROSS_FUNC_CHANGE]
                continue

            elif child.type == "return_statement":  # [CROSS_FUNC_CHANGE]
                node = self.create_node("return", self.extract_text(child), child)
                for prev in current_exits:
                    prev.add_next(node)
                current_exits = []
                continue

            elif child.type == 'expression_statement':
                expr = child.named_children[0]
                current_line = expr.start_point[0] + 1
                
                if expr.type == 'assignment_expression':
                    node = self.create_node("assign", self.extract_text(expr), expr)
                    for prev in current_exits: prev.add_next(node)
                    current_exits = [node]
                else:
                    node = self.create_node("normal", self.extract_text(expr), expr)
                    for prev in current_exits: prev.add_next(node)
                    current_exits = [node]

            elif child.type == 'if_statement':
                condition_node = child.child_by_field_name('condition')
                cond_text = self.extract_text(condition_node) if condition_node else "(...)"
                
                cond_node = self.create_node("if_cond", f"[IF] {cond_text}", condition_node)
                for prev in current_exits: prev.add_next(cond_node)

                true_block = child.child_by_field_name('body')
                true_exits = self.build_from_block(true_block, [cond_node])

                all_exits = true_exits
                current_false_exits = [cond_node]

                for sub in child.named_children:
                    if sub.type == 'else_if_clause':
                        sub_cond_node = sub.child_by_field_name('condition')
                        sub_cond_text = self.extract_text(sub_cond_node) if sub_cond_node else "(...)"
                        elif_cond_node = self.create_node("if_cond", f"[ELSEIF] {sub_cond_text}", sub_cond_node)
                        for prev in current_false_exits: prev.add_next(elif_cond_node)
                        
                        elif_body = sub.child_by_field_name('body')
                        elif_exits = self.build_from_block(elif_body, [elif_cond_node])
                        all_exits.extend(elif_exits)
                        current_false_exits = [elif_cond_node]
                    
                    elif sub.type == 'else_clause':
                        else_body = sub.child_by_field_name('body')
                        if not else_body and sub.named_children:
                            else_body = sub.named_children[0]
                        else_exits = self.build_from_block(else_body, current_false_exits)
                        all_exits.extend(else_exits)
                        current_false_exits = []

                all_exits.extend(current_false_exits)
                current_exits = all_exits

            elif child.type == 'while_statement':
                condition_node = child.child_by_field_name('condition')
                cond_text = self.extract_text(condition_node) if condition_node else "(...)"
                cond_node = self.create_node("while_cond", f"[WHILE] {cond_text}", condition_node)
                
                for prev in current_exits: prev.add_next(cond_node)
                
                body = child.child_by_field_name('body')
                body_exits = self.build_from_block(body, [cond_node])
                
                for prev in body_exits: prev.add_next(cond_node)
                
                current_exits = [cond_node]

            elif child.type == 'switch_statement':
                condition_node = child.child_by_field_name('condition')
                cond_text = self.extract_text(condition_node) if condition_node else "(...)"
                switch_node = self.create_node("switch_cond", f"[SWITCH] {cond_text}")
                
                for prev in current_exits: prev.add_next(switch_node)
                
                body = child.child_by_field_name('body')
                if not body or body.type != 'switch_block':
                    current_exits = [switch_node]
                    continue
                
                switch_exits = []
                fallthrough_exits = []
                
                for case_child in body.named_children:
                    if case_child.type in ['case_statement', 'default_statement']:
                        if case_child.type == 'case_statement':
                            val_node = case_child.child_by_field_name('value')
                            val_text = self.extract_text(val_node) if val_node else "(...)"
                            case_node = self.create_node("case_cond", f"[CASE] {val_text}")
                        else:
                            val_node = None
                            case_node = self.create_node("case_cond", "[DEFAULT]")
                            
                        switch_node.add_next(case_node)
                        case_entry_exits = [case_node] + fallthrough_exits
                        
                        stmts = [c for c in case_child.named_children if c != val_node]
                        case_exits = case_entry_exits
                        has_break = False
                        
                        for stmt in stmts:
                            if stmt.type == 'break_statement':
                                has_break = True
                                switch_exits.extend(case_exits)
                                case_exits = []
                                break
                            else:
                                case_exits = self.build_from_block(stmt, case_exits)
                        
                        if not has_break:
                            fallthrough_exits = case_exits
                        else:
                            fallthrough_exits = []

                switch_exits.extend(fallthrough_exits)
                has_default = any(c.type == 'default_statement' for c in body.named_children)
                if not has_default:
                    switch_exits.append(switch_node)
                
                current_exits = switch_exits

        return current_exits
