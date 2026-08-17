import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import LoadRepoRequest, FileRequest, RiskRequest, AskRequest
from services.repo_service import clone_repo, python_files
from services.parser_service import parse_files, build_tree, graph_for
from services.risk_score_service import score_file
from services.embedding_service import build_index, search
from services.cache_service import get_repo, set_repo
from services import ai_service

load_dotenv()
app=FastAPI(title="Legacy Code Explainer")
app.add_middleware(CORSMiddleware, allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?", allow_methods=["*"], allow_headers=["*"])

def repo_or_404(repo_id):
    repo=get_repo(repo_id)
    if not repo: raise HTTPException(404,"Repository not found. Load it again.")
    return repo

@app.post("/api/load-repo")
def load_repo(request: LoadRepoRequest):
    try:
        repo_id, root=clone_repo(request.repo_url)
        existing=get_repo(repo_id)
        if existing: return {"repo_id":repo_id,"file_tree":existing["file_tree"],"has_readme":existing["has_readme"]}
        files=python_files(root)
        if not files: raise HTTPException(422,"No Python files found in this repository.")
        dependency_map=parse_files(files); scores={p:score_file(d) for p,d in dependency_map.items()}
        record={"files":files,"dependency_map":dependency_map,"scores":scores,"file_tree":build_tree(list(dependency_map),scores),"has_readme":(root/"README.md").exists() or (root/"readme.md").exists()}
        set_repo(repo_id,record); build_index(repo_id,{p:files[p] for p in dependency_map})
        return {"repo_id":repo_id,"file_tree":record["file_tree"],"has_readme":record["has_readme"]}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400,f"Could not load repository: {exc}")

@app.post("/api/explain-file")
def explain_file(request: FileRequest):
    repo=repo_or_404(request.repo_id); info=repo["dependency_map"].get(request.file_path)
    if not info: raise HTTPException(404,"Python file not found.")
    explanation,functions=ai_service.explain(request.repo_id,request.file_path,repo["files"][request.file_path],info)
    return {"explanation":explanation,"functions":functions,"imports":info["imports"],"called_by":info["called_by"]}

@app.post("/api/dependency-graph")
def dependency_graph(request: FileRequest):
    repo=repo_or_404(request.repo_id)
    if request.file_path not in repo["dependency_map"]: raise HTTPException(404,"Python file not found.")
    return {"mermaid_syntax":graph_for(request.file_path,repo["dependency_map"])}

@app.post("/api/risk-check")
def risk_check(request: RiskRequest):
    repo=repo_or_404(request.repo_id); info=repo["dependency_map"].get(request.file_path)
    if not info or request.function_name not in info["functions"]: raise HTTPException(404,"Function not found.")
    dependents=[x for x in info["called_by"] if x.endswith(":"+request.function_name)]
    return {"dependents":dependents,"warning":ai_service.risk(request.repo_id,request.file_path,request.function_name,dependents)}

@app.post("/api/onboarding-path")
def onboarding_path(request: dict): return {"path":ai_service.onboarding(request["repo_id"],repo_or_404(request["repo_id"])["dependency_map"])}
@app.post("/api/generate-readme")
def generate_readme(request: dict): return {"readme_markdown":ai_service.readme(request["repo_id"],repo_or_404(request["repo_id"])["dependency_map"])}
@app.post("/api/ask")
def ask(request: AskRequest):
    repo_or_404(request.repo_id); chunks=search(__import__('services.embedding_service',fromlist=['build_index']).build_index(request.repo_id, get_repo(request.repo_id)["files"]),request.question)
    return {"answer":ai_service.qa(request.repo_id,request.question,chunks),"sources":list(dict.fromkeys(c["file_path"] for c in chunks))}
