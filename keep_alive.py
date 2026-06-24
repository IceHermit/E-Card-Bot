from fastapi import FastAPI
import uvicorn
import threading
import os

app = FastAPI()

@app.get("/")
def home():
    return "Successfully Pinged!"

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

def keep_running():
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()