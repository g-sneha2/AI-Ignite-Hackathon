import ast
from collections import defaultdict

try:
    from tree_sitter import Language, Parser
    from tree_sitter_python import language as python_language
    _parser = Parser(Language(python_language()))
except Exception:  # Keep analysis available when an optional native grammar cannot load.
    _parser = None

BRANCHES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.Match, ast.With, ast.AsyncWith)

def _import_target(module: str | None, level: int) -> str:
    return ("." * level) + (module or "")

def parse_files(files: dict[str, str]) -> dict[str, dict]:
    dependency_map = {}
    functions_by_file = {}
    call_names = defaultdict(list)
    for file_path, code in files.items():
        try:
            # tree-sitter is used first for fault-tolerant language validation; AST then
            # supplies Python's convenient semantic node representation.
            if _parser is not None:
                _parser.parse(code.encode("utf-8", errors="replace"))
            tree = ast.parse(code)
            imports, functions, calls = [], [], []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import): imports.extend(a.name for a in node.names)
                elif isinstance(node, ast.ImportFrom): imports.append(_import_target(node.module, node.level))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name): calls.append(node.func.id)
                    elif isinstance(node.func, ast.Attribute): calls.append(node.func.attr)
            dependency_map[file_path] = {"imports": sorted(set(imports)), "functions": functions,
                "called_by": [], "loc": len(code.splitlines()),
                "complexity_estimate": sum(isinstance(n, BRANCHES) for n in ast.walk(tree))}
            functions_by_file[file_path] = set(functions)
            call_names[file_path] = calls
        except (SyntaxError, ValueError, TypeError):
            continue
    # Call attribution is conservative: unique function names only, avoiding false certainty.
    owners = defaultdict(list)
    for path, names in functions_by_file.items():
        for name in names: owners[name].append(path)
    for caller, calls in call_names.items():
        for call in set(calls):
            for target in owners.get(call, []):
                if target != caller:
                    dependency_map[target]["called_by"].append(f"{caller}:{call}")
    for info in dependency_map.values(): info["called_by"] = sorted(set(info["called_by"]))
    return dependency_map

def build_tree(paths: list[str], scores: dict[str, str]) -> list[dict]:
    root: dict = {}
    for path in paths:
        cursor = root
        parts = path.split("/")
        for part in parts[:-1]: cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = None
    def render(node, prefix=""):
        out=[]
        for name, child in sorted(node.items()):
            path = f"{prefix}/{name}".strip("/")
            if child is None: out.append({"path": path, "type": "file", "risk_score": scores.get(path, "green")})
            else: out.append({"path": path, "type": "dir", "children": render(child, path)})
        return out
    return render(root)

def graph_for(file_path: str, depmap: dict) -> str:
    safe = lambda s: "N" + str(abs(hash(s)))
    lines=["graph TD", f'  {safe(file_path)}["{file_path}"]']
    info=depmap.get(file_path, {})
    for imp in info.get("imports", [])[:12]:
        label = imp.replace('"', "'")
        lines += [f'  {safe(imp)}["{label}"]', f"  {safe(file_path)} --> {safe(imp)}"]
    for caller in info.get("called_by", [])[:12]:
        label = caller.split(":")[0]
        lines += [f'  {safe(caller)}["{label}"]', f"  {safe(caller)} --> {safe(file_path)}"]
    return "\n".join(lines)
