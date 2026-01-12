import sounddevice as sd
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

class AudioInput:
    def __init__(self, device, channels):
        self.device = device
        self.channels = channels
        self.levels = {}
        self.last_update = time.time()
        self.stream = None
        
        try:
            if device is None:
                # Try to get default input device
                device_info = sd.query_devices(kind='input')
                logger.info(f"Using default audio device: {device_info['name']}")
            else:
                device_info = sd.query_devices(device)
                logger.info(f"Using audio device: {device_info['name']}")
            
            self.stream = sd.InputStream(
                device=device,
                channels=channels,
                callback=self._callback,
                samplerate=48000,
                blocksize=2400
            )
            self.stream.start()
            logger.info(f"Audio stream started with {channels} channels")
        except Exception as e:
            logger.error(f"Failed to initialize audio device: {e}")
            logger.warning("Running without audio input - levels will be simulated")
            self.stream = None
    
    def _callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        try:
            # Calculate RMS level for each channel in dB
            for ch in range(self.channels):
                if ch < indata.shape[1]:
                    rms = np.sqrt(np.mean(indata[:, ch]**2))
                    if rms > 0:
                        db = 20 * np.log10(rms)
                    else:
                        db = -100
                    self.levels[ch + 1] = db  # 1-indexed channels
            
            self.last_update = time.time()
        except Exception as e:
            logger.error(f"Error in audio callback: {e}")
    
    def get(self):
        """Returns (levels_dict, last_audio_timestamp)"""
        if self.stream is None:
            # Simulate no audio
            return ({}, 0)
        return (self.levels.copy(), self.last_update)
    
    def close(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
                logger.info("Audio stream closed")
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
