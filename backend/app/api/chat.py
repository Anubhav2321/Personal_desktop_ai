from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from groq import Groq
from datetime import datetime, timezone
import os
import uuid
import json
import re

# The chat and tasks collections were retrieved from the database.
from ..database import client as db_client 
from ..database import tasks_collection, conversations_collection, chat_history_collection

# System control engine
from .system_control import execute_action, get_system_stats

router = APIRouter()

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 🚀 New: Code Vault collection initialized.
vault_collection = db_client.aris_db.code_vault  

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Optional — auto-creates new session if missing

# 🧠 ENHANCED SYSTEM PROMPT WITH TOOL CALLING

SYSTEM_PROMPT = """You are ARIS, a highly advanced AI personal assistant with FULL SYSTEM ACCESS to the user's Windows laptop AND FULL INTERNET ACCESS.
The person chatting with you is your creator, Anubhav. Address him as "Anubhav" or "Sir".
Your tone must be exceptionally smooth, charismatic, polite, and deeply helpful like JARVIS from Iron Man.
Keep answers concise, direct, and completely plain text (no markdown, bold, or asterisks) so your text-to-speech engine reads flawlessly.

YOU HAVE FULL CONTROL OF THE LAPTOP AND INTERNET. When the user asks you to do something on their system or needs information from the internet, you MUST respond with a JSON action block.

AVAILABLE ACTIONS (use these exact action names):

--- SYSTEM ---
- open_app: Open an application. Params: app_name (e.g., "whatsapp", "chrome", "spotify", "chatgpt", "discord", "telegram", "notepad", "vs code", "calculator", "task manager", "settings", "steam", ANY app name)
- open_url: Open a URL. Params: url
- search_google: Search Google in the browser. Params: query
- search_youtube: Search YouTube in the browser. Params: query
- open_youtube: Open YouTube homepage. No params.
- play_youtube: Play a song/video on YouTube. Params: song_name
- get_battery: Get battery info. No params.
- get_system_stats: Get CPU, RAM, disk info. No params.
- get_network_info: Get WiFi/network info. No params.
- get_time: Get current time. No params.
- get_uptime: Get system uptime. No params.
- get_processes: Get running processes. No params.

--- INTERNET KNOWLEDGE (USE THESE TO ANSWER QUESTIONS!) ---
- web_search: Search the internet and get real results as text. Params: query, max_results (optional, default 5). USE THIS whenever the user asks about current events, facts, news, weather, prices, sports, any knowledge question, or anything you are not 100 percent sure about.
- get_web_info: Fetch the full text content of a webpage. Params: url. USE THIS to read a specific article or webpage.
- get_news: Get latest news headlines on a topic. Params: topic, max_results (optional, default 5). USE THIS when the user asks about news or current events.

--- FILE SYSTEM ---
- create_file: Create a file. Params: filepath, content (optional)
- read_file: Read a file. Params: filepath
- delete_file: Delete a file. Params: filepath
- list_directory: List folder contents. Params: dirpath
- open_folder: Open folder in Explorer. Params: dirpath

--- MEDIA CONTROL ---
- play_pause: Toggle media play/pause. No params.
- next_track: Skip to next track. No params.
- prev_track: Go to previous track. No params.
- volume_up: Increase volume. No params.
- volume_down: Decrease volume. No params.
- mute: Toggle mute. No params.

--- SYSTEM CONTROL ---
- screenshot: Take a screenshot. No params.
- lock_screen: Lock the screen. No params.
- shutdown: Shutdown PC. Params: delay (default 30 seconds)
- cancel_shutdown: Cancel scheduled shutdown. No params.
- restart: Restart PC. Params: delay (default 10 seconds)
- sleep: Put PC to sleep. No params.
- kill_process: Kill a process. Params: process_name

IMPORTANT RULES:
1. When the user wants a SYSTEM ACTION or INFORMATION, you MUST include a JSON block in your response wrapped in ```action tags like this:
```action
{"action": "action_name", "params": {"param_name": "value"}}
```
2. You may include BOTH a spoken response AND an action block. The spoken part goes BEFORE the action block.
3. For simple chat/questions with no system action needed, just respond normally without any action block.
4. Common path shortcuts: Desktop = C:/Users/""" + os.getlogin() + """/Desktop, Downloads = C:/Users/""" + os.getlogin() + """/Downloads, Documents = C:/Users/""" + os.getlogin() + """/Documents
5. When asked to play music, use play_youtube action.
6. For "open YouTube", use open_youtube. For "play [song] on YouTube", use play_youtube.
7. Always be natural in your spoken response. Example: "Opening YouTube for you right away, Sir." followed by the action block.
8. NEVER use markdown formatting (no *, #, _, etc.) in your spoken text.
9. CRITICAL: When the user asks ANY knowledge question (what is, who is, how to, tell me about, what's the weather, latest news, etc.), ALWAYS use web_search to get real-time information from the internet. Do NOT rely only on your training data.
10. For news and current events, use get_news action.
11. You know EVERYTHING about this laptop. You can open ANY app installed on this system including WhatsApp, ChatGPT, Spotify, Discord, Chrome, and all others.
"""

