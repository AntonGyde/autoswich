import logging

logger = logging.getLogger(__name__)

class MicManager:
    def __init__(self, mic_configs):
        self.mics = mic_configs
        logger.info(f"Initialized MicManager with {len(mic_configs)} microphones")
    
    def evaluate(self, levels):
        """
        Evaluate microphone levels and determine which is dominant.
        Returns: (any_active, dominant, scores, dominance_score)
            - any_active: Boolean indicating if any microphone is active
            - dominant: ID of the dominant microphone (or None if no dominant mic)
            - scores: Dictionary mapping mic IDs to their scores
            - dominance_score: Score value of the dominant microphone
        """
        try:
            scores = {}
            active_mics = []
            
            for mic in self.mics:
                if not mic.get("enabled", True):
                    continue
                
                ch = mic["input_channel"]
                level = levels.get(ch, -100)
                threshold = mic["threshold_db"]
                weight = mic.get("weight", 1.0)
                
                if level > threshold:
                    active_mics.append(mic["id"])
                    # Score is level above threshold, weighted
                    scores[mic["id"]] = (level - threshold) * weight
                else:
                    scores[mic["id"]] = 0
            
            any_active = len(active_mics) > 0
            
            # Find dominant mic (highest score)
            dominant = None
            dominance = 0
            if scores:
                dominant = max(scores, key=scores.get)
                dominance = scores[dominant]
                if dominance <= 0:
                    dominant = None
            
            return any_active, dominant, scores, dominance
        except Exception as e:
            logger.error(f"Error evaluating microphones: {e}")
            return False, None, {}, 0
