def score_file(info: dict) -> str:
    complexity = info.get("complexity_estimate", 0)
    dependents = len(info.get("called_by", []))
    if complexity > 15 and dependents > 3: return "red"
    if complexity > 15 or dependents > 3: return "yellow"
    return "green"
