from typing import Any

_cache: dict[tuple[str, str, str, str], Any] = {}
_repos: dict[str, dict] = {}

def get_cached(repo_id: str, feature: str, identifier: str, version: str = "v1"):
    return _cache.get((repo_id, feature, identifier, version))

def set_cached(repo_id: str, feature: str, identifier: str, value: Any, version: str = "v1"):
    _cache[(repo_id, feature, identifier, version)] = value
    return value

def get_repo(repo_id: str): return _repos.get(repo_id)
def set_repo(repo_id: str, data: dict): _repos[repo_id] = data
