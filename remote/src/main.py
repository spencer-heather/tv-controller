#!/usr/bin/env python3

import gpiod
from config import button_config
import logging
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class RemoteControlGPIO:
    def __init__(self, button_config):
        self.last_event_time = 0
        self.debounce_ns = 200_000_000

        self.initialize_chip(button_config["chip_name"])
        self.power_pin = button_config["power_pin"]
        self.tv_switch_pin = button_config["tv_switch_pin"]
        self.tv_ids = button_config["tv_ids"]

        self.setup_gpio()

    def initialize_chip(self, chip_name):
        chip = gpiod.Chip(chip_name)
        self.chip = chip

    def setup_gpio(self):
        power_settings = gpiod.LineSettings(
            direction=gpiod.line.Direction.INPUT,
            bias=gpiod.line.Bias.PULL_DOWN,
            edge_detection=gpiod.line.Edge.RISING,
        )

        tv_switch_settings = gpiod.LineSettings(
            direction=gpiod.line.Direction.INPUT,
            bias=gpiod.line.Bias.PULL_DOWN,
        )

        self.line_request = self.chip.request_lines(
            config={
                self.power_pin: power_settings,
                self.tv_switch_pin: tv_switch_settings,
            },
            consumer="remote_control",
        )
        logger.info("GPIO settings initialized")

    def __enter__(self):
        return self

    def run(self):
        logger.info("Monitoring GPIO inputs")
        try:
            while True:
                events = self.line_request.read_edge_events()

                for event in events:
                    self.handle_event(event)
        except KeyboardInterrupt:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.line_request.release()
        self.chip.close()
        logger.info("Shut down successfully; goodbye")
        return False

    def handle_event(self, event):
        if event.timestamp_ns - self.last_event_time < self.debounce_ns:
            # Too soon; ignore
            return

        self.last_event_time = event.timestamp_ns

        if event.line_offset == self.power_pin:
            self.toggle_power()
        else:
            logger.error(f"Unexpected line offset encountered: {event.line_offset}")
            raise SystemExit()

    def get_current_tv_id(self):
        tv_switch_value = self.line_request.get_value(self.tv_switch_pin)
        current_tv_id = self.tv_ids["up"] if tv_switch_value else self.tv_ids["down"]
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


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s] %(message)s",
    )

    with RemoteControlGPIO(button_config) as remote:
        remote.run()


if __name__ == "__main__":
    main()
