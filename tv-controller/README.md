# TV Controller REST API

REST API for controlling TVs via serial protocols. Built with FastAPI and designed for home automation systems like Home Assistant.

Initially developed for Sony Bravia TVs using RS-232C serial protocol ([docs](https://pro-bravia.sony.net/develop/integrate/rs-232c/index.html)), but extensible to support other TV brands and protocols.

**Dependencies:**
- [FastAPI](https://fastapi.tiangolo.com/) - REST API framework
- [pySerial](https://pyserial.readthedocs.io/en/latest/) - Serial communication


## Installation

```bash
# Create virtual environment
python3 -m venv tv-controller/.venv
source tv-controller/.venv/bin/activate

# Install dependencies
python3 -m pip install -r requirements.txt
```

## Configuration

Copy the template and configure your TVs:

```bash
cp src/config.template.py src/config.py
```

Edit `src/config.py`:

```python
# Optional: "DEBUG", "INFO", "WARNING", "ERROR"
LOG_LEVEL = "INFO" 

TVs = {
    "living_room": {
        "name": "Living Room TV",
        "port": "/dev/ttyUSB0",
        "protocol_class": "sony_bravia_serial.SonyBraviaSerial",
    },
    "bedroom": {
        "name": "Bedroom TV",
        "port": "/dev/ttyUSB1",
        "protocol_class": "sony_bravia_serial.SonyBraviaSerial",
    },
}
```

The keys for the TVs dict will be the `tv_id`s used in [calls to the API](#api-documentation).

**Configuration Options:**
- `name` - Human-readable TV name (required)
- `port` - Serial device path, e.g., `/dev/ttyUSB0` (required)
- `protocol_class` - Controller class path (required)
  - Available classes: `sony_bravia_serial.SonyBraviaSerial`
  - See [Adding New TV Protocols](#adding-new-tv-protocols) to implement custom protocols
- `LOG_LEVEL` - Logging verbosity: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"` (optional, default: `"INFO"`)

**Notes:**
- TV identifier `all` is reserved for broadcast commands

### SonyBraviaSerial

The Sony Bravia protocol supports additional configuration:

- `auto_enable_standby` - Automatically enable standby mode on startup (default: `True`)
  - Enables wake-from-sleep via serial commands
  - TVs must be powered on during first startup for automatic configuration
  - Alternatively, disable and use `/tv/{tv_id}/standby/on` endpoint manually (TV must be on)

---

## Usage

### Running Locally

```bash
cd src
uvicorn main:app --reload
```

API available at `http://localhost:8000`

### Deploying using systemd


Create `/etc/systemd/system/tv-controller.service`:

```ini
[Unit]
Description=TV Controller REST API
After=network.target

[Service]
Type=simple
User={{username}}
WorkingDirectory={{repo_root}}/tv-controller/src
ExecStart={{repo_root}}/tv-controller/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Replace `{{username}}` and `{{repo_root}}` with your values.

Enable and start:

```bash
sudo systemctl enable tv-controller
sudo systemctl start tv-controller
sudo systemctl status tv-controller
```

View logs:

```bash
sudo journalctl -u tv-controller -f
```

# API Documentation

Auto-generated interactive docs:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

## Quick Reference

**Power:**
- `POST /tv/{tv_id}/power/on|off|toggle`
- `GET /tv/{tv_id}/power`

**Volume:**
- `POST /tv/{tv_id}/volume/up|down?step=N`
- `GET /tv/{tv_id}/volume`

**Mute:**
- `POST /tv/{tv_id}/mute/toggle`
- `GET /tv/{tv_id}/mute`

**Standby (Sony Bravia):**
- `POST /tv/{tv_id}/standby/on|off`

**TV IDs:** Use the tv_ids in your config.py file (values of TVs dict) (e.g., `living_room` or `all` for broadcast)

## Examples

```bash
# Turn on specific TV
curl -X POST http://localhost:8000/tv/living_room/power/on

# Turn off all TVs
curl -X POST http://localhost:8000/tv/all/power/off

# Adjust volume
curl -X POST "http://localhost:8000/tv/living_room/volume/up?step=5"

# Check power state
curl http://localhost:8000/tv/living_room/power
```


# Development

## Adding New TV Protocols

1. Create a new Python file in `src/` inheriting from `BaseTVController`
2. Implement all required abstract methods (see `src/base_tv_controller.py`)
3. Update `config.py` with your protocol class

**Example:**

```python
# src/my_tv_protocol.py
from base_tv_controller import BaseTVController

class MyTVController(BaseTVController):
    def __init__(self, config: dict):
        self.port = config["port"]
        # Initialize your protocol

    def power_on(self):
        # Implementation
        pass

    # ... implement other required methods
```

```python
# config.py
TVs = {
    "my_tv": {
        "name": "My TV",
        "port": "/dev/ttyUSB0",
        "protocol_class": "my_tv_protocol.MyTVController",
    },
}
```

See `src/sony_bravia_serial.py` for a complete implementation example.


## Integrations

### Home Assistant

Example REST command configuration:

```yaml
rest_command:
  living_room_tv_on:
    url: "http://raspberrypi:8000/tv/living_room/power/on"
    method: POST

  all_tvs_off:
    url: "http://raspberrypi:8000/tv/all/power/off"
    method: POST

  living_room_tv_volume_up:
    url: "http://raspberrypi:8000/tv/living_room/volume/up?step=3"
    method: POST
```
