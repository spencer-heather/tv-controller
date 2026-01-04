# Home Assistant configurations

- [Configuration](./configuration.yaml) - defines a pass-through API for the remote control to hit the TV serial controller. Replace `${BASE_URL}` and `${PORT}` with the information for the TV serial controller.
- [Automation](./automation.yaml) - defines a Webhook endpoint for the remote control to hit that will hit the pass-through API to control the TV(s) serially. Define this in Settings -> Automations & scenes -> Create new automation.

N.B. that you cannot get a response body from the webhook, so information about the state of the TVs following sending a command will not be available.

Following defining these, make sure you reload your configuration (Developer tools -> YAML -> All YAML configuration).

