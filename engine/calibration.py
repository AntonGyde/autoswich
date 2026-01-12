import time
import logging

logger = logging.getLogger(__name__)

class CalibrationSession:
    def __init__(self, mic_id, duration=5.0):
        self.mic_id = mic_id
        self.duration = duration
        self.start_time = time.time()
        self.samples = []
        logger.info(f"Started calibration session for {mic_id}")
    
    def feed(self, level_db):
        """Feed audio level sample for calibration"""
        if not self.done():
            self.samples.append(level_db)
    
    def done(self):
        """Check if calibration session is complete"""
        return time.time() - self.start_time >= self.duration
    
    def result(self):
        """Calculate calibration results"""
        try:
            if not self.samples:
                logger.warning(f"No samples collected for {self.mic_id}")
                return {
                    "mic_id": self.mic_id,
                    "suggested_threshold": -45,
                    "suggested_weight": 1.0,
                    "samples": 0
                }
            
            # Calculate statistics
            avg_level = sum(self.samples) / len(self.samples)
            max_level = max(self.samples)
            
            # Suggest threshold 10dB below average
            suggested_threshold = avg_level - 10
            
            # Suggest weight based on signal strength
            # Stronger signals get lower weight to balance
            suggested_weight = 1.0
            if max_level > -30:
                suggested_weight = 0.8
            elif max_level < -50:
                suggested_weight = 1.2
            
            result = {
                "mic_id": self.mic_id,
                "suggested_threshold": round(suggested_threshold, 1),
                "suggested_weight": round(suggested_weight, 2),
                "avg_level": round(avg_level, 1),
                "max_level": round(max_level, 1),
                "samples": len(self.samples)
            }
            
            logger.info(f"Calibration complete for {self.mic_id}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error calculating calibration results: {e}")
            return {
                "mic_id": self.mic_id,
                "suggested_threshold": -45,
                "suggested_weight": 1.0,
                "error": str(e)
            }
