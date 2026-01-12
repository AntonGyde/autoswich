
import time, json
from engine.audio import AudioInput
from engine.mics import MicManager
from engine.state import StateMachine, SwitchState
from engine.decision import DecisionEngine
from engine.osc import OSCClient
from engine.calibration import CalibrationSession

class AutoCutEngine:
    def __init__(self, cfg, osc_log):
        self.cfg = cfg
        self.osc_log = osc_log
        self._init()

    def _init(self):
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

    def reload(self):
        self._init()

    def start_calibration(self, mic_id):
        self.automix = False
        self.state.set(SwitchState.STOPPED)
        self.calibration_sessions[mic_id] = CalibrationSession(mic_id)

    def apply_calibration(self, mic_id):
        if mic_id not in self.calibration_results:
            return False

        res = self.calibration_results[mic_id]
        for mic in self.cfg["mics"]:
            if mic["id"] == mic_id:
                mic["threshold_db"] = res["suggested_threshold"]
                mic["weight"] = res["suggested_weight"]

        with open("config.json", "w") as f:
            json.dump(self.cfg, f, indent=2)

        self.reload()
        return True

    def tick(self):
        levels, last_audio = self.audio.get()

        if time.time() - last_audio > 0.5:
            if not self.audio_fail:
                self.audio_fail = True
                self.state.set(SwitchState.WIDE)
                self.osc.wide("audio_fail")
            return {"state": self.state.state, "audio_fail": True}

        self.audio_fail = False

        for mic_id, session in list(self.calibration_sessions.items()):
            ch = next(m["input_channel"] for m in self.cfg["mics"] if m["id"] == mic_id)
            session.feed(levels.get(ch, -100))
            if session.done():
                self.calibration_results[mic_id] = session.result()
                del self.calibration_sessions[mic_id]

        if not self.automix:
            return {
                "levels": levels,
                "state": self.state.state,
                "calibration": self.calibration_results
            }

        active, dominant, scores, dominance = self.mics.evaluate(levels)
        if active:
            self.last_sound = time.time()

        silence = time.time() - self.last_sound
        wide, reason = self.decision.should_wide(active, silence)

        if self.state.state == SwitchState.WIDE:
            if self.state.duration() >= self.cfg["wide"].get("min_duration_s", 3):
                if dominant:
                    self.state.set(SwitchState.ACTIVE)
                    cam = next(m["camera"] for m in self.cfg["mics"] if m["id"] == dominant)
                    self.osc.cam(cam)
        elif wide:
            self.state.set(SwitchState.WIDE)
            self.osc.wide(reason)
        elif dominant:
            self.state.set(SwitchState.ACTIVE)
            cam = next(m["camera"] for m in self.cfg["mics"] if m["id"] == dominant)
            self.osc.cam(cam)

        return {
            "levels": levels,
            "state": self.state.state,
            "dominance": dominance,
            "calibration": self.calibration_results
        }
