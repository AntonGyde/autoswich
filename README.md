# autoswich

Autoswich DM3 / ATEM MINI - Automatic Camera Switching System

An intelligent audio-based camera switching system for multi-camera video production. Automatically switches between camera angles based on who is speaking, with support for OSC control and calibration.

## Features

- **Automatic Camera Switching**: Switches cameras based on audio levels and speaker detection
- **Multi-Speaker Detection**: Automatically switches to wide shot when multiple people speak
- **Silence Detection**: Returns to wide shot during silence periods
- **Interval-Based Wide Shots**: Periodically shows wide shots for visual variety
- **Microphone Calibration**: Easy calibration system to optimize threshold and weight settings
- **OSC Integration**: Sends camera commands via OSC protocol (compatible with ATEM switchers)
- **Web Interface**: Simple web UI for monitoring and calibration
- **Raspberry Pi Optimized**: Designed to run efficiently on Raspberry Pi hardware

## Requirements

- Python 3.11+
- Audio interface with multi-channel input
- OSC-compatible video switcher (e.g., ATEM MINI)

## Installation

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/AntonGyde/autoswich.git
cd autoswich

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn webapp:app --host 0.0.0.0 --port 8000
```

### Docker Installation

```bash
# Build the Docker image
docker build -t autoswich .

# Run the container
docker run -p 8000:8000 --device /dev/snd:/dev/snd autoswich
```

## Raspberry Pi Setup

### Prerequisites

1. **Update your Raspberry Pi**:
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

2. **Install system dependencies**:
```bash
sudo apt-get install -y python3-pip python3-dev portaudio19-dev libportaudio2
```

3. **Configure Audio Device**:

List available audio devices:
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

Update `config.json` with the correct device index:
```json
{
  "audio_device": 0,
  "audio_channels": 16
}
```

### Performance Optimization for Raspberry Pi

For better performance on Raspberry Pi, consider:

1. **Disable GUI** (if not needed):
```bash
sudo systemctl set-default multi-user.target
```

2. **Increase swap space** (for compilation):
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

3. **Enable audio device**:
```bash
# Add your user to audio group
sudo usermod -a -G audio $USER

# Configure audio permissions
sudo nano /etc/asound.conf
```

Add to `/etc/asound.conf`:
```
pcm.!default {
    type hw
    card 0
}

ctl.!default {
    type hw
    card 0
}
```

4. **Test audio input**:
```bash
arecord -l  # List recording devices
arecord -D hw:0,0 -d 5 -f cd test.wav  # Record 5 seconds
aplay test.wav  # Play back
```

### Running on Raspberry Pi

1. **Direct execution**:
```bash
cd autoswich
python3 -m uvicorn webapp:app --host 0.0.0.0 --port 8000
```

2. **Run as systemd service**:

Create `/etc/systemd/system/autoswich.service`:
```ini
[Unit]
Description=Autoswich Camera Switching Service
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/autoswich
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 -m uvicorn webapp:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable autoswich
sudo systemctl start autoswich
sudo systemctl status autoswich
```

View logs:
```bash
sudo journalctl -u autoswich -f
```

## Configuration

Edit `config.json` to configure the system:

- `audio_device`: Audio device index (use 0 for default, or specific device index)
- `audio_channels`: Number of audio channels
- `mics`: Array of microphone configurations
  - `id`: Unique identifier
  - `name`: Display name
  - `input_channel`: Audio input channel number (1-indexed)
  - `threshold_db`: Activation threshold in dB (e.g., -45)
  - `weight`: Priority weight (higher = more likely to be selected)
  - `camera`: Camera identifier for OSC commands
  - `enabled`: Enable/disable this microphone
- `osc`: OSC client configuration
  - `host`: OSC server IP address
  - `port`: OSC server port
- `wide`: Wide shot behavior configuration
  - `cooldown_s`: Minimum time between wide shots
  - `min_duration_s`: Minimum duration of wide shot
  - `multi_speaker`: Enable wide shot when multiple speakers detected
  - `silence`: Enable wide shot during silence
  - `interval`: Enable periodic wide shots

## Usage

1. **Access the web interface**: Open `http://localhost:8000` (or your Raspberry Pi's IP address)

2. **Calibrate microphones**:
   - Click "Calibrate" for a microphone
   - Have the person speak into that microphone for 5 seconds
   - Review the suggested threshold and weight values
   - Click "Apply" to save the calibration

3. **Monitor operation**: The system will automatically switch cameras based on audio levels

## Troubleshooting

### Audio Device Not Found

If you see "Failed to initialize audio device" errors:

1. Check available devices:
```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

2. Update `audio_device` in `config.json` to the correct device index

3. Verify audio permissions:
```bash
groups  # Should include 'audio'
```

### No Audio Input

1. Test with `arecord`:
```bash
arecord -D hw:0,0 -d 5 -f cd test.wav
```

2. Check if the device is busy:
```bash
lsof /dev/snd/*
```

3. Adjust audio levels:
```bash
alsamixer  # Press F4 for capture devices
```

### High CPU Usage on Raspberry Pi

1. Reduce audio sample rate in `engine/audio.py` (line with `samplerate=`)
2. Increase tick interval in `webapp.py` (line with `time.sleep(0.05)`)
3. Reduce number of enabled microphones in `config.json`

### OSC Not Sending

1. Verify OSC host and port in `config.json`
2. Check network connectivity:
```bash
ping <osc_host>
```

3. Test OSC manually:
```bash
python3 -c "from pythonosc import udp_client; client = udp_client.SimpleUDPClient('127.0.0.1', 12345); client.send_message('/test', 'hello')"
```

## Development

### Project Structure

```
autoswich/
├── config.json           # Configuration file
├── Dockerfile           # Docker container definition
├── requirements.txt     # Python dependencies
├── webapp.py           # FastAPI web application
├── engine/             # Core engine modules
│   ├── __init__.py
│   ├── engine.py       # Main engine orchestration
│   ├── audio.py        # Audio input handling
│   ├── mics.py         # Microphone management
│   ├── state.py        # State machine
│   ├── decision.py     # Decision logic
│   ├── osc.py          # OSC client
│   └── calibration.py  # Calibration system
└── static/             # Web interface
    └── index.html      # Web UI
```

### Adding Features

1. Modify configuration schema in `config.json`
2. Update engine modules as needed
3. Test changes locally
4. Update documentation

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please open an issue on GitHub.
