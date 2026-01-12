
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import json, threading, time, logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    with open("config.json") as f:
        cfg = json.load(f)
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load config.json: {e}", exc_info=True)
    raise

from engine.engine import AutoCutEngine

osc_log = []
try:
    engine = AutoCutEngine(cfg, osc_log)
    logger.info("Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize engine: {e}", exc_info=True)
    raise

latest = {}

app = FastAPI()

@app.get("/api/status")
def status():
    try:
        return latest
    except Exception as e:
        logger.error(f"Error in /api/status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calibrate/{mic_id}")
def calibrate(mic_id: str):
    try:
        logger.info(f"Calibration request for mic: {mic_id}")
        engine.start_calibration(mic_id)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error in /api/calibrate/{mic_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/apply/{mic_id}")
def apply(mic_id: str):
    try:
        logger.info(f"Apply calibration request for mic: {mic_id}")
        ok = engine.apply_calibration(mic_id)
        return {"applied": ok}
    except Exception as e:
        logger.error(f"Error in /api/apply/{mic_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def loop():
    global latest
    logger.info("Starting engine loop")
    while True:
        try:
            latest = engine.tick()
        except Exception as e:
            logger.error(f"Error in engine loop: {e}", exc_info=True)
            latest = {"error": str(e), "state": "ERROR"}
        time.sleep(0.05)

threading.Thread(target=loop, daemon=True).start()

app.mount("/", StaticFiles(directory="static", html=True), name="static")
