import ast
from copy import deepcopy

def split_code(code: str, file_name: str):

    tree = ast.parse(code)
    
    code_chunks = {
        "metadata": {
                "name": None,
                "type": None,
                'file_name': file_name,
            },
        "start_line": None,
        "end_line": None,
        "code": None,
        
    }
    slices = []
    global_vars = ""
    imports = ""

    for node in tree.body:
        chunk = deepcopy(code_chunks)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            code_chunk = ast.unparse(node)
            clean_code = "\n".join(l for l in code_chunk.splitlines() if l.strip())
            chunk["code"] = clean_code
            chunk["start_line"] = node.lineno
            chunk["end_line"] = node.end_lineno
            chunk["metadata"]["name"] = node.name
            chunk["metadata"]["type"] = type(node).__name__

        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            import_code = ast.get_source_segment(code, node)
            imports += import_code + "\n"
            
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Global)):
            assign_code = ast.get_source_segment(code, node)
            global_vars += assign_code + "\n"
                      
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
            chunk["code"] = clean_code
            chunk["start_line"] = node.lineno
            chunk["end_line"] = node.end_lineno
            chunk["metadata"]["name"] = node.name
            chunk["metadata"]["type"] = type(node).__name__

        if chunk["code"] is not None:
            slices.append(chunk)

    if global_vars:
        chunk = deepcopy(code_chunks)
        chunk["code"] = global_vars
        chunk["start_line"] = 0
        chunk["end_line"] = 0
        chunk["metadata"]["name"] = "Global variables"
        chunk["metadata"]["type"] = "Global variable or assignment"
        slices.append(chunk)
    if imports:
        chunk = deepcopy(code_chunks)
        chunk["code"] = imports
        chunk["start_line"] = 0
        chunk["end_line"] = 0
        chunk["metadata"]["name"] = "Imports"
        chunk["metadata"]["type"] = "Import statement"
        slices.append(chunk)

    return slices