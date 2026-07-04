from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from ..database import conversations_collection, chat_history_collection

router = APIRouter()

class ConversationCreate(BaseModel):
    title: str = "New Conversation"

# ==========================================
# 🚀 CREATE A NEW CONVERSATION SESSION
# ==========================================
@router.post("/conversations")
async def create_conversation(request: ConversationCreate = None):
    if conversations_collection is None:
        return {"status": "error", "message": "Database not available."}
    
    session_id = str(uuid.uuid4())[:12]  # Short unique ID
    now = datetime.now(timezone.utc).isoformat()
    
    conversation = {
        "session_id": session_id,
        "title": request.title if request else "New Conversation",
        "created_at": now,
        "updated_at": now,
        "message_count": 0
    }
    conversations_collection.insert_one(conversation)
    
    return {
        "status": "success",
        "session_id": session_id,
        "title": conversation["title"],
        "created_at": now
    }

# ==========================================
# 🚀 LIST ALL CONVERSATIONS (Most Recent First)
# ==========================================
@router.get("/conversations")
async def list_conversations():
    if conversations_collection is None:
        return {"conversations": []}
    
    convos = list(conversations_collection.find(
        {}, 
        {"_id": 0}
    ).sort("updated_at", -1))
    
    return {"conversations": convos}

# ==========================================
# 🚀 GET MESSAGES FOR A SPECIFIC CONVERSATION
# ==========================================
@router.get("/conversations/{session_id}")
async def get_conversation_messages(session_id: str):
    if chat_history_collection is None:
        return {"messages": [], "session_id": session_id}
    
    messages = list(chat_history_collection.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1))
    
    # Also get conversation metadata
    convo = conversations_collection.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    return {
        "session_id": session_id,
        "title": convo["title"] if convo else "Unknown",
        "messages": messages
    }

# ==========================================
# 🚀 DELETE A CONVERSATION AND ITS MESSAGES
# ==========================================
@router.delete("/conversations/{session_id}")
async def delete_conversation(session_id: str):
    if conversations_collection is None:
        return {"status": "error", "message": "Database not available."}
    
    # Delete all messages belonging to this conversation
    chat_history_collection.delete_many({"session_id": session_id})
    # Delete the conversation metadata
    conversations_collection.delete_one({"session_id": session_id})
    
    return {"status": "success", "message": f"Conversation {session_id} purged from databanks."}
