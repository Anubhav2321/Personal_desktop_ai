from fastapi import APIRouter
from pydantic import BaseModel
from ..database import vault_collection

router = APIRouter()

class SnippetRequest(BaseModel):
    title: str
    code: str
    language: str = "python"

@router.post("/add-snippet")
async def add_snippet(request: SnippetRequest):
    if vault_collection is None:
        return {"status": "error", "message": "Database not available."}
    new_snippet = {
        "title": request.title,
        "code": request.code,
        "language": request.language
    }
    vault_collection.insert_one(new_snippet)
    return {"status": "success", "message": "Snippet saved to Code Vault."}

@router.get("/get-snippets")
async def get_snippets():
    if vault_collection is None:
        return {"snippets": []}
    snippets = list(vault_collection.find({}, {"_id": 0}))
    return {"snippets": snippets}
