import os
from .cache_service import get_cached, set_cached
from prompts.templates import EXPLAIN_TEMPLATE, RISK_TEMPLATE, ONBOARDING_TEMPLATE, README_TEMPLATE, QA_TEMPLATE

def _chat(repo_id: str, feature: str, identifier: str, prompt: str) -> str | None:
    cached=get_cached(repo_id,feature,identifier)
    if cached: return cached
    if not os.getenv("COHERE_API_KEY"): return None
    try:
        import cohere
        response=cohere.ClientV2(os.environ["COHERE_API_KEY"]).chat(model="command-r-plus", messages=[{"role":"user","content":prompt}])
        text=response.message.content[0].text
        return set_cached(repo_id,feature,identifier,text)
    except Exception: return None

def explain(repo_id, path, code, info):
    prompt=EXPLAIN_TEMPLATE.format(file_path=path, imports=", ".join(info["imports"]) or "None", called_by=", ".join(info["called_by"]) or "None", code=limit(code))
    answer=_chat(repo_id,"explain",path,prompt)
    funcs=[{"name":n,"summary":f"Function defined in {path}."} for n in info["functions"]]
    return answer or f"`{path}` contains {info['loc']} lines and {len(info['functions'])} defined function(s). It imports {', '.join(info['imports']) or 'no modules tracked by the parser'}.", funcs

def risk(repo_id,path,function,dependents):
    prompt=RISK_TEMPLATE.format(function_name=function,file_path=path,dependents="\n".join(dependents) or "No direct dependents were detected.")
    return _chat(repo_id,"risk",f"{path}:{function}",prompt) or (f"No direct dependents were detected for `{function}`." if not dependents else f"Changing `{function}` may affect {', '.join(dependents[:5])}. Check behavior and call signatures before merging.")

def onboarding(repo_id, depmap):
    entries=sorted(depmap, key=lambda p:(len(depmap[p]["called_by"]), -depmap[p]["loc"]))[:8]
    context="\n".join(f"{p}: imports {d['imports']}; called by {d['called_by']}" for p,d in ((p,depmap[p]) for p in entries))
    answer=_chat(repo_id,"onboarding","path",ONBOARDING_TEMPLATE.format(entry_points_with_context=context))
    if answer: return [{"file":"Suggested reading path", "reason":answer}]
    return [{"file":p,"reason":"Start here because it is a likely entry point with few inbound dependencies." if not depmap[p]["called_by"] else "Read next to understand a module used elsewhere."} for p in entries]

def readme(repo_id, depmap):
    entries=", ".join(list(depmap)[:8]); summaries="\n".join(f"- {p}: {d['loc']} lines, functions: {', '.join(d['functions']) or 'none'}" for p,d in list(depmap.items())[:20])
    answer=_chat(repo_id,"readme","repo",README_TEMPLATE.format(entry_points=entries,file_summaries=summaries))
    return answer or f"# Codebase README\n\n## Overview\nThis Python project contains {len(depmap)} parsed modules.\n\n## How it's structured\n{summaries}\n\n## Getting started\nCreate a virtual environment, install the repository's dependencies, and review the entry-point modules first."

def qa(repo_id, question, chunks):
    context="\n\n".join(f"FILE: {c['file_path']}\n{limit(c['text'], 1800)}" for c in chunks)
    answer=_chat(repo_id,"ask",question,QA_TEMPLATE.format(question=question,retrieved_chunks=context))
    return answer or "I found the most relevant code below. Configure COHERE_API_KEY for a generated natural-language answer.\n\n" + context[:3500]

def limit(text, cap=24000):
    return text if len(text)<=cap else text[:cap]+"\n\n[Truncated: file exceeds the analysis limit.]"