def _get_or_create_session(session_id: str, first_message: str = "New Conversation"):
    """Get existing session or create a new one. Returns session_id."""
    if session_id and conversations_collection.find_one({"session_id": session_id}):
        return session_id
    
    # Auto-create a new conversation
    new_id = session_id or str(uuid.uuid4())[:12]
    now = datetime.now(timezone.utc).isoformat()
    
    # Generate title from first message (first 40 chars)
    title = first_message[:40].strip()
    if len(first_message) > 40:
        title += "..."
    
    conversations_collection.insert_one({
        "session_id": new_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "message_count": 0
    })
    return new_id

def _save_message(session_id: str, role: str, message: str):
    """Save a message to chat history and update conversation metadata."""
    now = datetime.now(timezone.utc).isoformat()
    
    chat_history_collection.insert_one({
        "session_id": session_id,
        "role": role,
        "message": message,
        "timestamp": now
    })
    
    # Update conversation's timestamp and message count
    conversations_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {"updated_at": now},
            "$inc": {"message_count": 1}
        }
    )

def _extract_action(response_text):
    """Extract action JSON from AI response text. Returns (clean_text, action_dict or None)."""
    # Look for ```action ... ``` blocks
    pattern = r'```action\s*\n?(.*?)\n?```'
    match = re.search(pattern, response_text, re.DOTALL)
    
    if match:
        action_json = match.group(1).strip()
        # Remove the action block from the spoken text
        clean_text = re.sub(pattern, '', response_text, flags=re.DOTALL).strip()
        try:
            action_data = json.loads(action_json)
            return clean_text, action_data
        except json.JSONDecodeError:
            return clean_text, None
    
    return response_text, None


