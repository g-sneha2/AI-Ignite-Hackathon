from pydantic import BaseModel, HttpUrl

class LoadRepoRequest(BaseModel):
    repo_url: str
class FileRequest(BaseModel):
    repo_id: str
    file_path: str
class RiskRequest(FileRequest):
    function_name: str
class AskRequest(BaseModel):
    repo_id: str
    question: str
