# Legacy Code Explorer

An end-to-end FastAPI + React application for exploring public Python GitHub repositories. It parses dependencies, scores modification risk, creates onboarding paths, drafts READMEs, and answers repository questions with Cohere-backed RAG.

## Run locally

1. In `backend`, copy the provided environment-variable names into a `.env` file, then run `pip install -r requirements.txt` and `uvicorn main:app --reload`.
2. In `frontend`, run `npm install` then `npm run dev`.
3. Open `http://localhost:5173` and paste a public GitHub repository URL.

You can paste either a repository root (`https://github.com/owner/repo`) or a single folder inside one (`https://github.com/owner/repo/tree/main/some/folder`). A folder URL scopes the analysis to that folder and downloads only its files, which matters for large monorepos.

`COHERE_API_KEY` enables Command R+ responses and Embed v4 indexing. The app provides deterministic local fallback summaries and retrieval if it is absent.

Clones are cached in the system temp directory; set `REPO_STORAGE` to relocate them. Keep that path outside `backend`, since `uvicorn --reload` restarts on any `.py` file appearing under it and that clears the in-memory repository cache.
