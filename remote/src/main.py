#!/usr/bin/env python3

import time
import gpiod
from config import button_config
import logging
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
try:
    from config import LOG_LEVEL
except ImportError:
    LOG_LEVEL = "INFO"


class RemoteControlGPIO:
    def __init__(self, button_config):
        self.initialize_chip(button_config["chip_name"])

        self.power_pin = button_config["power_pin"]
        self.power_last_event_time = 0
        self.power_debounce_ns = 200_000_000

        self.volume_pin_clk = button_config["volume_pin_clk"]
        self.volume_pin_dt = button_config["volume_pin_dt"]
        self.volume_steps = 0
        self.volume_last_event_time = 0
        self.volume_flush_delay_ns = 150_000_000
        self.volume_mute_pin = button_config["volume_mute_pin"]
        self.mute_last_event_time = 0
        self.mute_debounce_ns = 200_000_000

        self.tv_switch_pin = button_config.get("tv_switch_pin")
        self.tv_ids = button_config["tv_ids"]

        self.setup_gpio()

    def initialize_chip(self, chip_name):
        chip = gpiod.Chip(chip_name)
        self.chip = chip

    def setup_gpio(self):
        line_config = dict()
        line_config[self.power_pin] = gpiod.LineSettings(
            direction=gpiod.line.Direction.INPUT,
            bias=gpiod.line.Bias.PULL_DOWN,
            edge_detection=gpiod.line.Edge.RISING,
        )

        rotary_encoder_settings = gpiod.LineSettings(
            direction=gpiod.line.Direction.INPUT,
            bias=gpiod.line.Bias.PULL_UP,
            edge_detection=gpiod.line.Edge.BOTH,
        )
        line_config[self.volume_pin_clk] = rotary_encoder_settings
        line_config[self.volume_pin_dt] = rotary_encoder_settings

        line_config[self.volume_mute_pin] = gpiod.LineSettings(
            direction=gpiod.line.Direction.INPUT,
            bias=gpiod.line.Bias.PULL_DOWN,
            edge_detection=gpiod.line.Edge.RISING,
        )

        if self.tv_switch_pin is not None:
            line_config[self.tv_switch_pin] = gpiod.LineSettings(
                direction=gpiod.line.Direction.INPUT,
                bias=gpiod.line.Bias.PULL_DOWN,
            )

        self.line_request = self.chip.request_lines(
            config=line_config,
            consumer="remote_control",
        )
        logger.info("GPIO settings initialized")

    def __enter__(self):
        return self

    def run(self):
        logger.info("Monitoring GPIO inputs")
        try:
            while True:
                if self.line_request.wait_edge_events(timeout=0.1):
                    events = self.line_request.read_edge_events()
                    for event in events:
                        self.handle_event(event)

                self.flush_volume()
        except KeyboardInterrupt:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.line_request.release()
        self.chip.close()
        logger.info("Shut down successfully; goodbye")
        return False

    def handle_event(self, event):
        if event.line_offset == self.power_pin:
            if event.timestamp_ns - self.power_last_event_time < self.power_debounce_ns:
                # Too soon; ignore
                return

            self.power_last_event_time = event.timestamp_ns

            logger.debug("Detected power pin event")
            self.toggle_power()
        # Only respond to volume CLK events
        elif event.line_offset == self.volume_pin_clk:
            logger.debug("Detected volume pin CLK event")
            self.handle_volume_turn(event)
        elif event.line_offset == self.volume_pin_dt:
            pass
        elif event.line_offset == self.volume_mute_pin:
            if event.timestamp_ns - self.mute_last_event_time < self.mute_debounce_ns:
                # Too soon; ignore
                return

            self.mute_last_event_time = event.timestamp_ns

            logger.debug("Detected volume mute pin event")
            self.toggle_mute()
        else:
            logger.error(f"Unexpected line offset encountered: {event.line_offset}")
            raise SystemExit()

    def get_current_tv_id(self):
        if self.tv_switch_pin is not None:
            tv_switch_value = self.line_request.get_value(self.tv_switch_pin)
            current_tv_id = self.tv_ids[0] if tv_switch_value else self.tv_ids[1]
        else:
            current_tv_id = self.tv_ids[0]

        logger.debug(f"Current TV ID: {current_tv_id}")
        return current_tv_id

    def toggle_power(self):
        logger.info("Toggling power captain!")

        try:
            requests.post(
                "https://homeassistant.somanydoors.ca/api/webhook/tv_remote",
                json={
                    "tv_id": self.get_current_tv_id(),
                    "command": "power",
                    "subcommand": "toggle",
                },
            )
        except RequestException as e:
            logger.error(f"Request failed: {e}")

    def flush_volume(self):
        if self.volume_steps == 0:
            return

        now = time.time_ns()
        if now - self.volume_last_event_time >= self.volume_flush_delay_ns:
            if self.volume_steps > 0:
                self.volume_up(steps=self.volume_steps)
            else:
                self.volume_down(steps=abs(self.volume_steps))
            self.volume_steps = 0

    def handle_volume_turn(self, event):
        dt_value = self.line_request.get_value(self.volume_pin_dt)

        if event.event_type.name == "RISING_EDGE":
            if dt_value == gpiod.line.Value.INACTIVE:
                self.volume_steps += 1
            else:
                self.volume_steps -= 1
            self.volume_last_event_time = time.time_ns()

    def volume_up(self, steps: int = 1):
        logger.info(f"can't hear it m8 (turn it up) [{steps} steps]")

        try:
            requests.post(
                "https://homeassistant.somanydoors.ca/api/webhook/tv_remote",
                json={
                    "tv_id": self.get_current_tv_id(),
                    "command": "volume",
                    "subcommand": "up",
                    "params": {"step": steps},
                },
            )
        except RequestException as e:
            logger.error(f"Request failed: {e}")

    def volume_down(self, steps: int = 1):
        logger.info(f"shhh (turn it down) [{steps} steps]")

        try:
            requests.post(
                "https://homeassistant.somanydoors.ca/api/webhook/tv_remote",
                json={
                    "tv_id": self.get_current_tv_id(),
                    "command": "volume",
                    "subcommand": "down",
                    "params": {"step": steps},
                },
            )
        except RequestException as e:
            logger.error(f"Request failed: {e}")

    def toggle_mute(self):
        logger.info("Toggle mute")

        try:
            requests.post(
                "https://homeassistant.somanydoors.ca/api/webhook/tv_remote",
                json={
                    "tv_id": self.get_current_tv_id(),
                    "command": "volume",
                    "subcommand": "mute/toggle",
                },
            )
        except RequestException as e:
            logger.error(f"Request failed: {e}")


def main():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    with RemoteControlGPIO(button_config) as remote:
        remote.run()


if __name__ == "__main__":
    main()
