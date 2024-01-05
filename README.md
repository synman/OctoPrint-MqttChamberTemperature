[![Usage Statistics](https://github.com/synman/OctoPluginStats/actions/workflows/get-data.yaml/badge.svg)](https://synman.github.io/OctoPluginStats/#bettergrblsupportContainer)
# MQTT Chamber Temperature Plugin for Octoprint
 
* Requires the [MQTT](https://plugins.octoprint.org/plugins/mqtt/) Plugin to be installed and configured
* Subcribed topic configurable via Plugin Settings
* Can convert retrieved temperature to Celcius if provided in Fahrenheit
* Control enclosure temperature via MQTT state topics

## Screenshots

<img width="430" alt="Screenshot 2024-01-02 at 3 33 09 AM" src="https://github.com/synman/OctoPrint-MqttChamberTemperature/assets/1299716/f483b6dc-27bd-4d91-a873-d530db5e4fd8">
 
<img width="986" alt="Screenshot 2024-01-02 at 3 32 49 AM" src="https://github.com/synman/OctoPrint-MqttChamberTemperature/assets/1299716/1d2d5f69-cae6-4d78-824b-feabee421490">

<img width="967" alt="Screenshot 2024-01-05 at 10 24 33 AM" src="https://github.com/synman/OctoPrint-MqttChamberTemperature/assets/1299716/420e3b8d-e6a8-4c6a-a408-a9aec3a13c12">

## Temperature Sensor Ideas

* ESP8266/ESP32 BME280 - https://github.com/synman/BME280
* ESP8266/ESP32 SHT30 & LCD - https://github.com/synman/SHT-Sensor

## Power Plug Considerations

The easiest way to integration temperature control is by use of a Home Assistant integrated power plug such as the [TP-LINK HS103](https://www.tp-link.com/us/home-networking/smart-plug/hs103/) or similar.  Creating automations for managing the requested and actual state values via MQTT is then fairly trivial.
