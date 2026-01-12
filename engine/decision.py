import time
import logging

logger = logging.getLogger(__name__)

class DecisionEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.wide_cfg = cfg.get("wide", {})
        self.last_wide = 0
        self.cooldown = self.wide_cfg.get("cooldown_s", 8)
        self.multi_speaker_count = self.wide_cfg.get("multi_speaker", {}).get("count", 2)
        self.silence_time = self.wide_cfg.get("silence", {}).get("time_s", 4)
        self.interval_every = self.wide_cfg.get("interval", {}).get("every_s", 30)
        self.last_interval_wide = 0
        logger.info(f"DecisionEngine initialized with cooldown={self.cooldown}s")
    
    def should_wide(self, active_mics, silence_duration):
        """
        Determine if we should switch to wide shot.
        Returns: (should_wide, reason)
        """
        try:
            current_time = time.time()
            
            # Check cooldown - don't switch to wide if we just did
            if current_time - self.last_wide < self.cooldown:
                return False, None
            
            # Multi-speaker detection
            if self.wide_cfg.get("multi_speaker", {}).get("enabled", False):
                if len(active_mics) >= self.multi_speaker_count:
                    self.last_wide = current_time
                    return True, "multi_speaker"
            
            # Silence detection
            if self.wide_cfg.get("silence", {}).get("enabled", False):
                if silence_duration >= self.silence_time:
                    self.last_wide = current_time
                    return True, "silence"
            
            # Interval-based wide shot
            if self.wide_cfg.get("interval", {}).get("enabled", False):
                if current_time - self.last_interval_wide >= self.interval_every:
                    self.last_wide = current_time
                    self.last_interval_wide = current_time
                    return True, "interval"
            
            return False, None
        except Exception as e:
            logger.error(f"Error in decision engine: {e}")
            return False, None
