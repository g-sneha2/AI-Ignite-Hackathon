EXPLAIN_TEMPLATE = '''You are explaining code to a new engineer joining this team.

File: {file_path}
Imports: {imports}
Called by: {called_by}

Code:
{code}

Explain in plain English:
1. What this file/module does (2-3 sentences)
2. The purpose of each major function or class (1 sentence each)
3. Anything that looks fragile, unusual, or worth flagging to a newcomer

Keep it concise and skip restating the code line-by-line.'''

RISK_TEMPLATE = '''A developer wants to modify the function `{function_name}` in `{file_path}`.

The following files/functions currently depend on it:
{dependents}

Write a short (2-4 sentence) warning about what could break if this function's behavior or signature changes, for a developer who has never seen this codebase before.'''

ONBOARDING_TEMPLATE = '''Here are the likely entry points into this codebase, with their imports and what calls them:
{entry_points_with_context}

Suggest a logical order (5-8 files max) for a new engineer to read through this codebase to build understanding fastest. For each file, give a 1-sentence reason why it's next.'''

README_TEMPLATE = '''Based on the following codebase structure and file summaries, draft a README.md for this project:

Entry points: {entry_points}
File summaries: {file_summaries}

Include: a project title guess, a short overview, a "how it's structured" section, and a "getting started" section. Output valid Markdown.'''

QA_TEMPLATE = '''Answer the following question about this codebase using only the context provided.

Question: {question}

Relevant code context:
{retrieved_chunks}

Give a direct, specific answer. If the context doesn't fully answer the question, say what's missing.'''
