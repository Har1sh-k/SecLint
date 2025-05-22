import ast

def split_code(code: str):

    tree = ast.parse(code)

    chunks = []
    global_vars = []
    
    for node in tree.body:
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            code_chunk = ast.unparse(node)
            clean_code = "\n".join(l for l in code_chunk.splitlines() if l.strip())
            chunks.append(clean_code)
            
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            import_code = ast.get_source_segment(code, node)
            chunks.append(import_code)
            
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            assign_code = ast.get_source_segment(code, node)
            global_vars.append(assign_code)
            
        elif (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
            and len(node.test.comparators) == 1
            and isinstance(node.test.comparators[0], ast.Constant)
            and node.test.comparators[0].value == "__main__"
        ):
            code_chunk = ast.unparse(node)
            clean_code = "\n".join(l for l in code_chunk.splitlines() if l.strip())
            chunks.append(clean_code)   
        else:
            print(f"Skipping node of type {type(node).__name__}")
    chunks.append(global_vars)
    
    return chunks