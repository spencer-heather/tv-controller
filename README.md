# TV Controller

Resources for the serial TV controller we use to control our TVs & integration with Home Assistant.

This consists of three pieces:

1. The [TV controller](tv-controller) - a REST API that accepts input from Home Assistant to control the TV (power, volume, etc.)
2. The [Home Assistant configurations](home-assistant) that send HTTP requests to the TV controller to get state information or control the TV.
3. The [remote control](remote), which sends requests to Home Assistant to call various endpoints and control the TV.
