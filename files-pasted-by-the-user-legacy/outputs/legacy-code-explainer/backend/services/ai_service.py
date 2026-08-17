import os
import sys
from .cache_service import get_cached, set_cached
from prompts.templates import EXPLAIN_TEMPLATE, RISK_TEMPLATE, ONBOARDING_TEMPLATE, README_TEMPLATE, QA_TEMPLATE

def _chat(repo_id: str, feature: str, identifier: str, prompt: str) -> str | None:
    cached=get_cached(repo_id,feature,identifier)
    if cached: return cached
    
    api_key=os.getenv("COHERE_API_KEY")
    if not api_key:
        print("ERROR: COHERE_API_KEY environment variable not set!", file=sys.stderr)
        print(f"Current env vars: {list(os.environ.keys())}", file=sys.stderr)
        return None
    
    print(f"DEBUG: Attempting Cohere API call for feature={feature}, identifier={identifier}", file=sys.stderr)
    print(f"DEBUG: API key present: {bool(api_key)}, key length: {len(api_key) if api_key else 0}", file=sys.stderr)
    
    try:
        import cohere
        client=cohere.ClientV2(api_key)
        
        # Try models in order
        models_to_try=["command-r-plus-08-2024", "command-r-plus-04-2024", "command-r-plus", "command-r"]
        response=None
        last_error=None
        
        for model in models_to_try:
            try:
                print(f"DEBUG: Trying model: {model}", file=sys.stderr)
                response=client.chat(
                    model=model,
                    messages=[{"role":"user","content":prompt}]
                )
                print(f"DEBUG: Model {model} succeeded!", file=sys.stderr)
                break
            except Exception as e:
                print(f"DEBUG: Model {model} failed: {type(e).__name__}: {e}", file=sys.stderr)
                last_error=e
                continue
        
        if not response:
            print(f"ERROR: All models failed. Last error: {last_error}", file=sys.stderr)
            return None
        
        # Debug response structure
        print(f"DEBUG: Response type: {type(response)}", file=sys.stderr)
        print(f"DEBUG: Response attributes: {dir(response)}", file=sys.stderr)
        
        # Parse response
        text=None
        if hasattr(response, 'message'):
            print(f"DEBUG: Has message attribute", file=sys.stderr)
            msg=response.message
            print(f"DEBUG: Message type: {type(msg)}, content: {msg}", file=sys.stderr)
            
            if hasattr(msg, 'content'):
                content=msg.content
                print(f"DEBUG: Content type: {type(content)}", file=sys.stderr)
                
                if isinstance(content, list):
                    if content:
                        first_item=content[0]
                        print(f"DEBUG: First item type: {type(first_item)}", file=sys.stderr)
                        if hasattr(first_item, 'text'):
                            text=first_item.text
                        else:
                            text=str(first_item)
                elif isinstance(content, str):
                    text=content
                else:
                    text=str(content)
        
        if text and text.strip():
            print(f"DEBUG: Successfully extracted text, length: {len(text)}", file=sys.stderr)
            return set_cached(repo_id,feature,identifier,text)
        else:
            print(f"ERROR: Could not extract text from response", file=sys.stderr)
            return None
            
    except Exception as e:
        print(f"ERROR: Exception in _chat: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None

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
