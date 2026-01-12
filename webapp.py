
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import json, threading, time
from engine.engine import AutoCutEngine

with open("config.json") as f:
    cfg = json.load(f)

osc_log = []
engine = AutoCutEngine(cfg, osc_log)
latest = {}

app = FastAPI()

@app.get("/api/status")
def status():
    return latest

@app.post("/api/calibrate/{mic_id}")
def calibrate(mic_id: str):
    engine.start_calibration(mic_id)
    return {"ok": True}

@app.post("/api/apply/{mic_id}")
def apply(mic_id: str):
    ok = engine.apply_calibration(mic_id)
    return {"applied": ok}

def loop():
    global latest
    while True:
        latest = engine.tick()
        time.sleep(0.05)

threading.Thread(target=loop, daemon=True).start()

app.mount("/", StaticFiles(directory="static", html=True), name="static")
