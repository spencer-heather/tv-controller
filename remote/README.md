# Remote control

Code for sending commands to the tv-controller to control the TVs. This will be loaded onto a Raspberry Pi or [ESP32C6](https://wiki.seeedstudio.com/xiao_esp32c6_getting_started/) and buttons will be set up to control each of the endpoints exposed by [the TV controller](../tv-controller).

## Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
python3 -m pip install -r requirements.txt
```

## Configuration

Copy the template and configure your TVs:

```bash
cp src/config.template.py src/config.py
```

Edit `src/config.py`:

### `button_config`

- `button_config.chip_name` is almost certainly `/dev/gpiochip0`.
- `power_pin`: the input pin for the power button
- `volume_pin_ctk`, `volume_pin_dt`, `volume_mute_pin`: the input pins for the volume controls
- [Optional] `tv_switch_pin`: the pin controlling the toggle between TVs
- `tv_ids`: array of TVs defined in [the TV serial controller's config](../tv-controller/README.md#configuration)

## Wiring setup

- Connect 3.3V (pin 1) to power switch input
- Connect power switch output to `config.power_pin` (e.g. GPIO 16)
- Connect volume rotary encoder output CLK to `config.volume_pin_clk` (e.g. GPIO 13)
- Connect volume rotary encoder output DT to `config.volume_pin_dt` (e.g. GPIO 19)
- Connect volume rotary encoder output SW to `config.volume_mute_pin` (e.g. GPIO 26)
- Connect volume rotary encoder output + to 3.3V (pin 1)
- Connect volume rotary encoder ground to GND

Optional, if using a toggle switch to switch between the control of two TVs:
- Connect 3.3V (pin 1) to tv toggle switch input
- Connect tv toggle switch output to `config.tv_switch_pin` (e.g. GPIO 17)