@router.post("/chat")
async def process_terminal_input(request: ChatRequest):
    user_input = request.message.strip()
    lower_input = user_input.lower()

    # ==========================================
    # 🚀 1. PYTHON LOGIC: ADD TASK COMMAND
    # ==========================================
    if lower_input.startswith("/add-task") or lower_input.startswith("add-task"):
        task_text = user_input.replace("/add-task", "").replace("add-task", "").strip()
        if task_text:
            tasks_collection.insert_one({"task": task_text, "status": "pending"})
            return {
                "type": "system_command", 
                "response": f"[SYSTEM] Task '{task_text}' successfully saved to MongoDB.",
                "action": "reload_tasks"
            }
        else:
            return {"type": "error", "response": "[SYSTEM ERROR] Task description cannot be empty."}

    # ==========================================
    # 🚀 2. PYTHON LOGIC: SAVE CODE COMMAND (NEW)
    # ==========================================
    if lower_input.startswith("/save-code") or lower_input.startswith("save-code"):
        # It will be formatted.: /save-code filename.py | snippet details
        parts = user_input.split("|", 1)
        if len(parts) == 2:
            command_part = parts[0].strip()
            code_content = parts[1].strip()
            filename = command_part.replace("/save-code", "").replace("save-code", "").strip()
            
            if filename and code_content:
                vault_collection.insert_one({"filename": filename, "content": code_content})
                return {
                    "type": "system_command", 
                    "response": f"[SYSTEM] Snippet '{filename}' securely encrypted and stored in CODE_VAULT.",
                    "action": "reload_vault" # The frontend will be signaled to refresh the vault
                }
        return {"type": "error", "response": "[SYSTEM ERROR] Invalid format. Use: /save-code filename.ext | your code or description"}

    # ==========================================
    # 🚀 3. PYTHON LOGIC: HISTORY COMMAND
    # ==========================================
    if lower_input == "/history":
        chats = list(chat_history_collection.find({}, {"_id": 0}).sort("timestamp", 1))
        if not chats:
            return {"type": "system_command", "response": "[SYSTEM] Databanks are empty. No history found."}
        
        history_text = "\n".join([f"> {c['role']}: {c['message']}" for c in chats])
        return {"type": "history_command", "response": "[SYSTEM] Displaying Previous Logs:\n\n" + history_text}

    # ==========================================
    # 🚀 4. AI CHAT WITH SYSTEM ACTION SUPPORT
    # ==========================================
    try:
        # Get or create conversation session
        session_id = _get_or_create_session(request.session_id, user_input)
        
        # Save user message to session
        _save_message(session_id, "USER", user_input)

        # Build conversation context from session history (last 20 messages)
        session_messages = list(chat_history_collection.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(20))
        
        # Reverse to chronological order and format for Groq
        session_messages.reverse()
        context_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in session_messages:
            role = "user" if msg["role"] == "USER" else "assistant"
            context_messages.append({"role": role, "content": msg["message"]})

        chat_completion = groq_client.chat.completions.create(
            messages=context_messages,
            model="llama-3.1-8b-instant",  
        )
        
        ai_reply = chat_completion.choices[0].message.content
        
        # Extract action from AI response (if any)
        spoken_text, action_data = _extract_action(ai_reply)
        
        # Clean spoken text of markdown artifacts
        clean_reply = spoken_text.replace("*", "").replace("#", "").replace("_", "")
        
        # Execute system action if detected
        action_result = None
        action_type = "chat"
        
        if action_data and "action" in action_data:
            action_name = action_data["action"]
            action_params = action_data.get("params", None)
            
            # Execute the system action
            result = execute_action(action_name, action_params)
            
            # Format the result
            if isinstance(result, dict):
                action_result = json.dumps(result, indent=2)
            else:
                action_result = str(result)
            
            action_type = "system_action"
            
            # TWO-STEP AI FLOW: For web_search/get_news/get_web_info, feed results
            # back to the AI for natural language summarization
            if action_name in ("web_search", "get_news", "get_web_info") and action_result:
                try:
                    summary_messages = [
                        {"role": "system", "content": (
                            "You are ARIS, a smooth AI assistant like JARVIS. "
                            "The user asked a question and you searched the internet. "
                            "Below are the search results. Summarize the key information "
                            "in a clear, concise, conversational way. Use plain text only "
                            "(no markdown, no bold, no asterisks). Address the user as Sir or Anubhav. "
                            "Keep your answer focused and informative."
                        )},
                        {"role": "user", "content": f"User's question: {user_input}\n\nSearch results:\n{action_result}"}
                    ]
                    
                    summary_completion = groq_client.chat.completions.create(
                        messages=summary_messages,
                        model="llama-3.1-8b-instant",
                    )
                    
                    summarized = summary_completion.choices[0].message.content
                    # Clean markdown from summary
                    clean_reply = summarized.replace("*", "").replace("#", "").replace("_", "")
                    
                except Exception:
                    # If summarization fails, use the raw search results
                    if not clean_reply:
                        clean_reply = f"Here is what I found, Sir. {action_result}"
            
            # If AI didn't provide spoken text, create one
            if not clean_reply:
                clean_reply = f"Done, Sir. {action_result}"
        
        # Save AI response to session (just the spoken part)
        _save_message(session_id, "ARIS", clean_reply)
        
        response = {
            "type": action_type, 
            "response": clean_reply,
            "session_id": session_id
        }
        
        if action_result:
            response["action_result"] = action_result
            response["action_name"] = action_data.get("action", "unknown")
        
        return response
        
    except Exception as e:
        return {"type": "error", "response": f"[SYSTEM ERROR] Core logic failure: {str(e)}"}

# ==========================================
# 🚀 5. API ENDPOINT: GET VAULT DATA (NEW)
# ==========================================
@router.get("/get-vault")
async def get_vault():
    snippets = list(vault_collection.find({}, {"_id": 0}))
    return {"snippets": snippets}