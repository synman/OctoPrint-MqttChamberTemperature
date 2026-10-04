[![Usage Statistics](https://github.com/synman/OctoPluginStats/actions/workflows/get-data.yaml/badge.svg)](https://synman.github.io/OctoPluginStats/#bettergrblsupportContainer)
# MQTT Chamber Temperature Plugin for Octoprint

Shows an enclosure ("chamber") temperature in OctoPrint from an MQTT topic, and can drive an enclosure heater over MQTT.

* Requires the [MQTT](https://plugins.octoprint.org/plugins/mqtt/) Plugin to be installed and configured
* Subcribed topic configurable via Plugin Settings
* Enable heated chamber in the print profile
* ![image](https://github.com/user-attachments/assets/fa2fa3de-dc2d-44c5-bfde-926c15a78a20)
* Can convert retrieved temperature to Celcius if provided in Fahrenheit
* Can read the temperature from a JSON payload using a JSONPath expression
* Control enclosure temperature via MQTT state topics
* Optionally turn the heater off when a print ends (done, failed or cancelled) — enable "Turn Heater Off When Print Ends" under Temperature Control
* Chamber temperature presets appear in OctoPrint's temperature profiles once heated chamber is enabled in the printer profile

## Installation

Install from OctoPrint's Plugin Manager (search for "MQTT Chamber Temperature"), or with this URL in Plugin Manager → Get More → from URL:

```
https://github.com/synman/OctoPrint-MqttChamberTemperature/archive/main.zip
```

Restart OctoPrint after installing. Updates arrive through OctoPrint's Software Update, from the Stable channel or, if you opt in, the Release Candidate channel.

## Quick start

1. Install and configure the [MQTT plugin](https://plugins.octoprint.org/plugins/mqtt/) so it connects to your broker.
2. Enable **Heated Chamber** in your printer profile, then disconnect and reconnect the printer.
3. In Settings → MQTT Chamber Temperature, set **Subscribed Topic** to the topic your sensor publishes to.
4. Optional: turn on **Control Temperature** and set the state topics and ON/OFF values your heater uses.

Full settings reference, heater behavior and troubleshooting: [Operator Guide](docs/operator-guide.md).

## Screenshots

<img width="430" alt="Screenshot 2024-01-02 at 3 33 09 AM" src="https://github.com/synman/OctoPrint-MqttChamberTemperature/assets/1299716/f483b6dc-27bd-4d91-a873-d530db5e4fd8">
 
<img width="986" alt="Screenshot 2024-01-02 at 3 32 49 AM" src="https://github.com/synman/OctoPrint-MqttChamberTemperature/assets/1299716/1d2d5f69-cae6-4d78-824b-feabee421490">

<img width="967" alt="Screenshot 2024-01-05 at 10 24 33 AM" src="https://github.com/synman/OctoPrint-MqttChamberTemperature/assets/1299716/420e3b8d-e6a8-4c6a-a408-a9aec3a13c12">

## Temperature Sensor Ideas

* ESP8266/ESP32 BME280 - https://github.com/synman/BME280
* ESP8266/ESP32 SHT30 & LCD - https://github.com/synman/SHT-Sensor

## Heater and Power Plug Reference

The easiest way to manage temperature control is by use of a [miniature heater](https://www.amazon.com/dp/B07573FKSG) connected to a Home Assistant integrated power plug such as the [TP-LINK HS103](https://www.tp-link.com/us/home-networking/smart-plug/hs103/).  Creating automations for managing the requested and actual power state values via MQTT is then fairly trivial.

## Project structure

| Path | What it is |
|---|---|
| `octoprint_mqttchambertemperature/__init__.py` | The plugin: settings, MQTT handling, heater control, OctoPrint hooks |
| `octoprint_mqttchambertemperature/templates/mqttchambertemperature_settings.jinja2` | Settings page |
| `octoprint_mqttchambertemperature/static/js/mqttchambertemperature_settings.js` | Settings page view model and notifications |
| `setup.py` | Packaging; `plugin_version` is the release version |
| `docs/` | Operator guide, verification SOP, release runbook |

## Contributing

Pull requests are welcome. There are no automated tests, so please describe how you tested. Maintainers verify changes with the [local verification SOP](docs/local-verification-sop.md) and publish with the [release runbook](docs/releasing.md).
