
import time, json, logging
from engine.audio import AudioInput
from engine.mics import MicManager
from engine.state import StateMachine, SwitchState
from engine.decision import DecisionEngine
from engine.osc import OSCClient
from engine.calibration import CalibrationSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoCutEngine:
    def __init__(self, cfg, osc_log):
        self.cfg = cfg
        self.osc_log = osc_log
        logger.info("Initializing AutoCutEngine")
        self._init()

    def _init(self):
        try:
            self.audio = AudioInput(self.cfg.get("audio_device"), self.cfg["audio_channels"])
            self.mics = MicManager(self.cfg["mics"])
            self.state = StateMachine()
            self.decision = DecisionEngine(self.cfg)
            self.osc = OSCClient(self.cfg["osc"]["host"], self.cfg["osc"]["port"], self.osc_log)
            self.automix = self.cfg["automix"]["enabled"]
            self.last_sound = time.time()
            self.audio_fail = False
            self.calibration_sessions = {}
            self.calibration_results = {}
            logger.info("AutoCutEngine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AutoCutEngine: {e}", exc_info=True)
            raise

    def reload(self):
        try:
            logger.info("Reloading engine configuration")
            self._init()
        except Exception as e:
            logger.error(f"Failed to reload engine: {e}", exc_info=True)
            raise

    def start_calibration(self, mic_id):
        try:
            logger.info(f"Starting calibration for mic: {mic_id}")
            self.automix = False
            self.state.set(SwitchState.STOPPED)
            self.calibration_sessions[mic_id] = CalibrationSession(mic_id)
        except Exception as e:
            logger.error(f"Failed to start calibration for {mic_id}: {e}", exc_info=True)

    def apply_calibration(self, mic_id):
        try:
            if mic_id not in self.calibration_results:
                logger.warning(f"No calibration results found for {mic_id}")
                return False

            res = self.calibration_results[mic_id]
            logger.info(f"Applying calibration for {mic_id}: {res}")
            
            for mic in self.cfg["mics"]:
                if mic["id"] == mic_id:
                    mic["threshold_db"] = res["suggested_threshold"]
                    mic["weight"] = res["suggested_weight"]

            with open("config.json", "w") as f:
                json.dump(self.cfg, f, indent=2)

            self.reload()
            logger.info(f"Calibration applied successfully for {mic_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply calibration for {mic_id}: {e}", exc_info=True)
            return False

    def tick(self):
        try:
            current_time = time.time()  # Single time.time() call per tick
            levels, last_audio = self.audio.get()

            # Check for audio failure
            if current_time - last_audio > 0.5:
                if not self.audio_fail:
                    self.audio_fail = True
                    self.state.set(SwitchState.WIDE, current_time)
                    self.osc.wide("audio_fail")
                    logger.warning("Audio failure detected")
                return {"state": self.state.state, "audio_fail": True}

            self.audio_fail = False

            # Process calibration sessions
            for mic_id, session in list(self.calibration_sessions.items()):
                try:
                    ch = next(m["input_channel"] for m in self.cfg["mics"] if m["id"] == mic_id)
                    session.feed(levels.get(ch, -100))
                    if session.done():
                        self.calibration_results[mic_id] = session.result()
                        del self.calibration_sessions[mic_id]
                except Exception as e:
                    logger.error(f"Error processing calibration for {mic_id}: {e}")

            if not self.automix:
                return {
                    "levels": levels,
                    "state": self.state.state,
                    "calibration": self.calibration_results
                }

            active, dominant, scores, dominance = self.mics.evaluate(levels)
            if active:
                self.last_sound = current_time  # Use cached time

            silence = current_time - self.last_sound  # Use cached time
            wide, reason = self.decision.should_wide(active, silence)

            if self.state.state == SwitchState.WIDE:
                if self.state.duration(current_time) >= self.cfg["wide"].get("min_duration_s", 3):
                    if dominant:
                        self.state.set(SwitchState.ACTIVE, current_time)
                        cam = next(m["camera"] for m in self.cfg["mics"] if m["id"] == dominant)
                        self.osc.cam(cam)
            elif wide:
                self.state.set(SwitchState.WIDE, current_time)
                self.osc.wide(reason)
            elif dominant:
                self.state.set(SwitchState.ACTIVE, current_time)
                cam = next(m["camera"] for m in self.cfg["mics"] if m["id"] == dominant)
                self.osc.cam(cam)

            return {
                "levels": levels,
                "state": self.state.state,
                "dominance": dominance,
                "calibration": self.calibration_results
            }
        except Exception as e:
            logger.error(f"Error in tick(): {e}", exc_info=True)
            return {
                "state": self.state.state if hasattr(self, 'state') else "ERROR",
                "error": str(e)
            }
