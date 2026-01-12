from pythonosc import udp_client
import logging

logger = logging.getLogger(__name__)

class OSCClient:
    def __init__(self, host, port, osc_log):
        self.host = host
        self.port = port
        self.osc_log = osc_log
        
        try:
            self.client = udp_client.SimpleUDPClient(host, port)
            logger.info(f"OSC client initialized for {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to initialize OSC client: {e}")
            self.client = None
    
    def send(self, address, value):
        """Send OSC message"""
        try:
            if self.client:
                self.client.send_message(address, value)
                log_entry = {"address": address, "value": value}
                self.osc_log.append(log_entry)
                logger.debug(f"OSC sent: {address} = {value}")
        except Exception as e:
            logger.error(f"Failed to send OSC message to {address}: {e}")
    
    def cam(self, camera_id):
        """Switch to specific camera"""
        self.send("/camera", camera_id)
    
    def wide(self, reason):
        """Switch to wide shot"""
        self.send("/wide", reason)
