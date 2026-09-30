class CFGNode:
    def __init__(self, node_id, stmt_type, code_text, ast_node=None):
        self.id = node_id           
        self.type = stmt_type       
        self.code_text = code_text  
        self.ast_node = ast_node    
        self.next_nodes = []        

    def add_next(self, node):
        if node not in self.next_nodes:
            self.next_nodes.append(node)
