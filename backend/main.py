from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import requests
import sqlite3
import json
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== DATABASE =====
conn = sqlite3.connect("app.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    timestamp REAL
)
""")

conn.commit()

# ===== AI (FREE HUGGINGFACE) =====
HF_API = "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english"

def analyze_sentiment(text):
    try:
        res = requests.post(HF_API, json={"inputs": text})
        return res.json()
    except:
        return {"label": "NEUTRAL"}

# ===== CHAT WEBSOCKET =====
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        data = await websocket.receive_text()

        sentiment = analyze_sentiment(data)

        cursor.execute("INSERT INTO messages (content, timestamp) VALUES (?, ?)", (data, time.time()))
        conn.commit()

        response = {
            "message": data,
            "sentiment": sentiment
        }

        await websocket.send_text(json.dumps(response))