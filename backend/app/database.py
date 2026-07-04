from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

# MongoDB Connection URL (Localhost by default)
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

# Initialize with None so app can still start without MongoDB
client = None
db = None
tasks_collection = None
vault_collection = None
conversations_collection = None
chat_history_collection = None

try:
    # Initialize the MongoDB Client with a short timeout
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    # Test the connection
    client.admin.command('ping')

    # Create or connect to a database named 'aris_db'
    db = client.aris_db

    # Define Collections (Like tables in SQL)
    tasks_collection = db.tasks
    vault_collection = db.code_vault
    conversations_collection = db.conversations      # Chat session metadata
    chat_history_collection = db.chat_history         # Individual messages per session

    print("[SYSTEM] Successfully connected to ARIS Database.")
except Exception as e:
    print(f"[SYSTEM WARNING] Database connection failed: {e}")
    print("[SYSTEM] Running in degraded mode — database features disabled.")