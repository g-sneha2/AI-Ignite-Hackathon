import hashlib, os, re, stat, shutil, tempfile
from pathlib import Path
from urllib.parse import unquote
from git import GitCommandError, Repo

# Kept outside the source tree: clones land in the reloader's watch path otherwise, and every
# cloned .py file restarts the server mid-request and empties the in-memory repository cache.
REPO_ROOT = Path(os.getenv("REPO_STORAGE") or Path(tempfile.gettempdir()) / "legacy-code-explainer-repos")
GITHUB_URL = re.compile(
    r"https?://github\.com/(?P<owner>[\w.-]+)/(?P<name>[\w.-]+?)(?:\.git)?"
    r"(?:/(?:tree|blob)/(?P<ref>[^/]+)(?:/(?P<subdir>.*?))?)?/?"
)

def validate_github_url(url: str) -> tuple[str, str, str | None, str]:
    match = GITHUB_URL.fullmatch(unquote(url.strip()))
    if not match: raise ValueError("Enter a public GitHub repository URL.")
    return match.group("owner"), match.group("name"), match.group("ref"), (match.group("subdir") or "").strip("/")

def _repo_id(owner: str, name: str, ref: str | None, subdir: str) -> str:
    digest = hashlib.sha1(f"{owner}/{name}@{ref or ''}/{subdir}".encode()).hexdigest()[:10]
    return f"{owner}_{name}_{digest}"

def _force_remove(path: Path):
    if not path.exists(): return
    # Git marks pack files read-only, which blocks rmtree on Windows.
    shutil.rmtree(path, onexc=lambda func, target, _: (os.chmod(target, stat.S_IWRITE), func(target)))

def _fetch(url: str, target: Path, ref: str | None, subdir: str):
    options = ["--depth=1"] + ([f"--branch={ref}"] if ref else [])
    if not subdir:
        # Closing releases the handles Windows would otherwise refuse to let us move.
        Repo.clone_from(url, target, multi_options=options).close()
        return
    # Only one folder is needed, so skip downloading blobs for the rest of the repository.
    with Repo.clone_from(url, target, multi_options=options + ["--filter=blob:none", "--no-checkout"]) as repo:
        repo.git.sparse_checkout("set", "--cone", subdir)
        repo.git.checkout()

def _checkout(repo_id: str, owner: str, name: str, ref: str | None, subdir: str) -> Path:
    target = REPO_ROOT / repo_id
    if target.exists(): return target
    REPO_ROOT.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/{owner}/{name}.git"
    # Clone aside and move into place so an interrupted download never poisons the cache.
    staging = Path(tempfile.mkdtemp(dir=REPO_ROOT, prefix=".partial-"))
    clone = staging / "repo"
    try:
        try: _fetch(url, clone, ref, subdir)
        except GitCommandError:
            if not ref: raise
            # A commit sha, or a branch whose name contains slashes, cannot be cloned via --branch.
            _force_remove(clone)
            _fetch(url, clone, None, subdir)
        clone.rename(target)
    finally:
        _force_remove(staging)
    return target

def clone_repo(url: str) -> tuple[str, Path]:
    owner, name, ref, subdir = validate_github_url(url)
    repo_id = _repo_id(owner, name, ref, subdir)
    base = _checkout(repo_id, owner, name, ref, subdir).resolve()
    root = (base / subdir).resolve() if subdir else base
    if root != base and base not in root.parents: raise ValueError("That folder is outside the repository.")
    if not root.is_dir(): raise ValueError(f"'{subdir}' is not a folder in {owner}/{name}.")
    return repo_id, root

def python_files(root: Path) -> dict[str, str]:
    ignored = {".git", ".venv", "venv", "__pycache__", "node_modules", "build", "dist"}
    result = {}
    for path in root.rglob("*.py"):
        if any(part in ignored for part in path.parts): continue
        try: result[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
    return result
