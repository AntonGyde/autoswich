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
    
    def set(self, new_state, current_time=None):
        """Set the state machine to a new state.
        Args:
            new_state: The new state to transition to
            current_time: Optional current timestamp (uses time.time() if not provided)
        """
        if new_state != self.state:
            logger.info(f"State transition: {self.state} -> {new_state}")
            self.state = new_state
            self.state_start = current_time if current_time is not None else time.time()
    
    def duration(self, current_time=None):
        """Returns duration in current state in seconds.
        Args:
            current_time: Optional current timestamp (uses time.time() if not provided)
        """
        return (current_time if current_time is not None else time.time()) - self.state_start
