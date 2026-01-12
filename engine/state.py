import time
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SwitchState(str, Enum):
    WIDE = "WIDE"
    ACTIVE = "ACTIVE"
    STOPPED = "STOPPED"

class StateMachine:
    def __init__(self):
        self.state = SwitchState.WIDE
        self.state_start = time.time()
        logger.info("StateMachine initialized in WIDE state")
    
    def set(self, new_state):
        if new_state != self.state:
            logger.info(f"State transition: {self.state} -> {new_state}")
            self.state = new_state
            self.state_start = time.time()
    
    def duration(self):
        """Returns duration in current state in seconds"""
        return time.time() - self.state_start
