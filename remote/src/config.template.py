# Configuration for GPIO pins
button_config = {
    "chip_name": "/dev/gpiochip0",
    "power_pin": 16,
    "volume_pin_clk": 13,
    "volume_pin_dt": 19,
    "volume_mute_pin": 26,
    "tv_switch_pin": 17,
    "tv_ids": ["top", "bottom"],
}

# Optional: "DEBUG", "INFO", "WARNING", "ERROR"
LOG_LEVEL = "INFO"

HOME_ASSISTANT_WEBHOOK_URL = "${home_assistant_url_or_ip}/api/webhook/${trigger_id}"
