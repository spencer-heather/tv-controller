# Configuration for TV controllers
#
# Each TV needs:
#   - name: Human-readable name for the TV
#   - port: Serial device path (for serial-based protocols)
#   - protocol_class: Full path to the controller class (required)
#   - auto_enable_standby: Enable standby mode on startup (optional, protocol-specific)
#
# Logging level: "DEBUG", "INFO", "WARNING", "ERROR" (default: "INFO")
# Use "DEBUG" to see detailed packet information and error responses
LOG_LEVEL = "INFO"

# Example configuration for Sony Bravia TVs:
TVs = {
    "tv_identifier": {
        "name": "Nice name for TV",
        "port": "/dev/ttyUSB0",
        "protocol_class": "sony_bravia_serial.SonyBraviaSerial",
        # Optional: Auto-enable standby mode on startup (default: True)
        # "auto_enable_standby": True,
    }
}

# Example with multiple TVs using different protocols:
# TVs = {
#     "living_room": {
#         "name": "Living Room TV",
#         "port": "/dev/ttyUSB0",
#         "protocol_class": "sony_bravia_serial.SonyBraviaSerial",
#         "auto_enable_standby": True,
#     },
#     "bedroom": {
#         "name": "Bedroom TV",
#         "port": "/dev/ttyUSB1",
#         "protocol_class": "my_custom_protocol.MyTVController",
#         "custom_param": "some_value",  # Custom protocols can have their own params
#     },
# }
